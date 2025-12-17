import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

# Configuração da Página
st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

# Função para formatar em Moeda Brasileira (R$)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Tenta conectar ao Google Sheets, se falhar, avisa o usuário
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    pode_conectar = True
except Exception:
    pode_conectar = False

st.title("💳 Gestão Financeira Cloud - Final")

# --- LANÇAMENTO ---
tipo_gasto = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro_final", clear_on_submit=True):
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: desc = st.text_input("Descrição da Compra")
    with c2: valor = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3: p_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_total = st.number_input("Total Parc.", min_value=1, value=1)

    st.write("**Nomes das Pessoas:**")
    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        v_p1 = "Eu" if tipo_gasto == "100% Minha" else ""
        nome1 = st.text_input("Pessoa 1", value=v_p1)
    with d2:
        bloquear_p2 = (tipo_gasto != "Dividida (50/50)")
        nome2 = st.text_input("Pessoa 2", disabled=bloquear_p2)
    with d3:
        cartao = st.text_input("Cartão", value="Nubank")

    enviar = st.form_submit_button("✅ Salvar Dados", use_container_width=True)

    if enviar:
        if not desc or not nome1:
            st.error("Preencha a descrição e o nome!")
        else:
            v_p1 = valor if tipo_gasto != "Dividida (50/50)" else valor / 2
            v_p2 = valor / 2 if tipo_gasto == "Dividida (50/50)" else 0.0
            
            nova_linha = pd.DataFrame([{
                "Descrição": desc, "Valor Total": valor, "Parcela": f"{p_atual}/{p_total}",
                "Cartão": cartao, "P1_Nome": nome1, "P1_Valor": v_p1,
                "P2_Nome": nome2 if nome2 else "-", "P2_Valor": v_p2
            }])

            if pode_conectar:
                try:
                    df_nuvem = conn.read(ttl=0)
                    df_atualizado = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                    conn.update(data=df_atualizado)
                    st.success("Salvo no Google Sheets!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na nuvem: Verifique o formato da Private Key nos Secrets.")
            else:
                st.warning("Conexão Cloud não configurada. Use o botão 'Baixar CSV' abaixo para não perder dados.")

# --- EXIBIÇÃO ---
try:
    if pode_conectar:
        dados = conn.read(ttl=0)
        if not dados.empty:
            st.divider()
            st.subheader("📊 Totais Acumulados")
            resumo = {}
            for _, row in dados.iterrows():
                n1, n2 = row['P1_Nome'], row['P2_Nome']
                resumo[n1] = resumo.get(n1, 0) + float(row['P1_Valor'])
                if n2 != "-": resumo[n2] = resumo.get(n2, 0) + float(row['P2_Valor'])
            
            cols = st.columns(len(resumo))
            for idx, (p, t) in enumerate(resumo.items()):
                cols[idx].metric(p, formatar_real(t))
            
            st.dataframe(dados, use_container_width=True)
except:
    st.info("Aguardando dados...")
