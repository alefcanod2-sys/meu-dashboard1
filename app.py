import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da página para Celular/Web
st.set_page_config(
    page_title="Painel de Custos Mensais",
    page_icon="📊",
    layout="centered"
)

# Estilização visual dos cartões de indicadores
st.markdown("""
    <style>
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Custos Mensais (Ao Vivo)")

# 2. URL da sua planilha do Google Drive
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1c4jwuz0JKWPkDpTMSfm1YJMFgxsZMr0a/edit"

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # ttl=60 faz o Streamlit buscar dados atualizados do Drive a cada 60 segundos
    # Certifique-se de que "Janeiro 26" é o nome exato da aba na sua planilha
    df = conn.read(spreadsheet=URL_PLANILHA, worksheet="Janeiro 26", ttl=60)
    
    # Remove linhas vazias
    df = df.dropna(subset=['Descrição', 'Valor']).copy()
    
    # Tratamento da coluna de valores monetários
    if df['Valor'].dtype == object:
        df['Valor_Clean'] = df['Valor'].astype(str).str.replace('R$', '', regex=False)\
                                                  .str.replace('.', '', regex=False)\
                                                  .str.replace(',', '.', regex=False).str.strip()
        df['Valor_Clean'] = pd.to_numeric(df['Valor_Clean'], errors='coerce').fillna(0)
    else:
        df['Valor_Clean'] = df['Valor']

    # Botão de atualização rápida
    if st.button("🔄 Atualizar Agora"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # 3. Cartões de Resumo (KPIs)
    col1, col2 = st.columns(2)
    total_geral = df['Valor_Clean'].sum()
    
    # Filtro flexível para situação 'pago' ou 'ok'
    situacao_lower = df['Situação'].astype(str).str.lower()
    total_pago = df[situacao_lower.isin(['pago', 'ok'])]['Valor_Clean'].sum()
    total_pendente = total_geral - total_pago

    with col1:
        st.metric("Total Geral", f"R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col2:
        st.metric("Total Pendente", f"R$ {total_pendente:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")

    # 4. Gráfico Interativo de Gastos
    st.subheader("📉 Despesas por Item")
    fig_barras = px.bar(
        df.sort_values(by='Valor_Clean', ascending=True),
        x='Valor_Clean',
        y='Descrição',
        orientation='h',
        labels={'Valor_Clean': 'Valor (R$)', 'Descrição': ''},
        color='Situação',
        color_discrete_map={'pago': '#27ae60', 'Pago': '#27ae60', 'ok': '#27ae60'}
    )
    fig_barras.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_barras, use_container_width=True)

    # 5. Tabela Detalhada
    st.subheader("📋 Detalhamento dos Lançamentos")
    st.dataframe(
        df[['Descrição', 'Valor_Clean', 'Situação']].rename(columns={'Valor_Clean': 'Valor (R$)'}), 
        use_container_width=True, 
        hide_index=True
    )

except Exception as e:
    st.error(f"Erro ao carregar a planilha. Verifique se o compartilhamento está aberto para 'Qualquer pessoa com o link'. Detalhes: {e}")