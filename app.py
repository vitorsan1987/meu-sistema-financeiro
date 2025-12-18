import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro", page_icon="💰", layout="wide")

# --- LISTA DE NOMES PADRONIZADA (Sem o vazio no início para o multiselect) ---
NOMES_DISPONIVEIS = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div>div {
        background-color: #0d1117 !important; color: white !important; border: 1px solid #30363d !important;
    }
    .credit-card {
        padding: 25px; border-radius: 20px; color: white; margin-bottom: 15px; 
        box-shadow: 0 8px 16px rgba(0,0,0,0.4); width: 100%; min-height: 180px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .historico-container {
        background: #161b22; padding: 18px; border-radius: 12px;
        border: 1px solid #30363d; margin-bottom: 15px;
    }
    .card-resumo-neutro {
        background: #1c2128; padding: 25px; border-radius: 15px;
        border: 1px solid #444c56; margin-bottom: 20px;
    }
    .text-label { color: #8b949e; font-size: 0.85em; }
    .label-neutra { color: #768390; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
conn = sqlite3.connect('financas.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('CREATE TABLE IF NOT EXISTS cartoes (id INTEGER PRIMARY KEY, nome TEXT, cor TEXT, final TEXT, venc TEXT)')
    # Nova estrutura: participes armazena os nomes separados por vírgula, valor_por_pessoa o valor dividido
    c.execute('''CREATE TABLE IF NOT EXISTS compras (id INTEGER PRIMARY KEY, nome TEXT, valor_total REAL, cartao TEXT, 
                 parcelas INTEGER, parcela_atual INTEGER, participes TEXT, valor_por_pessoa REAL, data TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS fixos (id INTEGER PRIMARY KEY, item TEXT, valor REAL, p1_nome TEXT, p1_valor REAL, p2_nome TEXT, p2_valor REAL)')
    conn.commit()

init_db()

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    df_c_db = pd.read_sql("SELECT * FROM cartoes", conn)
    df_compras_todas = pd.read_sql("SELECT cartao, valor_total FROM compras", conn)
    dict_cores = dict(zip(df_c_db['nome'], df_c_db['cor']))
    
    for _, r in df_c_db.iterrows():
        gasto_cartao = df_compras_todas[df_compras_todas['cartao'] == r['nome']]['valor_total'].sum()
        st.markdown(f'<div class="credit-card" style="background:{r["cor"]};"><div><div style="display:flex; justify-content:space-between;"><b>{r["nome"]}</b><span style="font-size:0.7em;">CREDIT</span></div><div style="font-family:monospace; letter-spacing:3px; font-size:1.2em; margin-top:25px;">**** **** **** {r["final"]}</div></div><div style="display:flex; justify-content:space-between; align-items:flex-end;"><div><div style="font-size:0.6em;">GASTO TOTAL</div><b>{format_real(gasto_cartao)}</b></div><div style="font-size:0.7em;">DIA {r["venc"]}</div></div></div>', unsafe_allow_html=True)
        if st.button(f"🗑️ Remover {r['nome']}", key=f"del_c_{r['id']}"):
            c.execute("DELETE FROM cartoes WHERE id=?", (r['id'],))
            conn.commit()
            st.rerun()

    with st.expander("➕ Novo Cartão"):
        n_c = st.text_input("Banco")
        c_c = st.color_picker("Cor", "#8A05BE")
        f_c = st.text_input("Finais", max_chars=4)
        v_c = st.number_input("Vencimento", 1, 31, 28)
        if st.button("Salvar Cartão"):
            c.execute("INSERT INTO cartoes (nome, cor, final, venc) VALUES (?,?,?,?)", (n_c, c_c, f_c, str(v_c)))
            conn.commit()
            st.rerun()

# --- CONTEÚDO PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>💰 Finanças Compartilhadas</h1>", unsafe_allow_html=True)
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    col_form, col_hist = st.columns([1, 1.3])
    with col_form:
        st.subheader("Registrar Gasto")
        with st.form("compra_form", clear_on_submit=True):
            nome_compra = st.text_input("Descrição")
            valor_compra = st.number_input("Valor Total (R$)", min_value=0.0, step=0.01)
            c1, c2, c3 = st.columns(3)
            cartao_sel = c1.selectbox("Cartão", df_c_db['nome'].tolist() if not df_c_db.empty else ["Nenhum"])
            t_p = c2.number_input("Total Parc.", 1, 60, 1)
            a_p = c3.number_input("Parc. Atual", 1, 60, 1)
            
            # NOVIDADE: SELEÇÃO DE QUEM VAI DIVIDIR
            quem_divide = st.multiselect("Dividir com:", options=NOMES_DISPONIVEIS)
            
            if st.form_submit_button("🚀 Registrar"):
                if nome_compra and valor_compra > 0 and quem_divide:
                    valor_dividido = round(valor_compra / len(quem_divide), 2)
                    participantes_str = ",".join(quem_divide)
                    c.execute("INSERT INTO compras (nome, valor_total, cartao, parcelas, parcela_atual, participes, valor_por_pessoa, data) VALUES (?,?,?,?,?,?,?,?)",
                              (nome_compra, valor_compra, cartao_sel, t_p, a_p, participantes_str, valor_dividido, datetime.now().strftime("%d/%m/%Y")))
                    conn.commit()
                    st.rerun()
                else:
                    st.error("Preencha tudo e selecione ao menos 1 pessoa.")

    with col_hist:
        st.subheader("📋 Histórico")
        df_hist = pd.read_sql("SELECT * FROM compras ORDER BY id DESC", conn)
        for _, r in df_hist.iterrows():
            cor_v = dict_cores.get(r['cartao'], "#8A05BE")
            st.markdown(f"""
            <div class="historico-container">
                <div style="display:flex; justify-content:space-between;">
                    <b>{r['nome']}</b>
                    <span style="color:{cor_v}; font-weight:bold;">{format_real(r['valor_total'])}</span>
                </div>
                <div class="text-label">{r['data']} | {r['cartao']} | Parc. {r['parcela_atual']}/{r['parcelas']}</div>
                <div style="margin-top:8px; font-size:0.85em; border-top:1px solid #30363d; padding-top:5px; color:#8b949e;">
                    Participantes: <span style="color:{cor_v};">{r['participes'].replace(',', ', ')}</span><br>
                    Valor individual: <span style="color:{cor_v}; font-weight:bold;">{format_real(r['valor_por_pessoa'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Apagar", key=f"del_h_{r['id']}"):
                c.execute("DELETE FROM compras WHERE id=?", (r['id'],))
                conn.commit()
                st.rerun()

with tabs[1]:
    st.subheader("🏠 Contas Fixas (Simples)")
    with st.form("fixos_form", clear_on_submit=True):
        f_i = st.text_input("Conta")
        f_v = st.number_input("Valor", min_value=0.0)
        col_n1, col_n2 = st.columns(2)
        f_n1 = col_n1.selectbox("Pessoa A", [""] + NOMES_DISPONIVEIS)
        f_n2 = col_n2.selectbox("Pessoa B (Opcional)", [""] + NOMES_DISPONIVEIS)
        if st.form_submit_button("💾 Salvar"):
            v_ind = f_v / 2 if f_n2 != "" else f_v
            c.execute("INSERT INTO fixos (item, valor, p1_nome, p1_valor, p2_nome, p2_valor) VALUES (?,?,?,?,?,?)", (f_i, f_v, f_n1, v_ind, f_n2, v_ind if f_n2 != "" else 0))
            conn.commit()
            st.rerun()
    st.dataframe(pd.read_sql("SELECT * FROM fixos", conn), use_container_width=True)

with tabs[2]:
    st.subheader("📊 Resumo Mensal")
    df_c = pd.read_sql("SELECT * FROM compras", conn)
    df_f = pd.read_sql("SELECT * FROM fixos", conn)
    
    cols = st.columns(len(NOMES_DISPONIVEIS))
    for idx, n in enumerate(NOMES_DISPONIVEIS):
        # Lógica para somar as participações nas compras
        total_compras = 0
        for _, row in df_c.iterrows():
            if n in row['participes'].split(','):
                total_compras += row['valor_por_pessoa']
        
        # Lógica para fixos
        total_fixos = df_f[df_f['p1_nome'] == n]['p1_valor'].sum() + df_f[df_f['p2_nome'] == n]['p2_valor'].sum()
        
        with cols[idx]:
            st.markdown(f"""
            <div class="card-resumo-neutro">
                <h3 style="margin:0; color:#adbac7;">{n}</h3>
                <div class="label-neutra">Total Compras</div>
                <div style="font-size:1.1em; margin-bottom:10px;">{format_real(total_compras)}</div>
                <div class="label-neutra">Total Fixos</div>
                <div style="font-size:1.1em; margin-bottom:15px;">{format_real(total_fixos)}</div>
                <div class="label-neutra" style="border-top:1px solid #444c56; padding-top:10px;">Total Geral</div>
                <div style="color:#adbac7; font-size:1.6em; font-weight:bold;">{format_real(total_compras + total_fixos)}</div>
            </div>
            """, unsafe_allow_html=True)