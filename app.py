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
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

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
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 320px; }
    .cartao-container { 
        padding: 20px; border-radius: 15px; margin-bottom: 20px; color: white; 
        min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.1);
    }
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; border-left: 5px solid #8A05BE; }
    .chip { display: inline-block; padding: 2px 10px; border-radius: 12px; background-color: #21262d; color: #8b949e; font-size: 0.8em; margin-right: 6px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- FILTROS ---
st.markdown("## 📊 Controle Financeiro")
col_m1, col_m2 = st.columns([1, 1])
with col_m1:
    mes_sel = st.selectbox("📅 Selecione o Mês", MESES, index=datetime.now().month - 1)
with col_m2:
    data_ano = st.date_input("📅 Selecione o Ano", value=datetime.now())
    ano_sel = data_ano.year

mes_idx = str(MESES.index(mes_sel) + 1).zfill(2)
filtro_data = f"/{mes_idx}/{ano_sel}"

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras_raw = get_data("compras")
df_fixos_raw = get_data("fixos")

# Cores para o histórico
cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}

# Filtrar compras (Essencial para o resumo)
df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()

# Filtrar fixos (Se não houver coluna data, usamos todos os fixos cadastrados)
if not df_fixos_raw.empty and 'data' in df_fixos_raw.columns:
    df_fixos = df_fixos_raw[df_fixos_raw['data'].str.contains(filtro_data)]
else:
    df_fixos = df_fixos_raw

# --- SIDEBAR (CARTÕES REVISADOS) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                comp_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, c in comp_cartao.iterrows():
                    divisor = int(c['parcelas_total']) if int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / divisor)
            
            st.markdown(f"""
            <div class="cartao-container" style="background:{r['cor']};">
                <div><b>{r['nome']}</b></div>
                <div style="font-family:monospace;">**** {r['final']}</div>
                <div><small>Fatura {mes_sel}:</small><br><b>{format_real(fatura_mes)}</b></div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    
    with st.expander("➕ Adicionar Cartão"):
        with st.form("f_cartao", clear_on_submit=True):
            n = st.text_input("Banco"); c = st.color_picker("Cor", "#8A05BE"); f = st.text_input("Final", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n, "cor": c, "final": f}).execute()
                st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Lançar Compras", "🏠 Contas Fixas / AP", "📊 Resumo Mensal"])

with tabs[0]: # COMPRAS
    c1, c2 = st.columns([1, 1.4])
    with c1:
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            val_in = st.number_input("Valor", min_value=0.0, value=None)
            tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            c_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Cartão", options=c_opcoes, index=None)
            quem = st.multiselect("Quem paga?", LISTA_NOMES)
            if st.form_submit_button("🚀 Salvar"):
                if item and val_in and p_at and p_to and cartao_sel and quem:
                    v_calc = val_in * p_to if tipo_in == "Parcela Mensal" else val_in
                    data_s = datetime.now().strftime(f"%d/{mes_idx}/{ano_sel}")
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": v_calc, "cartao": cartao_sel,
                        "parcela_atual": int(p_at), "parcelas_total": int(p_to),
                        "participes": ",".join(quem), "data": data_s
                    }).execute()
                    st.rerun()
    with c2:
        if not df_compras.empty:
            for _, r in df_compras.sort_values(by="id", ascending=False).iterrows():
                div = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                v_p = float(r['valor_total']) / div
                chips = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                st.markdown(f'<div class="historico-container"><b>{r["nome"]}</b> ({int(r["parcela_atual"])}/{int(r["parcelas_total"])})<br>{chips}<br><b style="color:{cores_cartoes.get(r["cartao"], "#fff")}">{format_real(v_p)}</b></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[1]: # FIXAS (DIVISÃO AUTOMÁTICA)
    f1, f2 = st.columns([1, 1.4])
    with f1:
        with st.form("f_fixo", clear_on_submit=True):
            it = st.selectbox("Serviço", ["Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"])
            v_t = st.number_input("Valor Total", min_value=0.0)
            p1_n = st.selectbox("Pessoa 1", LISTA_NOMES)
            p2_n = st.selectbox("Pessoa 2", ["Ninguém"] + LISTA_NOMES)
            if st.form_submit_button("💾 Salvar"):
                p2_f = p2_n if p2_n != "Ninguém" else None
                v_p1 = v_t / 2 if p2_f else v_t
                v_p2 = v_t / 2 if p2_f else 0.0
                supabase.table("fixos").insert({
                    "item": it, "valor": v_t, "p1_nome": p1_n, "p1_valor": v_p1, "p2_nome": p2_f, "p2_valor": v_p2
                }).execute()
                st.rerun()
    with f2:
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f'<div class="historico-container"><b>{r["item"]}</b>: {format_real(r["valor"])}<br><small>{r["p1_nome"]} e {r["p2_nome"]}</small></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_f_{r['id']}"):
                    supabase.table("fixos").delete().eq( "id", r['id']).execute()
                    st.rerun()

with tabs[2]: # RESUMO (CORRIGIDO)
    st.subheader(f"📊 Resumo Geral - {mes_sel}")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Soma Compras
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    div = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / div) / len(parts)
        
        # Soma Fixos (Lógica Robusta)
        total_f = 0.0
        if not df_fixos.empty:
            # Soma onde a pessoa é P1
            soma_p1 = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum()
            # Soma onde a pessoa é P2
            soma_p2 = df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
            total_f = float(soma_p1) + float(soma_p2)
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome.upper()}</small><br>
                <b style="font-size:1.8em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.8em; color:#8b949e; margin-top:15px;">
                    🛒 Cartão: {format_real(total_c)}<br>
                    🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
