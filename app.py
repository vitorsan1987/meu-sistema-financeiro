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

# Lista de nomes para divisão
LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- FUNÇÕES DE SUPORTE ---
def get_data(tabela):
    try:
        res = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS (LAYOUT MELHORADO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    
    /* Layout do Cartão na Sidebar */
    .cartao-container { 
        background: #8A05BE; 
        padding: 20px; 
        border-radius: 15px; 
        margin-bottom: 15px; 
        color: white; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        min-height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* Containers do Histórico e Resumo */
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; min-height: 150px; }
    .parcela-tag { background: #8A05BE; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: bold; }
    
    /* Preview de Confirmação */
    .info-preview { background: #21262d; padding: 10px; border-radius: 5px; border-left: 5px solid #00ff00; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- BARRA LATERAL (CARTÕES GRANDES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            total_card = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum() if not df_compras.empty else 0.0
            st.markdown(f"""
            <div class="cartao-container" style="background:{r['cor']};">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:1.2em;">{r['nome']}</b>
                    <small style="opacity:0.8;">CREDIT</small>
                </div>
                <div style="font-family:monospace; font-size:1.1em; margin: 15px 0;">**** **** **** {r['final']}</div>
                <div>
                    <small style="opacity:0.8; font-size:0.7em;">TOTAL OCUPADO</small><br>
                    <b style="font-size:1.2em;">{format_real(total_card)}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    
    with st.expander("➕ Novo Cartão"):
        with st.form("form_cartao", clear_on_submit=True):
            n_nome = st.text_input("Nome do Banco")
            n_cor = st.color_picker("Cor do Cartão", "#8A05BE")
            n_final = st.text_input("4 últimos dígitos", max_chars=4)
            if st.form_submit_button("Salvar"):
                if n_nome and n_final:
                    supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final, "venc": "28"}).execute()
                    st.rerun()

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

# --- ABA DE COMPRAS ---
with tabs[0]:
    col1, col2 = st.columns([1, 1.3])
    with col1:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            item = st.text_input("Descrição (Ex: Empréstimo)")
            
            tipo_valor = st.radio("Como deseja inserir o valor?", ["Valor da Parcela (Mensal)", "Valor Total da Compra"])
            valor_digitado = st.number_input("Valor", min_value=0.0, format="%.2f")
            
            cp1, cp2 = st.columns(2)
            with cp1:
                p_atual_in = st.number_input("Parcela Atual", min_value=1, value=1)
            with cp2:
                p_total_in = st.number_input("Total de Parcelas", min_value=1, value=1)
            
            # Lógica de Cálculo para Preview
            if tipo_valor == "Valor da Parcela (Mensal)":
                valor_total_calc = valor_digitado * p_total_in
                parcela_mensal_total = valor_digitado
            else:
                valor_total_calc = valor_digitado
                parcela_mensal_total = valor_digitado / p_total_in if p_total_in > 0 else 0

            lista_c = df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"]
            cartao_sel = st.selectbox("Cartão", lista_c)
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            
            if valor_digitado > 0 and quem:
                cada_um = parcela_mensal_total / len(quem)
                st.markdown(f"""
                <div class="info-preview">
                    <b>Confirmação do Resumo:</b><br>
                    Parcela Mensal Total: {format_real(parcela_mensal_total)}<br>
                    Cada pessoa pagará: <b>{format_real(cada_um)}</b>
                </div>
                """, unsafe_allow_html=True)

            if st.form_submit_button("🚀 Salvar Gasto"):
                if item and valor_digitado > 0 and quem:
                    supabase.table("compras").insert({
                        "nome": item, 
                        "valor_total": valor_total_calc, 
                        "cartao": cartao_sel,
                        "parcela_atual": int(p_atual_in),
                        "parcelas_total": int(p_total_in),
                        "participes": ",".join(quem), 
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()

    with col2:
        st.subheader("📋 Histórico")
        if not df_compras.empty:
            df_hist = df_compras.sort_values(by="id", ascending=False)
            for _, r in df_hist.iterrows():
                # Lógica para mostrar valor da parcela no histórico
                v_total = float(r['valor_total'])
                p_total = int(r['parcelas_total'])
                valor_parcela_historico = v_total / p_total if p_total > 0 else v_total
                
                # Trava visual para parcela (menor de maior)
                v_a = int(r.get('parcela_atual', 1))
                p_atual_tag = min(v_a, p_total)
                
                tag_parc = f"<span class='parcela-tag'>{p_atual_tag} de {p_total}x</span>" if p_total > 1 else ""
                
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><b>{r['nome']}</b> {tag_parc}</span> 
                        <b style="color:#8A05BE;">{format_real(valor_parcela_historico)}</b>
                    </div>
                    <div style="font-size:0.85em; color:#8b949e; margin-top:5px;">
                        {r['data']} | {r['cartao']} | {str(r['participes']).replace(',', ', ')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Apagar", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

# --- ABA DE RESUMO MENSAL ---
with tabs[2]:
    st.subheader("📊 Resumo Mensal (Parcelas do Mês)")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c_mes = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    v_total = float(r['valor_total'])
                    v_parc_t = int(r.get('parcelas_total', 1))
                    total_c_mes += (v_total / v_parc_t) / len(parts)
        
        total_f = 0.0
        if not df_fixos.empty:
            total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + \
                      df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small style="text-transform:uppercase; color:#768390;">{nome}</small><br>
                <b style="font-size:1.6em; color:#adbac7;">{format_real(total_c_mes + total_f)}</b><br>
                <div style="font-size:0.85em; color:#8b949e; margin-top:10px; border-top:1px solid #333; padding-top:5px;">
                    Compras (Parc.): {format_real(total_c_mes)}<br>
                    Fixos: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
