import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# Conexão Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def get_data(tabela):
    try:
        res = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; }
    .chip { display: inline-block; padding: 2px 10px; border-radius: 12px; background-color: #21262d; color: #8b949e; font-size: 0.8em; margin-right: 6px; border: 1px solid #333; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- FILTROS DE TOPO ---
st.markdown("## 📊 Controle Financeiro")
col_m1, col_m2 = st.columns([1, 1])
with col_m1:
    mes_selecionado = st.selectbox("📅 Selecione o Mês", MESES, index=datetime.now().month - 1)
with col_m2:
    data_ano = st.date_input("📅 Selecione o Ano", value=datetime.now())
    ano_selecionado = data_ano.year

mes_idx = str(MESES.index(mes_selecionado) + 1).zfill(2)
filtro_data = f"/{mes_idx}/{ano_selecionado}"

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras_raw = get_data("compras")
df_fixos_raw = get_data("fixos")

cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}
df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()
df_fixos = df_fixos_raw[df_fixos_raw['data'].str.contains(filtro_data)] if not df_fixos_raw.empty else pd.DataFrame()

# --- BARRA LATERAL (CARTÕES) ---
with st.sidebar:
    st.markdown("<h3 style='color:#8A05BE;'>Meus Cartões</h3>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                comp_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, c in comp_cartao.iterrows():
                    total_p = int(c['parcelas_total']) if c['parcelas_total'] and int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / total_p)

            st.markdown(f"""
            <div style="padding:20px; border-radius:15px; background:{r['cor']}; color:white; margin-bottom:10px;">
                <b>{r['nome']}</b><br>**** {r['final']}<br>
                <small>FATURA: {format_real(fatura_mes)}</small>
            </div>
            """, unsafe_allow_html=True)
    
    with st.expander("➕ Novo Cartão"):
        with st.form("add_card"):
            n = st.text_input("Banco")
            c = st.color_picker("Cor", "#8A05BE")
            f = st.text_input("Final", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n, "cor": c, "final": f}).execute()
                st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]: # ABA COMPRAS
    c1, c2 = st.columns([1, 1.4])
    with c1:
        with st.form("form_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            v_col1, v_col2 = st.columns([1.5, 1])
            with v_col1: val_in = st.number_input("Valor", min_value=0.0, format="%.2f", value=None)
            with v_col2: tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            c_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Cartão", options=c_opcoes, index=None, placeholder="Selecione...")
            quem = st.multiselect("Quem paga?", LISTA_NOMES)
            if st.form_submit_button("🚀 Salvar Compra"):
                if item and val_in and p_at and p_to and cartao_sel and quem:
                    v_calc = val_in * p_to if tipo_in == "Parcela Mensal" else val_in
                    data_s = datetime.now().strftime(f"%d/{mes_idx}/{ano_selecionado}")
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": v_calc, "cartao": cartao_sel,
                        "parcela_atual": int(p_at), "parcelas_total": int(p_to),
                        "participes": ",".join(quem), "data": data_s
                    }).execute()
                    st.rerun()

    with c2: # HISTÓRICO COMPRAS
        if not df_compras.empty:
            for _, r in df_compras.sort_values(by="id", ascending=False).iterrows():
                # Correção do NameError: definindo v_mensal corretamente
                p_total_h = int(r['parcelas_total']) if r['parcelas_total'] and int(r['parcelas_total']) > 0 else 1
                v_mensal = float(r['valor_total']) / p_total_h
                cor_v = cores_cartoes.get(r['cartao'], "#ffffff")
                chips = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['nome']}</b> <small>{int(r['parcela_atual'])} de {p_total_h}x</small><br>{chips}</div>
                        <div style="text-align:right;"><b style="color:{cor_v};">{format_real(v_mensal)}</b><br><small>{r['cartao']}</small></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_c_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[1]: # ABA CONTAS FIXAS
    f1, f2 = st.columns([1, 1.4])
    with f1:
        st.markdown("### Lançar Gasto Fixo / AP")
        with st.form("form_fixo", clear_on_submit=True):
            tipo_fixo = st.selectbox("Categoria", ["Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"], index=None, placeholder="Selecione...")
            valor_f = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=None)
            # USANDO NOMES SIMPLES PARA O BANCO (p1_nome, p1_valor) para evitar erros de colunas novas
            p_quem = st.multiselect("Responsáveis", LISTA_NOMES)
            if st.form_submit_button("💾 Salvar Fixo"):
                if tipo_fixo and valor_f and p_quem:
                    data_f = f"01/{mes_idx}/{ano_selecionado}"
                    # Tentativa de salvar. Se der erro de coluna, o Supabase avisará.
                    # DICA: Verifique se sua tabela 'fixos' tem as colunas 'item', 'valor', 'participes', 'data'
                    supabase.table("fixos").insert({
                        "item": tipo_fixo, 
                        "valor": valor_f, 
                        "participes": ",".join(p_quem), 
                        "data": data_f
                    }).execute()
                    st.rerun()

    with f2:
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['item']}</b></div>
                        <div><b>{format_real(r['valor'])}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_f_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]: # RESUMO MENSAL
    st.subheader(f"📊 Resumo Geral - {mes_selecionado}")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Soma Compras
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    p_div = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / p_div) / len(parts)
        # Soma Fixos
        total_f = 0.0
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                parts_f = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts_f:
                    total_f += float(r['valor']) / len(parts_f)
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome}</small><br><b style="font-size:1.5em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.8em; color:#8b949e; margin-top:10px;">
                    🛒 Cartão: {format_real(total_c)}<br>🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
