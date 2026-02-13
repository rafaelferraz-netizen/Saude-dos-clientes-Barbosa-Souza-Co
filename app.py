import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="V4 Company - Gestão Interna", layout="wide", page_icon="🚀")

# --- LOGIN SIMPLIFICADO (TESTE) ---
if "logado" not in st.session_state:
    st.session_state["logado"] = False

if not st.session_state["logado"]:
    st.title("Acesso Restrito V4")
    user = st.text_input("Usuário")
    pw = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        # Verificação de texto simples para evitar erros de biblioteca
        if user == "admin" and pw == "v4123":
            st.session_state["logado"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")
else:
    # --- INTERFACE LOGADA ---
    if st.sidebar.button("Sair"):
        st.session_state["logado"] = False
        st.rerun()

    st.sidebar.image("https://v4company.com/wp-content/uploads/2021/08/logo-v4.png", width=100)
    
try:
    # Força o Streamlit a reconhecer a conexão baseada nos Secrets
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as e:
    st.error("⚠️ Erro de Configuração detectado!")
    st.info("As chaves foram inseridas, mas o sistema ainda não as validou.")
    st.write("Erro técnico:", e)
    if st.button("Tentar Reconectar Agora"):
        st.rerun()
    st.stop()

    st.title(f"📊 Dashboard de Performance - Unidade V4")

    # --- ABAS ---
    tab1, tab2 = st.tabs(["📝 Lançar Dados", "📈 Dashboard"])

    with tab1:
        res_clientes = conn.table("clientes").select("id, nome_cliente").execute()
        clientes_dict = {c['nome_cliente']: c['id'] for c in res_clientes.data} if res_clientes.data else {}

        if not clientes_dict:
            st.warning("Nenhum cliente cadastrado no Supabase.")
        else:
            with st.form("form_metricas", clear_on_submit=True):
                st.subheader("Entrada Semanal de Dados")
                c1, c2, c3 = st.columns(3)
                sel_cliente = c1.selectbox("Cliente", options=list(clientes_dict.keys()))
                sel_data = c2.date_input("Data da Semana")
                sel_flag = c3.selectbox("Status (Flag)", ["Manter", "Red Flag", "Onboarding"])

                st.divider()
                f1, f2, l1, l2, l3, l4, l5 = st.columns(7)
                inv = f1.number_input("Investimento (R$)", min_value=0.0)
                fat = f2.number_input("Faturam. (R$)", min_value=0.0)
                lds = l1.number_input("Leads", min_value=0)
                mql = l2.number_input("MQL", min_value=0)
                sql = l3.number_input("SQL", min_value=0)
                opt = l4.number_input("Oport.", min_value=0)
                vds = l5.number_input("Vendas", min_value=0)

                if st.form_submit_button("Salvar Métricas"):
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
                    st.success(f"Dados salvos!")

    with tab2:
        if clientes_dict:
            cliente_dash = st.selectbox("Filtrar Dashboard", options=list(clientes_dict.keys()))
            id_c = clientes_dict[cliente_dash]
            res_m = conn.table("metricas_semanais").select("*").eq("cliente_id", id_c).order("data_registro").execute()
            
            if res_m.data:
                df = pd.DataFrame(res_m.data)
                ultima = df.iloc[-1]
                roas = ultima['faturamento_cliente'] / ultima['investimento_midia'] if ultima['investimento_midia'] > 0 else 0
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Investimento", f"R$ {ultima['investimento_midia']:,.2f}")
                m2.metric("Faturamento", f"R$ {ultima['faturamento_cliente']:,.2f}")
                m3.metric("ROAS", f"{roas:.2f}")
                m4.metric("Leads", ultima['leads'])

                fig = go.Figure(go.Funnel(y=['Leads', 'MQL', 'SQL', 'Oport.', 'Vendas'], 
                                          x=[ultima['leads'], ultima['mql'], ultima['sql_leads'], ultima['oportunidades'], ultima['vendas']],
                                          marker={"color": "red"}))
                st.plotly_chart(fig, use_container_width=True)
