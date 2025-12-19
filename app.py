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

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; min-height: 160px; }
    .parcela-tag { background: #8A05BE; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: bold; }
    .info-preview { background: #21262d; padding: 10px; border-radius: 5px; border-left: 5px solid #00ff00; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            total_card = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum() if not df_compras.empty else 0.0
            st.markdown(f'<div style="background:{r["cor"]}; padding:15px; border-radius:10px; margin-bottom:10px;"><b>{r["nome"]}</b><br>Total Ocupado: {format_real(total_card)}</div>', unsafe_allow_html=True)

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    c1, c2 = st.columns([1, 1.3])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição (Ex: Empréstimo)")
            
            # OPÇÃO DE ENTRADA
            tipo_valor = st.radio("Como deseja inserir o valor?", ["Valor da Parcela (Mensal)", "Valor Total da Compra"])
            valor_digitado = st.number_input("Valor", min_value=0.0, format="%.2f")
            
            p_at = st.number_input("Parcela Atual", min_value=1, value=1)
            p_to = st.number_input("Total de Parcelas", min_value=1, value=1)
            
            cartao_sel = st.selectbox("Cartão", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            
            # LÓGICA DE CÁLCULO PARA O BANCO
            if tipo_valor == "Valor da Parcela (Mensal)":
                valor_para_banco = valor_digitado * p_to
            else:
                valor_para_banco = valor_digitado

            # PREVIEW EM TEMPO REAL
            if valor_digitado > 0 and len(quem) > 0:
                v_mensal_cheio = valor_para_banco / p_to
                v_cada_um = v_mensal_cheio / len(quem)
                st.markdown(f"""
                <div class="info-preview">
                    <b>Confirmação do Resumo:</b><br>
                    Parcela Mensal Total: {format_real(v_mensal_cheio)}<br>
                    Cada pessoa pagará: <b>{format_real(v_cada_um)}</b>
                </div>
                """, unsafe_allow_html=True)

            if st.form_submit_button("🚀 Salvar Gasto"):
                if item and valor_digitado > 0 and quem:
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": valor_para_banco, "cartao": cartao_sel,
                        "parcela_atual": int(p_at), "parcelas_total": int(p_to),
                        "participes": ",".join(quem), "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()

    with c2:
        st.subheader("📋 Histórico")
        if not df_compras.empty:
            for _, r in df_compras.iloc[::-1].iterrows():
                v_at, v_to = int(r['parcela_atual']), int(r['parcelas_total'])
                txt_p = f"<span class='parcela-tag'>{min(v_at, v_to)} de {max(v_at, v_to)}x</span>" if max(v_at, v_to) > 1 else ""
                st.markdown(f'<div class="historico-container"><b>{r["nome"]}</b> {txt_p}<br>Total: {format_real(r["valor_total"])}</div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]:
    st.subheader("📊 Resumo Mensal (Parcelas do Mês)")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c_mes = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                participantes = [p.strip() for p in str(r['participes']).split(',')]
                if nome in participantes:
                    # Cálculo: (Valor Total / Parcelas Totais) / Qtd de Pessoas
                    v_parc_cheia = float(r['valor_total']) / max(int(r['parcelas_total']), 1)
                    total_c_mes += v_parc_cheia / len(participantes)
        
        total_f = 0.0
        if not df_fixos.empty:
            total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome}</small><br>
                <b style="font-size:1.6em;">{format_real(total_c_mes + total_f)}</b><br>
                <div style="font-size:0.75em; color:#8b949e; margin-top:10px;">
                Compras: {format_real(total_c_mes)}<br>
                Fixos: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
