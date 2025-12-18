import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# Conexão Supabase através das Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- FUNÇÕES DE DADOS ---
def get_data(tabela):
    res = supabase.table(tabela).select("*").execute()
    return pd.DataFrame(res.data)

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- BARRA LATERAL (CARTÕES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            total_card = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum() if not df_compras.empty else 0.0
            st.markdown(f"""
            <div style="background:{r['cor']}; padding:15px; border-radius:10px; margin-bottom:10px; color:white;">
                <b>{r['nome']}</b><br><small>Final {r['final']}</small><br>
                <b>{format_real(total_card)}</b>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️", key=f"del_card_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    
    with st.expander("➕ Novo Cartão"):
        with st.form("f_cartao", clear_on_submit=True):
            n_nome = st.text_input("Banco")
            n_cor = st.color_picker("Cor", "#8A05BE")
            n_final = st.text_input("4 dígitos", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final, "venc": "28"}).execute()
                st.rerun()

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

# --- TAB 1: COMPRAS ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        st.subheader("Novo Gasto")
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("O que comprou?")
            valor = st.number_input("Valor total", min_value=0.0)
            cartao = st.selectbox("Cartão", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            if st.form_submit_button("Salvar"):
                if item and valor > 0 and quem:
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": valor, "cartao": cartao,
                        "participes": ",".join(quem), "valor_por_pessoa": round(valor/len(quem), 2),
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()
    with c2:
        st.subheader("Histórico")
        for _, r in df_compras.iloc[::-1].iterrows():
            st.markdown(f'<div class="historico-container"><b>{r["nome"]}</b> - {format_real(r["valor_total"])}<br><small>{r["participes"]}</small></div>', unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_h_{r['id']}"):
                supabase.table("compras").delete().eq("id", r['id']).execute()
                st.rerun()

# --- TAB 2: CONTAS FIXAS (ATUALIZADA) ---
with tabs[1]:
    col_f1, col_f2 = st.columns([1, 1.3])
    
    with col_f1:
        st.subheader("Registar Conta Fixa")
        with st.form("f_fixo", clear_on_submit=True):
            servico = st.text_input("Serviço (ex: Aluguer, Netflix)")
            valor_f = st.number_input("Valor Mensal", min_value=0.0)
            st.write("Quem paga?")
            p1 = st.selectbox("Pessoa 1", LISTA_NOMES, index=0)
            p1_v = st.number_input("Quanto a Pessoa 1 paga?", min_value=0.0)
            p2 = st.selectbox("Pessoa 2 (Opcional)", ["Ninguém"] + LISTA_NOMES, index=0)
            p2_v = st.number_input("Quanto a Pessoa 2 paga?", min_value=0.0)
            
            if st.form_submit_button("📌 Salvar Conta Fixa"):
                supabase.table("fixos").insert({
                    "item": servico,
                    "valor": valor_f,
                    "p1_nome": p1,
                    "p1_valor": p1_v,
                    "p2_nome": "" if p2 == "Ninguém" else p2,
                    "p2_valor": p2_v
                }).execute()
                st.rerun()

    with col_f2:
        st.subheader("Lista de Contas Fixas")
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f"""
                <div class="historico-container">
                    <b>{r['item']}</b> - <span style="color:#8A05BE;">{format_real(r['valor'])}</span><br>
                    <small>{r['p1_nome']}: {format_real(r['p1_valor'])} 
                    {f" | {r['p2_nome']}: {format_real(r['p2_valor'])}" if r['p2_nome'] else ""}</small>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Remover", key=f"del_fixo_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()

# --- TAB 3: RESUMO ---
with tabs[2]:
    st.subheader("Resumo Geral")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Compras variáveis
        total_c = sum([r['valor_por_pessoa'] for _, r in df_compras.iterrows() if nome in str(r['participes']).split(',')])
        # Contas fixas (verifica se o nome está em p1 ou p2)
        total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + \
                  df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with res_cols[i]:
            st.markdown(f'<div class="card-resumo"><small>{nome}</small><br><b>{format_real(total_c + total_f)}</b><br><small style="font-size:0.7em;">Fixas: {format_real(total_f)}</small></div>', unsafe_allow_html=True)
