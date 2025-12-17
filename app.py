import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuração da Página
st.set_page_config(page_title="Finanças Pro Cloud", layout="wide")

# Função para formatar valores em Real (BRL)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

# 2. Inicialização da Conexão Segura
# O Streamlit buscará as credenciais em [connections.gsheets] nos Secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Tenta ler a planilha para validar se a chave está correta
    dados_atuais = conn.read(ttl=0)
    conexao_ok = True
except Exception as e:
    st.error("Erro de Autenticação: Verifique a 'private_key' nos Secrets do Streamlit Cloud.")
    st.info("Dica: Use aspas triplas ( \"\"\" ) para envolver a chave nos Secrets.")
    conexao_ok = False

st.title("💳 Gestão Financeira Cloud - Versão Final")

# --- INTERFACE DE LANÇAMENTO ---
st.subheader("📝 Registrar Gasto")
tipo_divisao = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro", clear_on_submit=True):
    # Linha 1: Dados da Compra
    c1, c2, c3, c4 = st.columns([2, 1, 0.7, 0.7])
    with c1: 
        desc = st.text_input("Descrição da Compra (ex: Mercado)")
    with c2: 
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3: 
        parc_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4: 
        parc_total = st.number_input("Total Parc.", min_value=1, value=1)

    # Linha 2: Responsáveis e Cartão
    st.write("**Identificação:**")
    d1, d2, d3 = st.columns([1, 1, 1])
    with d1:
        v_def_p1 = "Eu" if tipo_divisao == "100% Minha" else ""
        nome_p1 = st.text_input("Pessoa 1", value=v_def_p1)
    with d2:
        bloqueado_p2 = (tipo_divisao != "Dividida (50/50)")
        nome_p2 = st.text_input("Pessoa 2", disabled=bloqueado_p2, placeholder="Nome do parceiro")
    with d3:
        cartao_nome = st.selectbox("Cartão Usado", ["Nubank", "BB", "Itaú", "Inter", "Outro"])

    # Botão de Envio
    enviar = st.form_submit_button("✅ Salvar na Nuvem", use_container_width=True)

    if enviar and conexao_ok:
        if not desc or not nome_p1:
            st.error("Por favor, preencha a descrição e o nome da Pessoa 1.")
        else:
            # Lógica de partilha (50/50 ou integral)
            val_p1 = valor_total if tipo_divisao != "Dividida (50/50)" else valor_total / 2
            val_p2 = valor_total / 2 if tipo_divisao == "Dividida (50/50)" else 0.0
            
            # Criar nova linha para a planilha
            nova_linha = pd.DataFrame([{
                "Descrição": desc,
                "Valor Total": valor_total,
                "Parcela": f"{parc_atual}/{parc_total}",
                "Cartão": cartao_nome,
                "P1_Nome": nome_p1,
                "P1_Valor": val_p1,
                "P2_Nome": nome_p2 if nome_p2 else "-",
                "P2_Valor": val_p2
            }])

            try:
                # Lê o que já existe, junta com o novo e atualiza a nuvem
                df_nuvem = conn.read(ttl=0)
                df_final = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                conn.update(data=df_final)
                st.success("Dados salvos com sucesso no Google Sheets!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gravar dados: {e}")

# --- VISUALIZAÇÃO DOS DADOS ---
if conexao_ok:
    try:
        # Busca dados atualizados
        dados_salvos = conn.read(ttl=0)
        
        if not dados_salvos.empty:
            st.divider()
            st.subheader("📊 Totais Acumulados")
            
            # Cálculo de totais por pessoa
            resumo = {}
            for _, linha in dados_salvos.iterrows():
                # Pessoa 1
                n1, v1 = linha['P1_Nome'], float(linha['P1_Valor'])
                resumo[n1] = resumo.get(n1, 0) + v1
                # Pessoa 2
                if linha['P2_Nome'] != "-":
                    n2, v2 = linha['P2_Nome'], float(linha['P2_Valor'])
                    resumo[n2] = resumo.get(n2, 0) + v2
            
            # Exibe Totais em Colunas
            col_m = st.columns(len(resumo))
            for idx, (nome, total) in enumerate(resumo.items()):
                col_m[idx].metric(nome, formatar_real(total))
            
            st.write("### 📋 Histórico na Planilha")
            st.dataframe(dados_salvos, use_container_width=True)
    except:
        st.info("Aguardando o primeiro registro para mostrar os dados.")
