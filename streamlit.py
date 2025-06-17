import streamlit as st
import pandas as pd
import plotly.express as px
import duckdb
import os
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Análise Temporal de Dengue",
    page_icon="🦟",
    layout="wide"
)

# Inicializa conexão com DuckDB
@st.cache_resource
def get_duckdb_connection():
    return duckdb.connect()

# Função para carregar dados com DuckDB
@st.cache_data
def carregar_dados(query):
    con = get_duckdb_connection()
    return con.execute(query).df()

# Função para carregar o mapeamento de cidades
@st.cache_data
def carregar_mapeamento_cidades():
    return pd.read_parquet('dengue_visualizacao/mapeamento_cidades.parquet')

# Função para formatar ano e semana
def formatar_ano_semana(row):
    return f"{row['Ano']} S{str(row['Semana']).zfill(2)}"

# Função para formatar ano e mês
def formatar_ano_mes(row):
    return f"{row['Ano']} M{str(row['Mes']).zfill(2)}"

# Função para converter ano e semana em valor numérico para ordenação
def criar_valor_ordenacao(row):
    if 'Semana' in row:
        return int(f"{row['Ano']}{str(row['Semana']).zfill(2)}")
    elif 'Mes' in row:
        return int(f"{row['Ano']}{str(row['Mes']).zfill(2)}")
    return int(row['Ano'])

# Função para converter ano e mês em data
def converter_mes_para_data(df):
    # Garantir que Ano e Mes sejam strings com o formato correto
    df["Data"] = pd.to_datetime(df["Ano"].astype(str) + "-" + df["Mes"].astype(str).str.zfill(2) + "-01")
    return df

# Título da aplicação
st.title("Análise Temporal de Casos de Dengue")

# Sidebar com filtros
st.sidebar.header("Filtros")

# Carregar mapeamento de cidades
df_cidades = carregar_mapeamento_cidades()

# Lista de estados
estados = [os.path.splitext(f)[0] for f in os.listdir("dengue_com_taxa") if f.endswith('.parquet')]
estado_selecionado = st.sidebar.selectbox("Selecione o Estado", ["Todos"] + sorted(estados))

# Lista de cidades do estado selecionado
cidades = []
if estado_selecionado != "Todos":
    # Carregar dados do estado selecionado
    query_cidades = f"""
    SELECT DISTINCT Municipio
    FROM 'dengue_com_taxa/{estado_selecionado}.parquet'
    ORDER BY Municipio
    """
    df_cidades_estado = carregar_dados(query_cidades)
    cidades = df_cidades_estado['Municipio'].unique().tolist()
    cidade_selecionada = st.sidebar.selectbox("Selecione a Cidade", ["Todas"] + sorted(cidades))

# Seleção da granularidade
granularidade = st.sidebar.selectbox("Escolha a granularidade (Frequência)", ["Semanal", "Mensal", "Anual"])

# Seleção do tipo de dado
tipo_dado = st.sidebar.radio("Selecione o tipo de dado", ["Casos", "Taxa"])

# Preparar a query base
if estado_selecionado == "Todos":
    arquivo = "dengue_visualizacao/totais_geral.parquet"
else:
    arquivo = f"dengue_com_taxa/{estado_selecionado}.parquet"

# Construir a query de acordo com a granularidade e filtros
filtro_cidade = ""
if estado_selecionado != "Todos" and 'cidade_selecionada' in locals() and cidade_selecionada != "Todas":
    filtro_cidade = f" AND \"Municipio\" = '{cidade_selecionada}'"

coluna_valor = "Casos" if tipo_dado == "Casos" else "Taxa"

if granularidade == "Semanal":
    query = f"""
    SELECT 
        Ano,
        Semana,
        SUM({coluna_valor}) as {coluna_valor}
    FROM '{arquivo}'
    WHERE 1=1 {filtro_cidade}
    GROUP BY Ano, Semana
    ORDER BY Ano, Semana
    """
    df_temporal = carregar_dados(query)
    df_temporal["Período"] = df_temporal['Semana']
    eixo_x = "Período"
    titulo_x = "Ano-Semana"
elif granularidade == "Mensal":
    query = f"""
    SELECT 
        Ano,
        Mes,
        SUM({coluna_valor}) as {coluna_valor}
    FROM '{arquivo}'
    WHERE 1=1 {filtro_cidade}
    GROUP BY Ano, Mes
    ORDER BY Ano, Mes
    """
    df_temporal = carregar_dados(query)
    df_temporal["Período"] = df_temporal['Mes']
    eixo_x = "Período"
    titulo_x = "Ano-Mês"
else:  # Anual
    query = f"""
    SELECT 
        Ano,
        SUM({coluna_valor}) as {coluna_valor}
    FROM '{arquivo}'
    WHERE 1=1 {filtro_cidade}
    GROUP BY Ano
    ORDER BY Ano
    """
    df_temporal = carregar_dados(query)
    df_temporal["Período"] = df_temporal["Ano"].astype(str)
    eixo_x = "Período"
    titulo_x = "Ano"

# Criar título do gráfico
if estado_selecionado == "Todos":
    titulo_grafico = f"{tipo_dado} de Dengue por {granularidade} - Brasil"
elif 'cidade_selecionada' in locals() and cidade_selecionada != "Todas":
    titulo_grafico = f"{tipo_dado} de Dengue por {granularidade} - {cidade_selecionada} ({estado_selecionado})"
else:
    titulo_grafico = f"{tipo_dado} de Dengue por {granularidade} - {estado_selecionado}"

# Criar gráfico
fig = px.line(
    df_temporal, 
    x=eixo_x, 
    y=coluna_valor,
    title=titulo_grafico,
    labels={coluna_valor: f"Número de {tipo_dado}", eixo_x: titulo_x}
)

# Melhorar formatação do eixo X
if granularidade == "Semanal":
    fig.update_xaxes(
        tickangle=45,
        nticks=20
    )
elif granularidade == "Mensal":
    fig.update_xaxes(
        tickangle=45,
        nticks=15
    )
else:
    fig.update_xaxes(
        tickangle=45
    )

# Exibir gráfico
st.plotly_chart(fig, use_container_width=True)

# Estatísticas
st.header("Estatísticas")

col1, col2, col3 = st.columns(3)

# Total
total = df_temporal[coluna_valor].sum()
col1.metric(f"Total de {tipo_dado}", f"{total:,.2f}" if tipo_dado == "Taxa" else f"{int(total):,}")

# Média por período
media_periodo = df_temporal[coluna_valor].mean()
col2.metric(f"Média por período ({granularidade.lower()})", f"{media_periodo:,.2f}" if tipo_dado == "Taxa" else f"{int(media_periodo):,}")

# Período com maior valor
max_periodo = df_temporal.loc[df_temporal[coluna_valor].idxmax()]
col3.metric(f"Período com maior {tipo_dado.lower()}", f"{max_periodo['Período']}: {max_periodo[coluna_valor]:,.2f}" if tipo_dado == "Taxa" else f"{max_periodo['Período']}: {int(max_periodo[coluna_valor]):,}")

# Exibir dados brutos
with st.expander("Ver Dados"):
    df_display = df_temporal[["Período", coluna_valor]]
    st.dataframe(df_display)

# Adicionar informações sobre os dados
st.sidebar.markdown("---")
st.sidebar.info("""
**Sobre os Dados**
- Dados organizados por estado e município
- Período: 2014 a 2025
- Granularidades disponíveis: Semanal, Mensal e Anual
- Fonte: Datasus - Ministério da Saúde
""") 
