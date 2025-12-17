import streamlit as st
import pandas as pd

st.set_page_config(page_title="Finanças Pro BR", layout="wide")

# Inicialização de dados persistentes
if 'transacoes' not in st.session_state:
    st.session_state.transacoes = []
if 'cartoes' not in st.session_state:
    st.session_state.cartoes = {}

# Função para formatar em Moeda Brasileira (R$)
def formatar_real(valor):
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")

st.title("💳 Gestão de Compras e Parcelas")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações")
    with st.expander("➕ Novo Cartão"):
        nome_card = st.text_input("Nome do Cartão", key="cad_card")
        if st.button("Salvar Cartão"):
            if nome_card and len(st.session_state.cartoes) < 5:
                st.session_state.cartoes[nome_card] = nome_card
                st.rerun()
    
    st.divider()
    st.write("### 💳 Seus Cartões")
    for c in st.session_state.cartoes.keys():
        st.code(c)
    
    if st.button("🗑️ Limpar Todos os Dados", type="primary"):
        st.session_state.transacoes = []
        st.session_state.cartoes = {}
        st.rerun()

# --- FORMULÁRIO DE LANÇAMENTO ---
st.subheader("📝 Registrar Compra")

# Seleção de modalidade fora do form para atualizar os nomes instantaneamente
tipo_gasto = st.radio(
    "Selecione a modalidade:",
    ["100% Minha", "Dividida (50/50)", "100% de Outra Pessoa"],
    horizontal=True
)

with st.form("form_financeiro", clear_on_submit=True):
    # Linha principal com os novos campos de parcela
    c1, c2, c3, c4, c5 = st.columns([2, 1, 0.7, 0.7, 1.5])
    
    with c1:
        desc = st.text_input("Descrição da Compra")
    with c2:
        valor = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
    with c3:
        # NOVO: Campo para o número da parcela atual
        p_atual = st.number_input("Nº Parc.", min_value=1, value=1, step=1)
    with c4:
        # NOVO: Campo para o total de parcelas
        p_total = st.number_input("Total", min_value=1, value=1, step=1)
    with c5:
        cartao_lista = list(st.session_state.cartoes.keys())
        cartao_sel = st.selectbox("Cartão Usado", cartao_lista if cartao_lista else ["Cadastre um cartão"])

    st.write("**Nomes dos Responsáveis:**")
    d1, d2 = st.columns(2)
    
    with d1:
        val_p1 = "Eu" if tipo_gasto == "100% Minha" else ""
        nome1 = st.text_input("Pessoa 1", value=val_p1)

    with d2:
        bloquear_p2 = True if tipo_gasto != "Dividida (50/50)" else False
        nome2 = st.text_input("Pessoa 2 (Para dividida)", disabled=bloquear_p2)

    enviar = st.form_submit_button("✅ Adicionar à Lista", use_container_width=True)

    if enviar:
        if not cartao_lista:
            st.error("Adicione um cartão na lateral primeiro.")
        elif not desc:
            st.error("Preencha a descrição!")
        elif tipo_gasto == "Dividida (50/50)" and (not nome1 or not nome2):
            st.error("Para divisões, preencha os dois nomes!")
        else:
            v_p1, v_p2 = 0.0, 0.0
            n2_final = nome2 if tipo_gasto == "Dividida (50/50)" else "-"

            if tipo_gasto == "Dividida (50/50)":
                v_p1 = v_p2 = valor / 2
            else:
                v_p1 = valor
            
            # Formata o texto da parcela como "1/10"
            texto_parcela = f"{p_atual}/{p_total}"
            
            st.session_state.transacoes.append({
                "Descrição": desc,
                "Valor Total": valor,
                "Parcela": texto_parcela,
                "Cartão": cartao_sel,
                "P1_Nome": nome1, "P1_Valor": v_p1,
                "P2_Nome": n2_final, "P2_Valor": v_p2
            })
            st.rerun()

# --- EXIBIÇÃO ---
if st.session_state.transacoes:
    st.divider()
    df = pd.DataFrame(st.session_state.transacoes)
    
    # Resumo de Totais
    st.subheader("📊 Totais por Nome")
    totais = {}
    for t in st.session_state.transacoes:
        totais[t['P1_Nome']] = totais.get(t['P1_Nome'], 0) + t['P1_Valor']
        if t['P2_Nome'] != "-":
            totais[t['P2_Nome']] = totais.get(t['P2_Nome'], 0) + t['P2_Valor']
    
    col_res = st.columns(len(totais))
    for idx, (nome, total) in enumerate(totais.items()):
        col_res[idx].metric(f"Total: {nome}", formatar_real(total))

    # Tabela Detalhada
    st.subheader("📋 Lista de Gastos")
    h_cols = st.columns([2, 1, 1, 1.5, 2, 2, 0.5])
    labels = ["Descrição", "Total", "Parc.", "Cartão", "Pessoa 1", "Pessoa 2", ""]
    for col, lab in zip(h_cols, labels):
        col.write(f"**{lab}**")

    for i, row in df.iterrows():
        r = st.columns([2, 1, 1, 1.5, 2, 2, 0.5])
        r[0].write(row['Descrição'])
        r[1].write(formatar_real(row['Valor Total']))
        r[2].write(row['Parcela'])
        r[3].write(row['Cartão'])
        r[4].write(f"{row['P1_Nome']}: {formatar_real(row['P1_Valor'])}")
        r[5].write(f"{row['P2_Nome']}: {formatar_real(row['P2_Valor'])}")
        if r[6].button("X", key=f"del_{i}"):
            st.session_state.transacoes.pop(i)
            st.rerun()