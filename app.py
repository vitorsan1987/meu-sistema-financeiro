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
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    .cartao-container { padding: 20px; border-radius: 15px; margin-bottom: 15px; color: white; min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; }
    .parcela-tag { background: #30363d; color: #adbac7; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; border: 1px solid #444c56; }
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

# --- DADOS ---
df_cartoes = get_data("cartoes")
df_compras_raw = get_data("compras")
df_fixos = get_data("fixos") # Dados de fixos não têm filtro de data no seu banco original

cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}
df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h3 style='color:#8A05BE;'>Meus Cartões</h3>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                comp_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, c in comp_cartao.iterrows():
                    divisor = int(c['parcelas_total']) if int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / divisor)
            st.markdown(f'<div class="cartao-container" style="background:{r["cor"]};"><b>{r["nome"]}</b><br>**** {r["final"]}<br><small>FATURA: {format_real(fatura_mes)}</small></div>', unsafe_allow_html=True)
            if st.button(f"🗑️ {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    with st.expander("➕ Novo Cartão"):
        with st.form("f_cartao", clear_on_submit=True):
            n = st.text_input("Banco"); c = st.color_picker("Cor", "#8A05BE"); f = st.text_input("Final", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n, "cor": c, "final": f}).execute()
                st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas / AP", "📊 Resumo Mensal"])

with tabs[0]: # COMPRAS
    c1, c2 = st.columns([1, 1.4])
    with c1:
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            v_col1, v_col2 = st.columns([1.5, 1])
            with v_col1: val_in = st.number_input("Valor", min_value=0.0, format="%.2f", value=None)
            with v_col2: tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            c_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Cartão", options=c_opcoes, index=None, placeholder="Escolha...")
            quem = st.multiselect("Quem paga?", LISTA_NOMES)
            if st.form_submit_button("🚀 Salvar Compra"):
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
                div_h = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                v_parc = float(r['valor_total']) / div_h
                cor_v = cores_cartoes.get(r['cartao'], "#ffffff")
                chips = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                st.markdown(f'<div class="historico-container"><div style="display:flex; justify-content:space-between;"><div><b>{r["nome"]}</b> <small class="parcela-tag">{int(r["parcela_atual"])} de {int(r["parcelas_total"])}x</small><br>{chips}</div><div style="text-align:right;"><b style="color:{cor_v};">{format_real(v_parc)}</b><br><small>{r["cartao"]}</small></div></div></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[1]: # CONTAS FIXAS (BASEADO NO SEU SQL)
    f1, f2 = st.columns([1, 1.4])
    with f1:
        st.subheader("🏠 Lançar Contas do Apartamento")
        with st.form("f_fixo", clear_on_submit=True):
            it = st.selectbox("Serviço", ["Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"])
            v_f = st.number_input("Valor Total", min_value=0.0)
            st.write("Divisão:")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p1_n = st.selectbox("Pessoa 1", LISTA_NOMES)
                p1_v = st.number_input("Valor P1", min_value=0.0)
            with col_p2:
                p2_n = st.selectbox("Pessoa 2 (Opcional)", ["Ninguém"] + LISTA_NOMES)
                p2_v = st.number_input("Valor P2", min_value=0.0)
            if st.form_submit_button("💾 Salvar Fixo"):
                p2_final = p2_n if p2_n != "Ninguém" else None
                supabase.table("fixos").insert({
                    "item": it, "valor": v_f, "p1_nome": p1_n, "p1_valor": p1_v, "p2_nome": p2_final, "p2_valor": p2_v
                }).execute()
                st.rerun()
    with f2:
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f'<div class="historico-container"><b>{r["item"]}</b>: {format_real(r["valor"])}<br><small>{r["p1_nome"]}: {format_real(r["p1_valor"])} | {r["p2_nome"] if r["p2_nome"] else ""}: {format_real(r["p2_valor"])}</small></div>', unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_f_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]: # RESUMO MENSAL
    st.subheader(f"📊 Resumo Geral - {mes_sel}")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Soma Compras
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    div_r = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / div_r) / len(parts)
        # Soma Fixos (Baseado na sua estrutura SQL)
        total_f = 0.0
        if not df_fixos.empty:
            total_f += df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum()
            total_f += df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome}</small><br><b style="font-size:1.7em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:10px; border-top:1px solid #333; padding-top:8px;">
                    🛒 Cartão: {format_real(total_c)}<br>🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
