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
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; }
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
df_fixos = get_data("fixos") 

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
            st.markdown(f'<div style="padding:15px; border-radius:10px; background:{r["cor"]}; margin-bottom:10px;"><b>{r["nome"]}</b><br>FATURA: {format_real(fatura_mes)}</div>', unsafe_allow_html=True)

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas / AP", "📊 Resumo Mensal"])

with tabs[0]: # COMPRAS (Mantido conforme solicitado)
    # ... (Seu código de lançar compras permanece aqui)
    pass

with tabs[1]: # CONTAS FIXAS COM DIVISÃO AUTOMÁTICA
    f1, f2 = st.columns([1, 1.4])
    with f1:
        st.subheader("🏠 Lançar Gastos Fixos")
        with st.form("f_fixo", clear_on_submit=True):
            it = st.selectbox("Serviço", ["Parcela Financiamento AP", "Amortização", "Condomínio", "Luz", "Internet", "Outros"], index=None, placeholder="Selecione o serviço...")
            v_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", value=None)
            
            st.write("Quem divide esta conta?")
            p1_n = st.selectbox("Pessoa 1", LISTA_NOMES)
            p2_n = st.selectbox("Pessoa 2 (Opcional)", ["Ninguém"] + LISTA_NOMES)
            
            if st.form_submit_button("💾 Salvar e Dividir"):
                if it and v_total:
                    # Lógica de Divisão Automática
                    p2_final = p2_n if p2_n != "Ninguém" else None
                    
                    if p2_final:
                        v_p1 = v_total / 2
                        v_p2 = v_total / 2
                    else:
                        v_p1 = v_total
                        v_p2 = 0.0
                    
                    supabase.table("fixos").insert({
                        "item": it, 
                        "valor": v_total, 
                        "p1_nome": p1_n, 
                        "p1_valor": v_p1, 
                        "p2_nome": p2_final, 
                        "p2_valor": v_p2
                    }).execute()
                    st.success("Conta dividida e salva!")
                    st.rerun()
                else:
                    st.warning("Preencha o serviço e o valor total.")

    with f2:
        st.subheader("📋 Histórico de Fixas")
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{r['item']}</b>
                        <b>{format_real(r['valor'])}</b>
                    </div>
                    <div style="font-size:0.8em; color:#8b949e; margin-top:5px;">
                        {r['p1_nome']}: {format_real(r['p1_valor'])} 
                        {f"| {r['p2_nome']}: {format_real(r['p2_valor'])}" if r['p2_nome'] else ""}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_f_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]: # RESUMO MENSAL UNIFICADO
    st.subheader(f"📊 Resumo Geral - {mes_sel}")
    r_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Soma Cartões
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    div_r = int(r['parcelas_total']) if int(r['parcelas_total']) > 0 else 1
                    total_c += (float(r['valor_total']) / div_r) / len(parts)
        
        # Soma Fixas (Usa os valores automáticos salvos no banco)
        total_f = 0.0
        if not df_fixos.empty:
            total_f += float(df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum())
            total_f += float(df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum())
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome}</small><br><b style="font-size:1.7em;">{format_real(total_c + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:10px; border-top:1px solid #333; padding-top:8px;">
                    🛒 Cartão: {format_real(total_c)}<br>🏠 Fixas/AP: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
