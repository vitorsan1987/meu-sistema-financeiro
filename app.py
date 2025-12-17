import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Finanças Sync", layout="wide")

# Conectando à planilha (configurada nos Secrets do Streamlit Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

st.title("💳 Gestão Financeira - Sync Google Sheets")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    if 'cartoes' not in st.session_state: st.session_state.cartoes = ["Nubank", "BB"]
    
    with st.expander("➕ Gerenciar Cartões"):
        novo_c = st.text_input("Nome do Cartão")
        if st.button("Salvar"):
            st.session_state.cartoes.append(novo_c)
            st.rerun()

# --- FORMULÁRIO ---
tipo_gasto = st.radio("Modalidade:", ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"], horizontal=True)

with st.form("form_sync", clear_on_submit=True):
    c1, c2, c3, c4, c5 = st.columns([2, 1, 0.7, 0.7, 1.5])
    with c1: desc = st.text_input("Descrição")
    with c2: valor = st.number_input("Valor Total", min_value=0.0, step=0.01)
    with c3: p_atual = st.number_input("Nº", min_value=1, value=1)
    with c4: p_total = st.number_input("Total", min_value=1, value=1)
    with c5: cartao_sel = st.selectbox("Cartão", st.session_state.cartoes)

    d1, d2 = st.columns(2)
    with d1: nome1 = st.text_input("Pessoa 1", value="Eu" if tipo_gasto == "100% Minha" else "")
    with d2: nome2 = st.text_input("Pessoa 2", disabled=(tipo_gasto != "Dividida (50/50)"))

    if st.form_submit_button("✅ Salvar na Nuvem"):
        # Lógica de valores
        v1 = valor if tipo_gasto != "Dividida (50/50)" else valor / 2
        v2 = valor / 2 if tipo_gasto == "Dividida (50/50)" else 0.0
        n2_final = nome2 if tipo_gasto == "Dividida (50/50)" else "-"

        # Preparando a nova linha
        nova_linha = pd.DataFrame([{
            "Descrição": desc, "Valor Total": valor, "Parcela": f"{p_atual}/{p_total}",
            "Cartão": cartao_sel, "P1_Nome": nome1, "P1_Valor": v1,
            "P2_Nome": n2_final, "P2_Valor": v2
        }])

        # Lendo dados atuais e adicionando a nova linha
        try:
            df_atual = conn.read(ttl=0)
            df_novo = pd.concat([df_atual, nova_linha], ignore_index=True)
            conn.update(data=df_novo)
            st.success("Salvo com sucesso no Google Sheets!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- VISUALIZAÇÃO DOS DADOS SALVOS ---
st.divider()
try:
    dados_nuvem = conn.read(ttl=0)
    if not dados_nuvem.empty:
        st.subheader("📊 Histórico Salvo na Planilha")
        st.dataframe(dados_nuvem, use_container_width=True)
        
        # Totais rápidos
        totais = {}
        for _, r in dados_nuvem.iterrows():
            totais[r['P1_Nome']] = totais.get(r['P1_Nome'], 0) + float(r['P1_Valor'])
            if r['P2_Nome'] != "-":
                totais[r['P2_Nome']] = totais.get(r['P2_Nome'], 0) + float(r['P2_Valor'])
        
        c_tot = st.columns(len(totais))
        for idx, (n, v) in enumerate(totais.items()):
            c_tot[idx].metric(f"Total {n}", formatar_real(v))
except:
    st.info("Aguardando o primeiro registro na planilha...")
