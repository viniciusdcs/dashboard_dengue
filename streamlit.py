import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Casos de Dengue",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------
# Carregar o arquivo consolidado
# ---------------------
@st.cache_data
def carregar_dados():
    pasta_dados = os.path.join(os.path.dirname(__file__), "dados_dengue")
    arquivo_consolidado = os.path.join(pasta_dados, "dengue_consolidado.xlsx")
    
    if not os.path.exists(arquivo_consolidado):
        st.error("Arquivo de dados consolidados não encontrado!")
        st.info("Execute o script 'gerar_consolidado.py' primeiro.")
        return None
    
    return pd.read_excel(arquivo_consolidado)

# Carregar os dados
df = carregar_dados()

if df is None:
    st.stop()

# ---------------------
# Sidebar - Filtros
# ---------------------
st.sidebar.title("Filtros")

# Filtro de Ano para o Mapa
anos = sorted(df["Ano"].unique(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano para o Mapa", anos)

# Filtro de Estado para o Gráfico de Linha
estados = sorted(df["Estado"].unique())
estado_selecionado = st.sidebar.selectbox("Selecione o Estado para o Gráfico", estados)

# ---------------------
# Dashboard principal
# ---------------------
st.title("Dashboard de Casos de Dengue no Brasil")

# Layout de duas colunas para os gráficos
col1, col2 = st.columns(2)

# Filtrar dados para o ano selecionado (para o mapa)
df_ano = df[df["Ano"] == ano_selecionado]

with col1:
    # Mapa de casos por estado
    st.subheader(f"Casos de Dengue por Estado - {ano_selecionado}")
    
    fig_mapa = px.choropleth(
        df_ano,
        geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
        locations="UF",  
        featureidkey="properties.sigla",
        color="Total de Casos",
        color_continuous_scale="Reds",
        scope="south america",
        labels={"Total de Casos": "Casos de Dengue"}
    )
    
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    fig_mapa.update_layout(height=500)
    st.plotly_chart(fig_mapa, use_container_width=True)

# Filtrar dados para o estado selecionado (para o gráfico de linha)
df_estado = df[df["Estado"] == estado_selecionado].sort_values("Ano")

with col2:
    # Gráfico de linha por ano para o estado selecionado
    st.subheader(f"Evolução de Casos em {estado_selecionado}")
    
    fig_linha = px.line(
        df_estado,
        x="Ano", 
        y="Total de Casos",
        markers=True,
        title=f"Casos de Dengue por Ano - {estado_selecionado}"
    )
    
    fig_linha.update_layout(
        xaxis_title="Ano",
        yaxis_title="Total de Casos",
        height=500
    )
    
    st.plotly_chart(fig_linha, use_container_width=True)

# Rodapé
st.markdown("---")
st.markdown("Dashboard desenvolvido para monitoramento de casos de dengue no Brasil. Dados obtidos do DATASUS.")
st.markdown("Fonte: Ministério da Saúde/SVS - Sistema de Informação de Agravos de Notificação - Sinan Net")
