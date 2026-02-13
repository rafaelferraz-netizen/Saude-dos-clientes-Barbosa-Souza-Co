import streamlit as st
import streamlit_authenticator as stauth
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="V4 Company - Gestão Interna", layout="wide", page_icon="🚀")

# --- 1. AUTENTICAÇÃO (LOGIN) ---
# Substitua a senha abaixo pelo hash da sua senha preferida futuramente
names = ["Franqueado V4"]
usernames = ["admin"]
passwords = ["$2b$12$K.lVz8f5fF5vXy7pY.GkReFp/W2yG3k6Z.S1v0VqE2mRjX/3U2C/G"] # v4company123

authenticator = stauth.Authenticate(
    {"usernames": {usernames[0]: {"name": names[0], "password": passwords[0]}}},
    "v4_auth_cookie", "signature_key", cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Acesso Restrito", "main")

if authentication_status:
    # --- INTERFACE LOGADA ---
    authenticator.logout("Sair", "sidebar")
    st.sidebar.image("https://v4company.com/wp-content/uploads/2021/08/logo-v4.png", width=100)
    
    # Conexão Supabase
    conn = st.connection("supabase", type=SupabaseConnection)

    st.title(f"📊 Dashboard de Performance - Unidade V4")

    # --- ABA 1: LANÇAMENTO ---
    tab1, tab2 = st.tabs(["📝 Lançar Dados", "📈 Dashboard"])

    with tab1:
        # Buscar clientes do banco
        res_clientes = conn.table("clientes").select("id, nome_cliente").execute()
        clientes_dict = {c['nome_cliente']: c['id'] for c in res_clientes.data} if res_clientes.data else {}

        if not clientes_dict:
            st.warning("Nenhum cliente cadastrado. Cadastre um cliente no painel do Supabase primeiro.")
        else:
            with st.form("form_metricas", clear_on_submit=True):
                st.subheader("Entrada Semanal de Dados")
                c1, c2, c3 = st.columns(3)
                sel_cliente = c1.selectbox("Cliente", options=list(clientes_dict.keys()))
                sel_data = c2.date_input("Data da Semana")
                sel_flag = c3.selectbox("Status (Flag)", ["Manter", "Red Flag", "Onboarding"])

                st.divider()
                f1, f2, l1, l2, l3, l4, l5 = st.columns(7)
                inv = f1.number_input("Investimento (R$)", min_value=0.0, step=100.0)
                fat = f2.number_input("Faturam. (R$)", min_value=0.0, step=100.0)
                lds = l1.number_input("Leads", min_value=0)
                mql = l2.number_input("MQL", min_value=0)
                sql = l3.number_input("SQL", min_value=0)
                opt = l4.number_input("Oport.", min_value=0)
                vds = l5.number_input("Vendas", min_value=0)

                if st.form_submit_button("Salvar Métricas na Nuvem"):
                    payload = {
                        "cliente_id": clientes_dict[sel_cliente],
                        "data_registro": str(sel_data),
                        "flag": sel_flag,
                        "investimento_midia": inv,
                        "faturamento_cliente": fat,
                        "leads": lds,
                        "mql": mql,
                        "sql_leads": sql,
                        "oportunidades": opt,
                        "vendas": vds
                    }
                    conn.table("metricas_semanais").insert(payload).execute()
                    st.success(f"Dados de {sel_cliente} salvos com sucesso!")

    with tab2:
        # --- ABA 2: VISUALIZAÇÃO ---
        if clientes_dict:
            cliente_dash = st.selectbox("Filtrar Dashboard por Cliente", options=list(clientes_dict.keys()))
            id_c = clientes_dict[cliente_dash]
            
            # Buscar métricas
            res_m = conn.table("metricas_semanais").select("*").eq("cliente_id", id_c).order("data_registro").execute()
            
            if res_m.data:
                df = pd.DataFrame(res_m.data)
                
                # Cálculos Rápidos
                ultima = df.iloc[-1]
                roas = ultima['faturamento_cliente'] / ultima['investimento_midia'] if ultima['investimento_midia'] > 0 else 0
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Investimento (Últ.)", f"R$ {ultima['investimento_midia']:,.2f}")
                m2.metric("Faturamento (Últ.)", f"R$ {ultima['faturamento_cliente']:,.2f}")
                m3.metric("ROAS", f"{roas:.2f}")
                m4.metric("Leads", ultima['leads'])

                # Gráfico de Funil Simples
                st.subheader("Eficiência do Funil")
                labels = ['Leads', 'MQL', 'SQL', 'Oport.', 'Vendas']
                values = [ultima['leads'], ultima['mql'], ultima['sql_leads'], ultima['oportunidades'], ultima['vendas']]
                fig = go.Figure(go.Funnel(y=labels, x=values, marker={"color": "red"}))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Ainda não há dados históricos para este cliente.")

elif authentication_status == False:
    st.error("Usuário/Senha incorretos.")
elif authentication_status == None:
    st.warning("Por favor, faça login para acessar os dados da unidade.")
