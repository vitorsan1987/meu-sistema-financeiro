import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# Lista de Nomes Padronizada para os Selects
LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]

# Conexão com Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTILO CSS (TEMA ESCURO E ROXO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; }
    .historico-container { background: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; }
    .card-resumo-neutro { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; }
    .text-roxo { color: #8A05BE !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE DADOS ---
def get_data(sheet):
    return conn.read(worksheet=sheet, ttl="0s")

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- CARREGAR DADOS ---
try:
    df_cartoes = get_data("cartoes")
    df_compras = get_data("compras")
    df_fixos = get_data("fixos")
    dict_cores = dict(zip(df_cartoes['nome'], df_cartoes['cor']))
except:
    st.error("Erro de conexão. Verifique as Secrets e se a planilha está como 'Qualquer pessoa com o link pode EDITAR'.")
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    for _, r in df_cartoes.iterrows():
        gasto = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum()
        st.markdown(f"""
        <div style="background:{r['cor']}; padding:15px; border-radius:12px; margin-bottom:10px; color:white;">
            <b>{r['nome']}</b><br><small>Gasto Total: {format_real(gasto)}</small>
        </div>
        """, unsafe_allow_html=True)

# --- CONTEÚDO ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    c_form, c_hist = st.columns([1, 1.3])
    with c_form:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            nome = st.text_input("Descrição da Compra")
            valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f", value=0.0)
            cartao = st.selectbox("Cartão", df_cartoes['nome'].tolist())
            
            # SELEÇÃO DE MÚLTIPLAS PESSOAS
            quem = st.multiselect("Dividir com quem?", LISTA_NOMES)
            
            if st.form_submit_button("🚀 Registrar na Nuvem"):
                if nome and valor > 0 and quem:
                    # Cálculo: Valor Total / Quantidade de pessoas selecionadas
                    valor_indiv = round(valor / len(quem), 2)
                    nova_compra = pd.DataFrame([{
                        "id": int(datetime.now().timestamp()),
                        "nome": nome,
                        "valor_total": valor,
                        "cartao": cartao,
                        "participes": ",".join(quem),
                        "valor_por_pessoa": valor_indiv,
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }])
                    conn.update(worksheet="compras", data=pd.concat([df_compras, nova_compra], ignore_index=True))
                    st.rerun()
                else:
                    st.warning("Preencha a descrição, o valor e selecione as pessoas.")

    with c_hist:
        st.subheader("📋 Histórico")
        for idx, row in df_compras.iloc[::-1].iterrows():
            cor_c = dict_cores.get(row['cartao'], "#8A05BE")
            st.markdown(f"""
            <div class="historico-container">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:bold;">{row['nome']}</span>
                    <span style="color:{cor_c}; font-weight:bold; font-size:1.1em;">{format_real(row['valor_total'])}</span>
                </div>
                <div style="color:#8b949e; font-size:0.8em; margin-top:5px;">
                    {row['data']} | {row['cartao']} | Individual: {format_real(row['valor_por_pessoa'])}
                </div>
                <div style="font-size:0.85em; color:#adbac7; margin-top:5px; border-top:1px solid #333; padding-top:5px;">
                    Participantes: {str(row['participes']).replace(',', ', ')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Apagar", key=f"del_{row['id']}"):
                conn.update(worksheet="compras", data=df_compras.drop(idx))
                st.rerun()

with tabs[2]:
    st.subheader("📊 Resumo Neutro (Total Acumulado)")
    res_cols = st.columns(len(LISTA_NOMES))
    for i, nome in enumerate(LISTA_NOMES):
        # Soma as participações deste nome em todas as linhas de compras
        total_c = sum([r['valor_por_pessoa'] for _, r in df_compras.iterrows() if nome in str(r['participes']).split(',')])
        # Soma os fixos (se houver)
        total_f = df_fixos[df_fixos['p1_nome'] == nome]['p1_valor'].sum() + df_fixos[df_fixos['p2_nome'] == nome]['p2_total'].sum()
        
        with res_cols[i]:
            st.markdown(f"""
            <div class="card-resumo-neutro">
                <small style="color:#768390;">{nome}</small><br>
                <b style="font-size:1.4em; color:#adbac7;">{format_real(total_c + total_f)}</b>
            </div>
            """, unsafe_allow_html=True)
