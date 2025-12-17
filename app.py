import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da Página
st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

# Função para formatar valores em Moeda Brasileira (R$)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# Inicialização da Conexão Segura
# O Streamlit busca automaticamente as configurações em [connections.gsheets] nos Secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    conexao_ok = True
except Exception as e:
    st.error("Erro de Autenticação: Verifique a 'private_key' nos Secrets.")
    st.info("Dica: Certifique-se de usar o formato de linha única com '\\n' nos Secrets.")
    conexao_ok = False

st.title("💳 Gestão Financeira Cloud - Final")

# --- INTERFACE DE LANÇAMENTO ---
tipo_divisao = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro_final", clear_on_submit=True):
    # Campos de Entrada
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: desc = st.text_input("Descrição da Compra")
    with c2: valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3: p_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: p_total = st.number_input("Total Parc.", min_value=1, value=1)

    st.write("**Identificação das Pessoas:**")
    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        v_def_p1 = "Eu" if tipo_divisao == "100% Minha" else ""
        nome_p1 = st.text_input("Pessoa 1", value=v_def_p1)
    with d2:
        bloqueado_p2 = (tipo_divisao != "Dividida (50/50)")
        nome_p2 = st.text_input("Pessoa 2", disabled=bloqueado_p2, placeholder="Obrigatório para divisão")
    with d3:
        cartao_sel = st.selectbox("Cartão Usado", ["Nubank", "BB", "Itaú", "Inter", "Outro"])

    # Botão de Envio
    enviar = st.form_submit_button("✅ Salvar na Planilha Cloud", use_container_width=True)

    if enviar and conexao_ok:
        if not desc or not nome_p1:
            st.error("Por favor, preencha a descrição e o nome da Pessoa 1.")
        else:
            # Lógica de partilha de valores
            val_p1 = valor_total if tipo_divisao != "Dividida (50/50)" else valor_total / 2
            val_p2 = valor_total / 2 if tipo_divisao == "Dividida (50/50)" else 0.0
            
            # Criar nova linha compatível com os cabeçalhos da imagem 1
            nova_linha = pd.DataFrame([{
                "Descrição": desc,
                "Valor Total": valor_total,
                "Parcela": f"{p_atual}/{p_total}",
                "Cartão": cartao_sel,
                "P1_Nome": nome_p1,
                "P1_Valor": val_p1,
                "P2_Nome": nome_p2 if nome_p2 else "-",
                "P2_Valor": val_p2
            }])

            try:
                # Atualização: Lê -> Concatena -> Envia
                df_nuvem = conn.read(ttl=0)
                df_final = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                conn.update(data=df_final)
                st.success("Dados registrados com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gravar na nuvem: {e}")

# --- VISUALIZAÇÃO DOS DADOS ---
if conexao_ok:
    try:
        dados_salvos = conn.read(ttl=0)
        if not dados_salvos.empty:
            st.divider()
            st.subheader("📊 Resumo e Histórico")
            
            # Cálculo de totais por pessoa
            resumo = {}
            for _, linha in dados_salvos.iterrows():
                n1, v1 = linha['P1_Nome'], float(linha['P1_Valor'])
                resumo[n1] = resumo.get(n1, 0) + v1
                if linha['P2_Nome'] != "-":
                    n2, v2 = linha['P2_Nome'], float(linha['P2_Valor'])
                    resumo[n2] = resumo.get(n2, 0) + v2
            
            col_m = st.columns(len(resumo))
            for idx, (nome, total) in enumerate(resumo.items()):
                col_m[idx].metric(nome, formatar_real(total))
            
            st.dataframe(dados_salvos, use_container_width=True)
    except:
        st.info("Planilha pronta para receber dados.")
