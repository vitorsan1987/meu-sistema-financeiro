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

# Configurações de Nomes e Datas
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

# --- ESTILO CSS (MODERNO E SCANNABLE) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    
    /* Estilização do Selectbox para maior visibilidade */
    div[data-baseweb="select"] {
        background-color: #1c2128 !important;
        border-radius: 8px !important;
        border: 1px solid #444c56 !important;
    }
    
    /* Cartão na Sidebar */
    .cartao-container { 
        padding: 20px; border-radius: 15px; margin-bottom: 15px; color: white; 
        min-height: 150px; display: flex; flex-direction: column; justify-content: space-between; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
    }
    
    /* Histórico */
    .historico-container { 
        background: #1c2128; padding: 18px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 12px; 
    }
    
    /* Resumo Mensal */
    .card-resumo { 
        background: #1c2128; padding: 20px; border-radius: 12px; 
        border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; 
    }
    
    /* Tags */
    .parcela-tag { 
        background: #30363d; color: #adbac7; padding: 2px 8px; border-radius: 4px; 
        font-size: 0.75em; font-weight: bold; border: 1px solid #444c56; margin-left: 8px;
    }
    
    .chip { 
        display: inline-block; padding: 2px 10px; border-radius: 12px; 
        background-color: #21262d; color: #8b949e; font-size: 0.8em; 
        margin-right: 6px; border: 1px solid #333; margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FILTRO DE PERÍODO (MÊS E CALENDÁRIO) ---
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
df_fixos = get_data("fixos")

cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}
df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()

# --- BARRA LATERAL (GESTÃO DE CARTÕES) ---
with st.sidebar:
    st.markdown("<h3 style='color:#8A05BE;'>Meus Cartões</h3>", unsafe_allow_html=True)
    
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                comp_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, c in comp_cartao.iterrows():
                    divisor = int(c['parcelas_total']) if c['parcelas_total'] and int(c['parcelas_total']) > 0 else 1
                    fatura_mes += (float(c['valor_total']) / divisor)

            st.markdown(f"""
            <div class="cartao-container" style="background:{r['cor']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:1.1em;">{r['nome']}</b>
                    <small style="opacity:0.8;">CREDIT</small>
                </div>
                <div style="font-family:monospace; font-size:1.1em; margin: 15px 0;">**** **** **** {r['final']}</div>
                <div>
                    <small style="opacity:0.8; font-size:0.65em;">FATURA DE {mes_selecionado.upper()}</small><br>
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
                    supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final, "venc": "28"}).execute()
                    st.rerun()

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Lançar Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]: 
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            item = st.text_input("O que comprou?")
            
            v_col1, v_col2 = st.columns([1.5, 1])
            with v_col1:
                val_in = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=None)
            with v_col2:
                tipo_in = st.selectbox("Lançar por:", ["Parcela Mensal", "Valor Total"])
            
            p_col1, p_col2 = st.columns(2)
            with p_col1: p_at = st.number_input("Parc. Atual", min_value=1, value=None)
            with p_col2: p_to = st.number_input("Total Parc.", min_value=1, value=None)
            
            cartoes_opcoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else []
            cartao_sel = st.selectbox("Selecione o Cartão", options=cartoes_opcoes, index=None, placeholder="Clique para selecionar...")
            
            quem = st.multiselect("Quem vai pagar?", LISTA_NOMES)
            
            if st.form_submit_button("🚀 Salvar Gasto"):
                if item and val_in and p_at and p_to and cartao_sel and quem:
                    v_calc = val_in * p_to if tipo_in == "Parcela Mensal" else val_in
                    data_s = datetime.now().strftime(f"%d/{mes_idx}/{ano_selecionado}")
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": v_calc, "cartao": cartao_sel,
                        "parcela_atual": int(p_at), "parcelas_total": int(p_to),
                        "participes": ",".join(quem), "data": data_s
                    }).execute()
                    st.rerun()
                else:
                    st.warning("Por favor, preencha todos os campos e selecione o cartão.")
                    
    with c2:
        st.subheader(f"📋 Histórico ({mes_selecionado})")
        if not df_compras.empty:
            for _, r in df_compras.sort_values(by="id", ascending=False).iterrows():
                divisor_h = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                v_mensal = float(r['valor_total']) / divisor_h
                cor_v = cores_cartoes.get(r['cartao'], "#ffffff")
                chips = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <b>{r['nome']}</b> <span class='parcela-tag'>{int(r['parcela_atual'])} de {int(r['parcelas_total'])}x</span>
                            <div style="margin-top:2px;">{chips}</div>
                        </div>
                        <div style="text-align:right;">
                            <b style="color:{cor_v}; font-size:1.2em;">{format_real(v_mes)}</b>
                            <div style="font-size:0.75em; color:#8b949e; margin-top:4px;">{r['cartao']} | {r['data']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Apagar", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]: 
    st.subheader(f"📊 Resumo Geral ({mes_selecionado})")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    divisor_r = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / divisor_r) / len(parts)
        
        total_f = 0.0
        if not df_fixos.empty and 'p1_nome' in df_fixos.columns:
            f1 = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum()
            f2 = df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum() if 'p2_nome' in df_fixos.columns else 0.0
            total_f = float(f1 + f2)
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small style="text-transform:uppercase; color:#768390;">{nome}</small><br>
                <b style="font-size:1.7em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:12px; border-top:1px solid #333; padding-top:8px;">
                    🛒 Compras: {format_real(total_c)}<br>
                    🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
