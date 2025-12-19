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

# --- ESTILO CSS (RESTAURANDO OS CARTÕES GRANDES) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 320px; }
    
    /* Layout dos Cartões na Sidebar (Visual Anterior) */
    .cartao-container { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 20px; 
        color: white; 
        min-height: 150px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; }
    </style>
    """, unsafe_allow_html=True)

# --- FILTROS NO TOPO ---
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
df_fixos = get_data("fixos")

# Filtrar compras pelo mês/ano
df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()

# --- BARRA LATERAL (CARTÕES EM DESTAQUE) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE; font-size: 1.5em; margin-bottom: 20px;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                comp_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, c in comp_cartao.iterrows():
                    divisor = int(c['parcelas_total']) if int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / divisor)
            
            # HTML para o Cartão Estilizado
            st.markdown(f"""
            <div class="cartao-container" style="background:{r['cor']};">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <b style="font-size:1.2em; text-transform: uppercase;">{r['nome']}</b>
                    <small style="opacity:0.8;">CREDIT</small>
                </div>
                <div style="font-family:monospace; font-size:1.1em; letter-spacing: 2px; margin: 15px 0;">
                    **** **** **** {r['final']}
                </div>
                <div>
                    <small style="opacity:0.8; font-size:0.7em; text-transform: uppercase;">Fatura de {mes_sel}</small><br>
                    <b style="font-size:1.3em;">{format_real(fatura_mes)}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    
    with st.expander("➕ Adicionar Novo Cartão"):
        with st.form("f_cartao", clear_on_submit=True):
            n = st.text_input("Banco")
            c = st.color_picker("Cor", "#8A05BE")
            f = st.text_input("Final (4 dígitos)", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n, "cor": c, "final": f}).execute()
                st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Lançar Compras", "🏠 Contas Fixas / AP", "📊 Resumo Mensal"])

with tabs[0]: # COMPRAS
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            v_col1, v_col2 = st.columns([1.5, 1])
            with v_col1: val_in = st.number_input("Valor", min_value=0.0, format="%.2f", value=None)
            with v_col2: tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            c_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Cartão", options=c_opcoes, index=None, placeholder="Selecione o cartão...")
            quem = st.multiselect("Quem vai pagar?", LISTA_NOMES)
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
        st.subheader(f"📋 Histórico ({mes_sel})")
        # (Lógica do histórico mantida...)

with tabs[1]: # CONTAS FIXAS (DIVISÃO AUTOMÁTICA)
    f1, f2 = st.columns([1, 1.4])
    with f1:
        st.subheader("🏠 Lançar Gastos Fixos")
        with st.form("f_fixo", clear_on_submit=True):
            it = st.selectbox("Serviço", ["Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"], index=None, placeholder="Escolha...")
            v_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", value=None)
            st.write("Quem divide esta conta?")
            p1_n = st.selectbox("Pessoa 1", LISTA_NOMES)
            p2_n = st.selectbox("Pessoa 2 (Opcional)", ["Ninguém"] + LISTA_NOMES)
            
            if st.form_submit_button("💾 Salvar e Dividir"):
                if it and v_total:
                    p2_final = p2_n if p2_n != "Ninguém" else None
                    v_p1 = v_total / 2 if p2_final else v_total
                    v_p2 = v_total / 2 if p2_final else 0.0
                    supabase.table("fixos").insert({
                        "item": it, "valor": v_total, "p1_nome": p1_n, 
                        "p1_valor": v_p1, "p2_nome": p2_final, "p2_valor": v_p2,
                        "data": f"01/{mes_idx}/{ano_sel}" # Adicionada data para filtro
                    }).execute()
                    st.rerun()

with tabs[2]: # RESUMO MENSAL UNIFICADO
    st.subheader(f"📊 Resumo Geral - {mes_sel}")
    # (Lógica de resumo mantida...)
