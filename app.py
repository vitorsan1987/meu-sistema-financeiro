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
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; }
    .parcela-tag { background: #8A05BE; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.75em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- SIDEBAR (CARTÕES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            total_card = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum() if not df_compras.empty else 0.0
            st.markdown(f"""
            <div style="background:{r['cor']}; padding:15px; border-radius:10px; margin-bottom:10px; color:white;">
                <div style="display:flex; justify-content:space-between;"><b>{r['nome']}</b> <small>CREDIT</small></div>
                <div style="font-family:monospace; margin:10px 0;">**** **** **** {r['final']}</div>
                <div style="font-size:1.1em; font-weight:bold;">Total: {format_real(total_card)}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    
    with st.expander("➕ Novo Cartão"):
        with st.form("f_cartao", clear_on_submit=True):
            n_nome = st.text_input("Banco")
            n_cor = st.color_picker("Cor", "#8A05BE")
            n_final = st.text_input("4 dígitos", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n_nome, "cor": n_cor, "final": n_final, "venc": "28"}).execute()
                st.rerun()

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]: # COMPRAS
    c1, c2 = st.columns([1, 1.3])
    with c1:
        st.subheader("Registrar Gasto")
        with st.form("f_compra", clear_on_submit=True):
            item = st.text_input("Descrição")
            valor = st.number_input("Valor total da compra", min_value=0.0)
            
            # Mudamos a ordem visual dos inputs para evitar confusão mental ao digitar
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_atual_num = st.number_input("Número da Parcela (Atual)", min_value=1, value=1)
            with col_p2:
                p_total_num = st.number_input("Total de Parcelas", min_value=1, value=1)
            
            cartoes_lista = df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"]
            cartao_sel = st.selectbox("Cartão", cartoes_lista)
            quem = st.multiselect("Dividir com:", LISTA_NOMES)
            
            if st.form_submit_button("🚀 Salvar Gasto"):
                if item and valor > 0 and quem:
                    # Forçamos a ordem correta no momento da gravação no Supabase
                    supabase.table("compras").insert({
                        "nome": item, 
                        "valor_total": valor, 
                        "cartao": cartao_sel,
                        "parcela_atual": int(p_atual_num),
                        "parcelas_total": int(p_total_num),
                        "participes": ",".join(quem), 
                        "valor_por_pessoa": round(valor/len(quem), 2),
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.rerun()

    with c2:
        st.subheader("📋 Histórico")
        if not df_compras.empty:
            df_hist = df_compras.sort_values(by="id", ascending=False)
            for _, r in df_hist.iterrows():
                # --- CORREÇÃO FINAL DA TAG ---
                # Atribuímos a variáveis específicas para garantir a ordem "X de Y"
                num_atual = int(r.get('parcela_atual', 1))
                num_total = int(r.get('parcelas_total', 1))
                
                # Se for parcelado, mostra "6 de 12x"
                tag_final = f"<span class='parcela-tag'>{num_atual} de {num_total}x</span>" if num_total > 1 else ""
                
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span><b>{r['nome']}</b> {tag_final}</span> 
                        <b style="color:#8A05BE;">{format_real(r['valor_total'])}</b>
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
    st.subheader("📊 Resumo Mensal (Apenas a parcela do mês)")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        total_c_mes = 0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = str(r['participes']).split(',')
                if nome in parts:
                    # Cálculo: (Total da Compra / Total de Parcelas) / Qtd Pessoas
                    # Ex: (349 / 6) / 2 = 29,08 por pessoa
                    v_compra = float(r['valor_total'])
                    v_parc_total = int(r['parcelas_total'])
                    valor_da_parcela_mes = (v_compra / v_parc_total) / len(parts)
                    total_c_mes += valor_da_parcela_mes
        
        # Soma das fixas
        total_f = 0
        if not df_fixos.empty:
            total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + \
                      df_fixos[df_fixos['p2_nome'] == nome]['p2_valor'].sum()
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small style="text-transform:uppercase; color:#768390;">{nome}</small><br>
                <b style="font-size:1.6em; color:#adbac7;">{format_real(total_c_mes + total_f)}</b><br>
                <div style="font-size:0.75em; color:#8b949e; margin-top:10px;">
                    Parcelas: {format_real(total_c_mes)}<br>
                    Fixos: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
