import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Finanças Pro Cloud", layout="wide")

# Formatação de Moeda
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Conexão com tratamento de erro para a chave
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    dados_existentes = conn.read(ttl=0)
    conexao_ok = True
except Exception as e:
    st.error(f"Erro de Conexão: Verifique se a 'private_key' nos Secrets está correta.")
    st.info("Dica: A chave deve conter os caracteres '\\n' para indicar quebras de linha.")
    conexao_ok = False

st.title("💳 Gestão Financeira Cloud - Final")

# --- LANÇAMENTO ---
tipo_gasto = st.radio("Como deseja dividir?", ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"], horizontal=True)

with st.form("form_final", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: desc = st.text_input("Descrição")
    with c2: valor = st.number_input("Valor Total", min_value=0.0, step=0.01)
    with c3: p_at = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_tot = st.number_input("Total", min_value=1, value=1)

    d1, d2, d3 = st.columns([1, 1, 1])
    with d1: nome1 = st.text_input("Pessoa 1", value="Eu" if tipo_gasto == "100% Minha" else "")
    with d2: nome2 = st.text_input("Pessoa 2", disabled=(tipo_gasto != "Dividida (50/50)"))
    with d3: cartao = st.selectbox("Cartão", ["Nubank", "BB", "Itaú", "Outro"])

    if st.form_submit_button("✅ Salvar na Planilha Cloud") and conexao_ok:
        v1 = valor if tipo_gasto != "Dividida (50/50)" else valor / 2
        v2 = valor / 2 if tipo_gasto == "Dividida (50/50)" else 0.0
        
        nova_linha = pd.DataFrame([{
            "Descrição": desc, "Valor Total": valor, "Parcela": f"{p_at}/{p_tot}",
            "Cartão": cartao, "P1_Nome": nome1, "P1_Valor": v1,
            "P2_Nome": nome2 if nome2 else "-", "P2_Valor": v2
        }])

        try:
            df_atualizado = pd.concat([dados_existentes, nova_linha], ignore_index=True)
            conn.update(data=df_atualizado)
            st.success("Salvo com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao gravar: {e}")

# --- VISUALIZAÇÃO ---
if conexao_ok and not dados_existentes.empty:
    st.divider()
    st.subheader("📊 Totais Acumulados")
    resumo = {}
    for _, row in dados_existentes.iterrows():
        n1, v1 = row['P1_Nome'], float(row['P1_Valor'])
        resumo[n1] = resumo.get(n1, 0) + v1
        if row['P2_Nome'] != "-":
            n2, v2 = row['P2_Nome'], float(row['P2_Valor'])
            resumo[n2] = resumo.get(n2, 0) + v2
    
    cols = st.columns(len(resumo))
    for idx, (nome, total) in enumerate(resumo.items()):
        cols[idx].metric(nome, formatar_real(total))
    
    st.dataframe(dados_existentes, use_container_width=True)
