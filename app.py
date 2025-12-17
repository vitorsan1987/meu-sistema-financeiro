import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da Página
st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

# Função para formatar em Moeda Brasileira (R$)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Conexão Segura
try:
    # O Streamlit busca automaticamente os dados em [connections.gsheets] nos Secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    conexao_ok = True
except Exception as e:
    st.error("Erro crítico de conexão. Verifique os Secrets.")
    st.exception(e) # Mostra o erro detalhado para depuração
    conexao_ok = False

st.title("💳 Gestão Financeira Cloud - Final")

# --- LANÇAMENTO ---
tipo_gasto = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro_final", clear_on_submit=True):
    c1, c2, c3, c4, c5 = st.columns([2, 1, 0.7, 0.7, 1.5])
    with c1: desc = st.text_input("Descrição da Compra")
    with c2: valor = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3: p_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_total = st.number_input("Total Parc.", min_value=1, value=1)
    with c5: cartao_sel = st.selectbox("Cartão", ["Nubank", "BB", "Itaú", "Inter", "Outro"])

    st.write("**Nomes das Pessoas:**")
    d1, d2 = st.columns(2)
    with d1:
        v_p1_def = "Eu" if tipo_gasto == "100% Minha" else ""
        nome1 = st.text_input("Nome da Pessoa 1", value=v_p1_def)
    with d2:
        bloquear_p2 = (tipo_gasto != "Dividida (50/50)")
        nome2 = st.text_input("Nome da Pessoa 2", disabled=bloquear_p2)

    enviar = st.form_submit_button("✅ Salvar na Planilha Cloud", use_container_width=True)

    if enviar and conexao_ok:
        if not desc or not nome1:
            st.error("Preencha a descrição e o nome!")
        else:
            v_p1 = valor if tipo_gasto != "Dividida (50/50)" else valor / 2
            v_p2 = valor / 2 if tipo_gasto == "Dividida (50/50)" else 0.0
            
            nova_linha = pd.DataFrame([{
                "Descrição": desc, "Valor Total": valor, "Parcela": f"{p_atual}/{p_total}",
                "Cartão": cartao_sel, "P1_Nome": nome1, "P1_Valor": v_p1,
                "P2_Nome": nome2 if nome2 else "-", "P2_Valor": v_p2
            }])

            try:
                # Lê, concatena e atualiza
                df_nuvem = conn.read(ttl=0)
                df_atualizado = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                conn.update(data=df_atualizado)
                st.success("Salvo com sucesso no Google Sheets!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gravar na nuvem: {e}")

# --- EXIBIÇÃO ---
if conexao_ok:
    try:
        dados = conn.read(ttl=0)
        if not dados.empty:
            st.divider()
            st.subheader("📊 Totais Acumulados")
            resumo = {}
            for _, row in dados.iterrows():
                n1, v1 = row['P1_Nome'], float(row['P1_Valor'])
                resumo[n1] = resumo.get(n1, 0) + v1
                if row['P2_Nome'] != "-":
                    n2, v2 = row['P2_Nome'], float(row['P2_Valor'])
                    resumo[n2] = resumo.get(n2, 0) + v2
            
            cols = st.columns(len(resumo))
            for idx, (p, t) in enumerate(resumo.items()):
                cols[idx].metric(p, formatar_real(t))
            
            st.dataframe(dados, use_container_width=True)
    except:
        st.info("Aguardando os primeiros dados da planilha...")
