import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da Página
st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

# 2. Função de Formatação e Limpeza da Chave
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

def preparar_conexao():
    try:
        # Corrige o erro de "Incorrect padding" tratando os caracteres de escape \n
        if "connections" in st.secrets and "gsheets" in st.secrets.connections:
            # Substitui a representação de texto '\\n' pela quebra de linha real '\n'
            st.secrets.connections.gsheets.private_key = st.secrets.connections.gsheets.private_key.replace("\\n", "\n")
        
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"Erro na configuração dos Secrets: {e}")
        return None

# Inicializa conexão
conn = preparar_conexao()

st.title("💳 Gestão Financeira - Sync Google Sheets")

# --- FORMULÁRIO DE LANÇAMENTO ---
st.subheader("📝 Registrar Gasto")

tipo_divisao = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro_final", clear_on_submit=True):
    # Linha 1: Dados Principais
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: desc = st.text_input("Descrição da Compra")
    with c2: valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3: p_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_total = st.number_input("Total Parc.", min_value=1, value=1)

    # Linha 2: Nomes e Cartão
    st.write("**Identificação das Pessoas:**")
    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        v_def_p1 = "Eu" if tipo_divisao == "100% Minha" else ""
        nome_p1 = st.text_input("Pessoa 1", value=v_def_p1)
    with d2:
        bloqueado_p2 = (tipo_divisao != "Dividida (50/50)")
        nome_p2 = st.text_input("Pessoa 2", disabled=bloqueado_p2, placeholder="Obrigatório para divisão")
    with d3:
        cartao_lista = ["Nubank", "BB", "Itaú", "Inter", "Outro"]
        cartao_sel = st.selectbox("Cartão Usado", cartao_lista)

    # Botão de Envio
    enviar = st.form_submit_button("✅ Salvar na Planilha Cloud", use_container_width=True)

    if enviar and conn:
        if not desc or not nome_p1:
            st.error("Preencha a descrição e o nome da Pessoa 1!")
        else:
            # Lógica de cálculo (50/50 ou integral)
            v1 = valor_total if tipo_divisao != "Dividida (50/50)" else valor_total / 2
            v2 = valor_total / 2 if tipo_divisao == "Dividida (50/50)" else 0.0
            
            # Criar nova linha para a planilha
            nova_linha = pd.DataFrame([{
                "Descrição": desc,
                "Valor Total": valor_total,
                "Parcela": f"{p_atual}/{p_total}",
                "Cartão": cartao_sel,
                "P1_Nome": nome_p1,
                "P1_Valor": v1,
                "P2_Nome": nome_p2 if nome_p2 else "-",
                "P2_Valor": v2
            }])

            try:
                # Processo de atualização: Lê -> Concatena -> Envia
                df_nuvem = conn.read(ttl=0)
                df_final = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                conn.update(data=df_final)
                st.success("Dados salvos com sucesso no Google Sheets!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gravar na nuvem: {e}")

# --- VISUALIZAÇÃO DOS DADOS ---
if conn:
    try:
        # Busca dados atualizados da planilha
        dados = conn.read(ttl=0)
        
        if not dados.empty:
            st.divider()
            st.subheader("📊 Totais Acumulados")
            
            # Cálculo de totais por pessoa de forma dinâmica
            resumo = {}
            for _, linha in dados.iterrows():
                # Pessoa 1
                n1, v1 = linha['P1_Nome'], float(linha['P1_Valor'])
                resumo[n1] = resumo.get(n1, 0) + v1
                # Pessoa 2 (se não for nulo)
                if linha['P2_Nome'] != "-":
                    n2, v2 = linha['P2_Nome'], float(linha['P2_Valor'])
                    resumo[n2] = resumo.get(n2, 0) + v2
            
            # Exibe os totais em colunas (Metrics)
            col_m = st.columns(len(resumo))
            for idx, (nome, total) in enumerate(resumo.items()):
                col_m[idx].metric(nome, formatar_real(total))
            
            st.write("### 📋 Histórico na Planilha")
            st.dataframe(dados, use_container_width=True)
    except Exception:
        st.info("Aguardando o primeiro registro para exibir o histórico.")
