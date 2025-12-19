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

# Configurações Iniciais
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

# --- ESTILO CSS (MODERNO E VISÍVEL) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    
    /* Melhoria na visibilidade dos campos de seleção */
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    
    .cartao-container { padding: 20px; border-radius: 15px; margin-bottom: 15px; color: white; min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; }
    .chip { display: inline-block; padding: 2px 10px; border-radius: 12px; background-color: #21262d; color: #8b949e; font-size: 0.8em; margin-right: 6px; border: 1px solid #333; margin-top: 8px; }
    .parcela-tag { background: #30363d; color: #adbac7; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; border: 1px solid #444c56; margin-left: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- FILTRO DE PERÍODO (CALENDÁRIO PARA ANO) ---
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

# Criar dicionário de cores para o histórico
cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}

# Filtrar dados pelo mês/ano selecionado
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
                    # Proteção contra erro de divisão por zero
                    divisor = int(c['parcelas_total']) if int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / divisor)

            st.markdown(f"""
            <div class="cartao-container" style="background:{r['cor']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:1.1em;">{r['nome']}</b>
                    <small style="opacity:0.8;">CREDIT</small>
                </div>
                <div style="font-family:monospace; font-size:1.1em; margin: 15px 0;">**** **** **** {r['final']}</div>
                <div>
                    <small style="opacity:0.8; font-size:0.65em;">FATURA DE {mes_sel.upper()}</small><br>
                    <b style="font-size:1.2em;">{format_real(fatura_mes)}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()

    with st.expander("➕ Adicionar Novo Cartão"):
        with st.form("form_cartao", clear_on_submit=True):
            n_nome = st.text_input("Banco")
            n_cor = st.color_picker("Cor do Cartão", "#8A05BE")
            n_final = st.text_input("4 últimos dígitos", max_chars=4)
            if st.form_submit_button("Salvar Cartão"):
                if n_nome and n_final:
                    supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final}).execute()
                    st.rerun()

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas / AP", "📊 Resumo Mensal"])

# --- ABA DE COMPRAS ---
with tabs[0]:
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            v_col1, v_col2 = st.columns([1.5, 1])
            with v_col1: val_in = st.number_input("Valor", min_value=0.0, format="%.2f", value=None)
            with v_col2: tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            cartoes_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Cartão", options=cartoes_opcoes, index=None, placeholder="Selecione o cartão...")
            quem_compra = st.multiselect("Quem vai pagar?", LISTA_NOMES)
            if st.form_submit_button("🚀 Salvar Compra"):
                if item and val_in and p_at and p_to and cartao_sel and quem_compra:
                    v_calc = val_in * p_to if tipo_in == "Parcela Mensal" else val_in
                    data_s = datetime.now().strftime(f"%d/{mes_idx}/{ano_sel}")
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": v_calc, "cartao": cartao_sel,
                        "parcela_atual": int(p_at), "parcelas_total": int(p_to),
                        "participes": ",".join(quem_compra), "data": data_s
                    }).execute()
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos obrigatórios.")
    with c2:
        st.subheader(f"📋 Histórico ({mes_sel})")
        if not df_compras.empty:
            for _, r in df_compras.sort_values(by="id", ascending=False).iterrows():
                # Correção do NameError: definindo valor da parcela
                div_h = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                v_parcela_h = float(r['valor_total']) / div_h
                cor_v = cores_cartoes.get(r['cartao'], "#ffffff")
                chips_compra = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['nome']}</b> <span class="parcela-tag">{int(r['parcela_atual'])} de {int(r['parcelas_total'])}x</span><br>{chips_compra}</div>
                        <div style="text-align:right;"><b style="color:{cor_v}; font-size:1.1em;">{format_real(v_parcela_h)}</b><br><small>{r['cartao']}</small></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

# --- ABA DE CONTAS FIXAS (BLINDADA CONTRA ERRO DE COLUNA) ---
with tabs[1]:
    f1, f2 = st.columns([1, 1.4])
    with f1:
        st.subheader("🏠 Lançar Gasto Fixo / AP")
        with st.form("form_fixo", clear_on_submit=True):
            tipo_fixo = st.selectbox("Categoria", [
                "Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"
            ], index=None, placeholder="Selecione o tipo...")
            valor_f = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=None)
            quem_fixo = st.multiselect("Responsáveis", LISTA_NOMES)
            if st.form_submit_button("💾 Salvar Fixo"):
                if tipo_fixo and valor_f and quem_fixo:
                    data_f = f"01/{mes_idx}/{ano_sel}"
                    # Enviamos apenas colunas básicas que garantidamente existem no banco
                    supabase.table("fixos").insert({
                        "item": tipo_fixo, 
                        "valor": valor_f, 
                        "participes": ",".join(quem_fixo), 
                        "data": data_f
                    }).execute()
                    st.rerun()
                else:
                    st.error("Preencha categoria, valor e responsáveis.")
    with f2:
        st.subheader(f"📋 Contas de {mes_sel}")
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{r['item']}</b></div>
                        <div style="text-align:right;"><b>{format_real(r['valor'])}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_f_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()

# --- ABA DE RESUMO MENSAL ---
with tabs[2]:
    st.subheader(f"📊 Resumo Geral - {mes_sel}")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    div_r = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / div_r) / len(parts)
        
        total_f = 0.0
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                parts_f = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts_f:
                    total_f += float(r['valor']) / len(parts_f)
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small style="text-transform:uppercase; color:#768390;">{nome}</small><br>
                <b style="font-size:1.7em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:12px; border-top:1px solid #333; padding-top:8px;">
                    🛒 Cartão: {format_real(total_c)}<br>
                    🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
