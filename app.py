import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# No Streamlit Cloud, você configurará a URL nas 'Secrets'
conn = st.connection("gsheets", type=GSheetsConnection)

# Lista de Nomes Padronizada
NOMES_DISPONIVEIS = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- ESTILO CSS (Mantendo o seu visual) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .historico-container { background: #161b22; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 15px; }
    .card-resumo-neutro { background: #1c2128; padding: 25px; border-radius: 15px; border: 1px solid #444c56; margin-bottom: 20px; }
    .text-roxo { color: #8A05BE !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
def get_data(worksheet):
    return conn.read(worksheet=worksheet, ttl="0s")

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Cartões Cloud</h2>", unsafe_allow_html=True)
    df_cartoes = get_data("cartoes")
    df_compras = get_data("compras")
    
    # Exibição dos cartões (Visual simplificado para Cloud)
    for _, r in df_cartoes.iterrows():
        gasto = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum()
        st.info(f"**{r['nome']}** (Final {r['final']})\n\nGasto Total: {format_real(gasto)}")

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo"])

with tabs[0]:
    col_f, col_h = st.columns([1, 1.3])
    with col_f:
        with st.form("nova_compra", clear_on_submit=True):
            nome = st.text_input("Descrição")
            valor = st.number_input("Valor Total", min_value=0.0, step=0.01)
            cartao = st.selectbox("Cartão", df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"])
            quem = st.multiselect("Dividir com:", NOMES_DISPONIVEIS)
            
            if st.form_submit_button("🚀 Registrar na Nuvem"):
                if nome and valor > 0 and quem:
                    nova_linha = pd.DataFrame([{
                        "id": len(df_compras) + 1,
                        "nome": nome,
                        "valor_total": valor,
                        "cartao": cartao,
                        "parcelas": 1,
                        "parcela_atual": 1,
                        "participes": ",".join(quem),
                        "valor_por_pessoa": round(valor / len(quem), 2),
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }])
                    df_atualizado = pd.concat([df_compras, nova_linha], ignore_index=True)
                    conn.update(worksheet="compras", data=df_atualizado)
                    st.success("Salvo no Google Sheets!")
                    st.rerun()

    with col_h:
        st.subheader("📋 Histórico Online")
        if not df_compras.empty:
            for _, r in df_compras.iloc[::-1].iterrows():
                st.markdown(f"""
                <div class="historico-container">
                    <b>{r['nome']}</b> - <span class="text-roxo">{format_real(r['valor_total'])}</span><br>
                    <small>{r['participes']} | {r['cartao']}</small>
                </div>
                """, unsafe_allow_html=True)

with tabs[2]:
    st.subheader("📊 Resumo Consolidado")
    df_fixos = get_data("fixos")
    cols = st.columns(len(NOMES_DISPONIVEIS))
    for idx, n in enumerate(NOMES_DISPONIVEIS):
        # Soma compras
        v_c = sum([row['valor_por_pessoa'] for _, row in df_compras.iterrows() if n in str(row['participes']).split(',')])
        # Soma fixos
        v_f = df_fixos[df_fixos['p1_nome'] == n]['p1_valor'].sum() + df_fixos[df_fixos['p2_nome'] == n]['p2_valor'].sum()
        
        with cols[idx]:
            st.markdown(f"""
            <div class="card-resumo-neutro">
                <h4>{n}</h4>
                <div style="font-size:1.5em; color:#8A05BE;">{format_real(v_c + v_f)}</div>
            </div>
            """, unsafe_allow_html=True)
