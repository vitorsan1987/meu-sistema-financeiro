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
    try:
        res = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; min-height: 160px; }
    .parcela-tag { background: #8A05BE; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: bold; }
    .info-preview { background: #21262d; padding: 10px; border-radius: 5px; border-left: 5px solid #8A05BE; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- SIDEBAR (CARTÕES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            total_card = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum() if not df_compras.empty else 0.0
            st.markdown(f"""
            <div style="background:{r['cor']}; padding:15px; border-radius:10px; margin-bottom:10px; color:white;">
                <b>{r['nome']}</b><br>Total: {format_real(total_card)}
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()

# --- CONTEÚDO ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            valor_total_compra = st.number_input("Valor Total da Dívida (Parcela x Vezes)", min_value=0.0)
            
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                p_atual = st.number_input("Parcela Atual", min_value=1, value=1)
            with p_col2:
                p_total = st.number_input("Total de Parcelas", min_value=1, value=1)
            
            cartao = st.selectbox("Cartão", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            
            # --- PREVIEW DO CÁLCULO ---
            if valor_total_compra > 0 and len(quem) > 0:
                v_parc = valor_total_compra / p_total
                v_indiv = v_parc / len(quem)
                st.markdown(f"""
                <div class="info-preview">
                    <b>Resumo do Cálculo Mensal:</b><br>
                    Parcela cheia: {format_real(v_parc)}<br>
                    Cada um paga: <b>{format_real(v_indiv)}</b>
                </div>
                """, unsafe_allow_html=True)

            if st.form_submit_button("🚀 Salvar no Banco"):
                if item and valor_total_compra > 0 and quem:
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": valor_total_compra, "cartao": cartao,
                        "parcela_atual": int(p_atual), "parcelas_total": int(p_total),
                        "participes": ",".join(quem), "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()

    with c2:
        st.subheader("📋 Histórico")
        if not df_compras.empty:
            for _, r in df_compras.iloc[::-1].iterrows():
                v_at = int(r['parcela_atual'])
                v_to = int(r['parcelas_total'])
                txt_p = f"<span class='parcela-tag'>{min(v_at, v_to)} de {max(v_at, v_to)}x</span>" if max(v_at, v_to) > 1 else ""
                st.markdown(f"""
                <div class="historico-container">
                    <b>{r['nome']}</b> {txt_p} <br>
                    Total: {format_real(r['valor_total'])}
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Apagar", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]:
    st.subheader("📊 Resumo Mensal (Apenas a parcela do mês)")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c_mes = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                participantes = [p.strip() for p in str(r['participes']).split(',')]
                if nome in participantes:
                    # Cálculo: (Valor Total / Maior número de parcelas) / Qtd de Pessoas
                    v_base = float(r['valor_total']) / max(int(r['parcela_atual']), int(r['parcelas_total']))
                    total_c_mes += v_base / len(participantes)
        
        total_f = 0.0
        if not df_fixos.empty:
            total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + \
                      df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome}</small><br>
                <b style="font-size:1.6em;">{format_real(total_c_mes + total_f)}</b><br>
                <div style="font-size:0.75em; color:#8b949e; margin-top:10px;">
                    Compras Parc: {format_real(total_c_mes)}<br>
                    Fixos: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
