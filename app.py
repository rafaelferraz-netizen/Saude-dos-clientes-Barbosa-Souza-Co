import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="V4 Gestão Cloud", layout="wide")

# Conectando ao Supabase (Ele vai buscar as chaves automaticamente)
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🛡️ Sistema de Gestão V4 + Supabase")

# 1. BUSCAR CLIENTES PARA O DROPDOWN
clientes = conn.table("clientes").select("id, nome_cliente").execute()
lista_clientes = {c['nome_cliente']: c['id'] for c in clientes.data}

# 2. FORMULÁRIO DENSO DE LANÇAMENTO
with st.expander("📝 Novo Lançamento Semanal", expanded=True):
    with st.form("form_v4"):
        c1, c2, c3 = st.columns(3)
        cliente_nome = c1.selectbox("Cliente", options=list(lista_clientes.keys()))
        data = c2.date_input("Data")
        flag = c3.selectbox("Flag", ["Manter", "Red Flag", "Onboarding"])

        st.divider()
        f1, f2, l1, l2, l3, l4, l5 = st.columns(7)
        inv = f1.number_input("Investimento", min_value=0.0)
        fat = f2.number_input("Faturamento", min_value=0.0)
        lds = l1.number_input("Leads", min_value=0)
        mql = l2.number_input("MQL", min_value=0)
        sql = l3.number_input("SQL", min_value=0)
        opt = l4.number_input("Oport.", min_value=0)
        vds = l5.number_input("Vendas", min_value=0)

        if st.form_submit_button("Salvar no Supabase"):
            dados = {
                "cliente_id": lista_clientes[cliente_nome],
                "data_registro": str(data),
                "flag": flag,
                "investimento_midia": inv,
                "faturamento_cliente": fat,
                "leads": lds,
                "mql": mql,
                "sql_leads": sql,
                "oportunidades": opt,
                "vendas": vds
            }
            conn.table("metricas_semanais").insert(dados).execute()
            st.success("Dados persistidos com sucesso!")

# 3. DASHBOARD (Busca os últimos 10 registros)
st.divider()
st.subheader("📊 Últimos Lançamentos")
historico = conn.table("metricas_semanais").select("*").limit(10).execute()
if historico.data:
    st.table(historico.data)
