import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração da Página
st.set_page_config(page_title="Finanças Pro Sync", layout="wide")

# Conexão Segura com Google Sheets (usa os Secrets do Streamlit Cloud)
conn = st.connection("gsheets", type=GSheetsConnection)

# Função para formatar em Moeda Brasileira (R$)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

st.title("💳 Gestão Financeira Cloud - Completo")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    if 'cartoes' not in st.session_state:
        st.session_state.cartoes = ["Nubank", "BB", "Itaú"]
    
    with st.expander("➕ Gerenciar Cartões"):
        novo_c = st.text_input("Nome do Cartão")
        if st.button("Adicionar"):
            if novo_c:
                st.session_state.cartoes.append(novo_c)
                st.rerun()
    
    st.divider()
    st.write("### 💳 Meus Cartões")
    for c in st.session_state.cartoes:
        st.code(c)

# --- FORMULÁRIO DE LANÇAMENTO ---
st.subheader("📝 Registrar Nova Compra")

# Modalidade fora do formulário para atualizar os campos de nome instantaneamente
tipo_gasto = st.radio(
    "Como deseja dividir este gasto?",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro_final", clear_on_submit=True):
    # Linha 1: Dados da Compra e Parcelas
    c1, c2, c3, c4, c5 = st.columns([2, 1, 0.7, 0.7, 1.5])
    
    with c1:
        desc = st.text_input("Descrição da Compra")
    with c2:
        valor = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3:
        p_atual = st.number_input("Nº Parc.", min_value=1, value=1)
    with c4:
        p_total = st.number_input("Total Parc.", min_value=1, value=1)
    with c5:
        cartao_sel = st.selectbox("Cartão Usado", st.session_state.cartoes)

    # Linha 2: Nomes dos Responsáveis
    st.write("**Nomes das Pessoas:**")
    d1, d2 = st.columns(2)
    
    with d1:
        # Se for minha, já preenche "Eu", se não, deixa livre
        v_p1 = "Eu" if tipo_gasto == "100% Minha" else ""
        nome1 = st.text_input("Nome da Pessoa 1", value=v_p1)
    
    with d2:
        # Só libera se for dividida
        bloquear_p2 = (tipo_gasto != "Dividida (50/50)")
        nome2 = st.text_input("Nome da Pessoa 2", disabled=bloquear_p2, placeholder="Obrigatório para divisão")

    # Botão de Envio
    enviar = st.form_submit_button("✅ Salvar na Planilha Cloud", use_container_width=True)

    if enviar:
        if not desc:
            st.error("Erro: Preencha a descrição da compra!")
        elif tipo_gasto == "Dividida (50/50)" and (not nome1 or not nome2):
            st.error("Erro: Para divisões, informe os dois nomes!")
        else:
            # Lógica de cálculo de valores por pessoa
            v_p1, v_p2 = 0.0, 0.0
            n2_final = nome2 if tipo_gasto == "Dividida (50/50)" else "-"

            if tipo_gasto == "Dividida (50/50)":
                v_p1 = v_p2 = valor / 2
            else:
                v_p1 = valor # Vai tudo para a Pessoa 1 (Eu ou Outra Pessoa)
            
            # Preparar a linha para o Google Sheets
            nova_linha = pd.DataFrame([{
                "Descrição": desc,
                "Valor Total": valor,
                "Parcela": f"{p_atual}/{p_total}",
                "Cartão": cartao_sel,
                "P1_Nome": nome1,
                "P1_Valor": v_p1,
                "P2_Nome": n2_final,
                "P2_Valor": v_p2
            }])

            try:
                # 1. Lê o que já existe na nuvem
                df_nuvem = conn.read(ttl=0)
                # 2. Junta com a nova linha
                df_atualizado = pd.concat([df_nuvem, nova_linha], ignore_index=True)
                # 3. Manda de volta para o Google Sheets
                conn.update(data=df_atualizado)
                st.success("Sucesso! Dados gravados na sua planilha do Google.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao conectar com a planilha: {e}")

# --- EXIBIÇÃO E RELATÓRIO ---
try:
    # Busca os dados atualizados do Sheets
    dados = conn.read(ttl=0)
    
    if not dados.empty:
        st.divider()
        st.subheader("📊 Totais Acumulados por Pessoa")
        
        # Cálculo de totais por nome de forma dinâmica
        resumo = {}
        for _, row in dados.iterrows():
            # Soma para Pessoa 1
            n1 = row['P1_Nome']
            resumo[n1] = resumo.get(n1, 0) + float(row['P1_Valor'])
            # Soma para Pessoa 2 (se existir)
            n2 = row['P2_Nome']
            if n2 != "-":
                resumo[n2] = resumo.get(n2, 0) + float(row['P2_Valor'])
        
        # Mostra em colunas (Metrics)
        col_metrics = st.columns(len(resumo))
        for idx, (pessoa, total) in enumerate(resumo.items()):
            col_metrics[idx].metric(f"Total: {pessoa}", formatar_real(total))

        # Tabela Detalhada com filtro opcional
        st.subheader("📋 Histórico Completo (Google Sheets)")
        
        # Filtro de busca simples
        busca = st.text_input("Filtrar descrição ou nome...")
        if busca:
            dados = dados[dados.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)]
            
        st.dataframe(dados, use_container_width=True)
except:
    st.info("Aguardando conexão com o Google Sheets ou primeira compra...")
