import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Conexão direta (os segredos devem estar perfeitos nos Secrets do Cloud)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    conexao_ok = True
except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    conexao_ok = False

st.title("💳 Gestão Financeira Cloud")

tipo_divisao = st.radio("Modalidade:", ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"], horizontal=True)

with st.form("form_sync", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: desc = st.text_input("Descrição")
    with c2: valor = st.number_input("Valor", min_value=0.0, step=0.01)
    with c3: p_at = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_tot = st.number_input("Total", min_value=1, value=1)
    
    d1, d2, d3 = st.columns([1, 1, 1])
    with d1: nome1 = st.text_input("Pessoa 1", value="Eu" if tipo_divisao == "100% Minha" else "")
    with d2: nome2 = st.text_input("Pessoa 2", disabled=(tipo_divisao != "Dividida (50/50)"))
    with d3: cartao = st.selectbox("Cartão", ["Nubank", "BB", "Itaú", "Inter"])

    if st.form_submit_button("✅ Salvar na Planilha") and conexao_ok:
        v1 = valor if tipo_divisao != "Dividida (50/50)" else valor / 2
        v2 = valor / 2 if tipo_divisao == "Dividida (50/50)" else 0.0
        
        nova_linha = pd.DataFrame([{
            "Descrição": desc, "Valor Total": valor, "Parcela": f"{p_at}/{p_tot}",
            "Cartão": cartao, "P1_Nome": nome1, "P1_Valor": v1,
            "P2_Nome": nome2 if nome2 else "-", "P2_Valor": v2
        }])

        try:
            df_atual = conn.read(ttl=0)
            df_final = pd.concat([df_atual, nova_linha], ignore_index=True)
            conn.update(data=df_final)
            st.success("Salvo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao gravar: {e}")

# Exibição
if conexao_ok:
    try:
        dados = conn.read(ttl=0)
        if not dados.empty:
            st.divider()
            st.subheader("📊 Resumo")
            st.dataframe(dados, use_container_width=True)
    except:
        st.info("Planilha vazia ou aguardando dados...")
