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
    
    .cartao-container { 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        color: white; 
        min-height: 150px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); 
    }
    
    .historico-container { 
        background: #1c2128; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #30363d; 
        margin-bottom: 12px; 
    }
    
    .card-resumo { 
        background: #1c2128; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #444c56; 
        margin-bottom: 15px; 
        min-height: 150px; 
    }
    
    .parcela-tag { 
        background: #30363d; 
        color: #adbac7; 
        padding: 2px 8px; 
        border-radius: 4px; 
        font-size: 0.7em; 
        font-weight: bold; 
        border: 1px solid #444c56;
    }
    
    .chip { 
        display: inline-block; 
        padding: 2px 10px; 
        border-radius: 12px; 
        background-color: #21262d; 
        color: #8b949e; 
        font-size: 0.8em; 
        margin-right: 4px; 
        border: 1px solid #30363d; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- FILTRO DE MÊS GLOBAL ---
col_m1, col_m2 = st.columns([1, 4])
with col_m1:
    mes_selecionado = st.selectbox("📅 Mês", MESES, index=datetime.now().month - 1)
with col_m2:
    ano_selecionado = st.number_input("Ano", min_value=2024, max_value=2030, value=datetime.now().year)

mes_idx = str(MESES.index(mes_selecionado) + 1).zfill(2)
filtro_data = f"/{mes_idx}/{ano_selecionado}"

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras_raw = get_data("compras")
df_fixos = get_data("fixos")

# Criar dicionário de cores dos cartões para o histórico
cores_cartoes = dict(zip(df_cartoes['nome'], df_cartoes['cor'])) if not df_cartoes.empty else {}

if not df_compras_raw.empty:
    df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)]
else:
    df_compras = pd.DataFrame()

# --- BARRA LATERAL (CARTÕES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            fatura_mes = 0.0
            if not df_compras.empty:
                compras_cartao = df_compras[df_compras['cartao'] == r['nome']]
                for _, compra in compras_cartao.iterrows():
                    fatura_mes += (float(compra['valor_total']) / int(compra['parcelas_total']))

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
    
    with st.expander("➕ Novo Cartão"):
        with st.form("form_cartao", clear_on_submit=True):
            n_nome = st.text_input("Banco")
            n_cor = st.color_picker("Cor do Cartão", "#8A05BE")
            n_final = st.text_input("4 dígitos finais", max_chars=4)
            if st.form_submit_button("Salvar Cartão"):
                if n_nome and n_final:
                    supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final, "venc": "28"}).execute()
                    st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]: 
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            item = st.text_input("Descrição do Gasto")
            
            col_v1, col_v2 = st.columns([1.5, 1])
            with col_v1:
                valor_digitado = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col_v2:
                tipo_valor = st.selectbox("Tipo de Entrada", ["Parcela Mensal", "Valor Total"])
            
            cp1, cp2 = st.columns(2)
            with cp1: p_atual_in = st.number_input("Parc. Atual", min_value=1, value=1)
            with cp2: p_total_in = st.number_input("Total Parc.", min_value=1, value=1)
            
            cartao_sel = st.selectbox("Cartão Utilizado", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com", LISTA_NOMES)
            
            if st.form_submit_button("🚀 Salvar Gasto"):
                if item and valor_digitado > 0 and quem:
                    v_total_calc = valor_digitado * p_total_in if tipo_valor == "Parcela Mensal" else valor_digitado
                    data_salvar = datetime.now().strftime(f"%d/{mes_idx}/{ano_selecionado}")
                    supabase.table("compras").insert({
                        "nome": item, "valor_total": v_total_calc, "cartao": cartao_sel,
                        "parcela_atual": int(p_atual_in), "parcelas_total": int(p_total_in),
                        "participes": ",".join(quem), "data": data_salvar
                    }).execute()
                    st.rerun()
                    
    with c2:
        st.subheader(f"📋 Histórico ({mes_selecionado})")
        if not df_compras.empty:
            for _, r in df_compras.sort_values(by="id", ascending=False).iterrows():
                v_mensal = float(r['valor_total']) / int(r['parcelas_total'])
                cor_valor = cores_cartoes.get(r['cartao'], "#ffffff")
                chips = "".join([f'<span class="chip">{p.strip()}</span>' for p in str(r['participes']).split(',')])
                
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <span style="font-size:1.1em; font-weight:bold;">{r['nome']}</span>
                            <span class='parcela-tag'>{int(r['parcela_atual'])} / {int(r['parcelas_total'])}x</span>
                            <div style="margin-top:6px;">{chips}</div>
                        </div>
                        <div style="text-align:right;">
                            <b style="color:{cor_valor}; font-size:1.2em;">{format_real(v_mensal)}</b>
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
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c_mes = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    total_c_mes += (float(r['valor_total']) / int(r['parcelas_total'])) / len(parts)
        
        total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + \
                  df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum() if not df_fixos.empty else 0.0
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small style="text-transform:uppercase; color:#768390; letter-spacing:1px;">{nome}</small><br>
                <b style="font-size:1.6em; color:#adbac7;">{format_real(total_c_mes + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:10px; border-top:1px solid #333; padding-top:8px;">
                    🛒 Variável: {format_real(total_c_mes)}<br>
                    🏠 Fixas: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
