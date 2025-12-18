import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro", page_icon="💰", layout="wide")

# Conexão Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- FUNÇÕES ---
def get_data(tabela):
    res = supabase.table(tabela).select("*").execute()
    return pd.DataFrame(res.data)

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; }
    </style>
    """, unsafe_allow_html=True)

# --- DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- INTERFACE ---
tabs = st.tabs(["🛒 Compras", "🏠 Fixas", "📊 Resumo"])

with tabs[0]:
    col1, col2 = st.columns([1, 1.3])
    with col1:
        with st.form("nova_compra"):
            nome = st.text_input("O que comprou?")
            valor = st.number_input("Valor", min_value=0.0)
            cartao = st.selectbox("Cartão", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            
            if st.form_submit_button("🚀 Salvar"):
                if nome and valor > 0 and quem:
                    v_indiv = round(valor / len(quem), 2)
                    supabase.table("compras").insert({
                        "nome": nome, "valor_total": valor, "cartao": cartao,
                        "participes": ",".join(quem), "valor_por_pessoa": v_indiv,
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()

    with col2:
        st.subheader("Histórico")
        if not df_compras.empty:
            for idx, r in df_compras.iloc[::-1].iterrows():
                st.markdown(f'<div class="historico-container"><b>{r["nome"]}</b>: {format_real(r["valor_total"])}<br><small>{r["participes"]}</small></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]:
    st.subheader("Resumo por Pessoa")
    cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        v_c = sum([r['valor_por_pessoa'] for _, r in df_compras.iterrows() if nome in str(r['participes']).split(',')])
        with cols[i]:
            st.markdown(f'<div class="card-resumo"><b>{nome}</b><br>{format_real(v_c)}</div>', unsafe_allow_html=True)
