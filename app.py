import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão V4 Company", layout="wide")

# --- BANCO DE DADOS (SQLITE) ---
def init_db():
    conn = sqlite3.connect('v4_gestao.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY, nome TEXT, bu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS metricas 
                 (id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, flag TEXT,
                  investimento REAL, faturamento REAL, leads INTEGER, mql INTEGER, 
                  sql INTEGER, oportunidades INTEGER, vendas INTEGER)''')
    conn.commit()
    return conn

conn = init_db()

# --- LÓGICA DE CÁLCULO ---
def calcular_kpis(df):
    if df.empty: return None
    # Evitar divisão por zero
    df['ROAS'] = df['faturamento'] / df['investimento'].replace(0, 1)
    df['ROI (%)'] = ((df['faturamento'] - df['investimento']) / df['investimento'].replace(0, 1)) * 100
    df['Conv. Global (%)'] = (df['vendas'] / df['leads'].replace(0, 1)) * 100
    df['L -> MQL (%)'] = (df['mql'] / df['leads'].replace(0, 1)) * 100
    df['MQL -> SQL (%)'] = (df['sql'] / df['mql'].replace(0, 1)) * 100
    df['SQL -> Opt (%)'] = (df['oportunidades'] / df['sql'].replace(0, 1)) * 100
    df['Opt -> Venda (%)'] = (df['vendas'] / df['oportunidades'].replace(0, 1)) * 100
    return df

# --- INTERFACE: SIDEBAR (Cadastro de Clientes) ---
st.sidebar.header("⚙️ Configurações")
novo_cliente = st.sidebar.text_input("Novo Cliente")
if st.sidebar.button("Cadastrar Cliente") and novo_cliente:
    conn.execute("INSERT INTO clientes (nome) VALUES (?)", (novo_cliente,))
    conn.commit()
    st.sidebar.success("Cadastrado!")

# Carregar Clientes
clientes_df = pd.read_sql("SELECT * FROM clientes", conn)
cliente_selecionado = st.selectbox("Selecione o Cliente para Analisar/Lançar", clientes_df['nome'].tolist())

# --- INTERFACE: FORMULÁRIO DE LANÇAMENTO ---
with st.expander("📝 Novo Lançamento Semanal", expanded=False):
    with st.form("form_metricas"):
        col1, col2, col3 = st.columns(3)
        data = col1.date_input("Data da Semana", datetime.now())
        flag = col2.selectbox("Flag", ["Manter", "Red Flag", "Onboarding"])
        
        st.divider()
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        inv = c1.number_input("Investimento (R$)", min_value=0.0)
        fat = c2.number_input("Faturamento (R$)", min_value=0.0)
        lds = c3.number_input("Leads", min_value=0)
        mql = c4.number_input("MQL", min_value=0)
        sql = c5.number_input("SQL", min_value=0)
        opt = c6.number_input("Oportunidade", min_value=0)
        vds = c7.number_input("Vendas", min_value=0)
        
        if st.form_submit_button("Salvar Dados"):
            c_id = clientes_df[clientes_df['nome'] == cliente_selecionado]['id'].values[0]
            conn.execute("INSERT INTO metricas VALUES (NULL,?,?,?,?,?,?,?,?,?,?)",
                         (int(c_id), str(data), flag, inv, fat, lds, mql, sql, opt, vds))
            conn.commit()
            st.success("Dados salvos com sucesso!")

# --- INTERFACE: DASHBOARD ---
st.header(f"📊 Dashboard: {cliente_selecionado}")

# Buscar dados do banco
if not clientes_df.empty:
    cid = clientes_df[clientes_df['nome'] == cliente_selecionado]['id'].values[0]
    df_metrics = pd.read_sql(f"SELECT * FROM metricas WHERE cliente_id = {cid} ORDER BY data", conn)
    df_metrics = calcular_kpis(df_metrics)

    if df_metrics is not None and not df_metrics.empty:
        # Métricas de topo (Cards)
        m = df_metrics.iloc[-1] # Última semana
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ROAS", f"{m['ROAS']:.2f}")
        c2.metric("ROI", f"{m['ROI (%)']:.1f}%")
        c3.metric("Conv. Global", f"{m['Conv. Global (%)']:.1f}%")
        c4.metric("Status", m['flag'])

        # Gráfico Comparativo de Evolução
        st.subheader("📈 Evolução Semanal")
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Scatter(x=df_metrics['data'], y=df_metrics['leads'], name="Leads", line=dict(color='blue')))
        fig_evol.add_trace(go.Scatter(x=df_metrics['data'], y=df_metrics['vendas'], name="Vendas", line=dict(color='green')))
        st.plotly_chart(fig_evol, use_container_width=True)

        # Gráfico de Funil (Última Semana)
        st.subheader("🌪️ Saúde do Funil (Eficiência por Etapa)")
        funil_data = [m['L -> MQL (%)'], m['MQL -> SQL (%)'], m['SQL -> Opt (%)'], m['Opt -> Venda (%)']]
        funil_labels = ['Lead > MQL', 'MQL > SQL', 'SQL > Opt', 'Opt > Venda']
        fig_funil = go.Figure(go.Bar(x=funil_labels, y=funil_data, marker_color='red'))
        fig_funil.update_layout(yaxis_title="Percentual %", yaxis_range=[0,100])
        st.plotly_chart(fig_funil, use_container_width=True)
    else:
        st.info("Ainda não há dados lançados para este cliente.")
