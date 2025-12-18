import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# Conexão Supabase através das Secrets do Streamlit Cloud
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# Lista fixa de nomes para seleção e divisão
LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]

# --- FUNÇÕES DE DADOS (SUPABASE) ---
def get_data(tabela):
    res = supabase.table(tabela).select("*").execute()
    return pd.DataFrame(res.data)

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS (TEMA ESCURO E ROXO) ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    
    /* Histórico */
    .historico-container { 
        background: #161b22; padding: 15px; border-radius: 10px; 
        border: 1px solid #30363d; margin-bottom: 10px; 
    }
    
    /* Cards de Resumo */
    .card-resumo { 
        background: #1c2128; padding: 20px; border-radius: 12px; 
        border: 1px solid #444c56; margin-bottom: 15px; 
    }
    
    /* Botões e Inputs */
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- CARREGAR DADOS INICIAIS ---
df_cartoes = get_data("cartoes")
df_compras = get_data("compras")
df_fixos = get_data("fixos")

# --- BARRA LATERAL (GESTÃO DE CARTÕES) ---
with st.sidebar:
    st.markdown("<h2 style='color:#8A05BE;'>💳 Meus Cartões</h2>", unsafe_allow_html=True)
    
    # Listar cartões existentes com soma total
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            # Lógica de soma do total gasto neste cartão específico
            if not df_compras.empty:
                total_do_cartao = df_compras[df_compras['cartao'] == r['nome']]['valor_total'].sum()
            else:
                total_do_cartao = 0.0

            st.markdown(f"""
            <div style="background:{r['cor']}; padding:15px; border-radius:10px; margin-bottom:10px; color:white; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                <div style="display:flex; justify-content:space-between;">
                    <b style="font-size:1.1em;">{r['nome']}</b>
                    <span style="font-size:0.7em; opacity:0.8;">CREDIT</span>
                </div>
                <div style="font-family:monospace; font-size:1.1em; margin: 15px 0;">**** **** **** {r['final']}</div>
                <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                    <div>
                        <div style="font-size:0.6em; opacity:0.8;">GASTO TOTAL NO CARTÃO</div>
                        <b style="font-size:1.1em;">{format_real(total_do_cartao)}</b>
                    </div>
                    <div style="font-size:0.7em;">DIA {r['venc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🗑️ Remover {r['nome']}", key=f"del_card_{r['id']}"):
                supabase.table("cartoes").delete().eq("id", r['id']).execute()
                st.rerun()
    else:
        st.info("Nenhum cartão cadastrado.")

    st.divider()
    
    # Formulário para Adicionar Novo Cartão
    with st.expander("➕ Adicionar Novo Cartão"):
        with st.form("form_novo_cartao", clear_on_submit=True):
            n_nome = st.text_input("Nome do Banco (Ex: Nubank)")
            n_cor = st.color_picker("Cor do Cartão", "#8A05BE")
            n_final = st.text_input("4 últimos dígitos", max_chars=4)
            n_venc = st.number_input("Dia de Vencimento", 1, 31, 28)
            
            if st.form_submit_button("Salvar Cartão"):
                if n_nome and n_final:
                    supabase.table("cartoes").insert({
                        "nome": n_nome,
                        "cor": n_cor,
                        "final": n_final,
                        "venc": str(n_venc)
                    }).execute()
                    st.success("Cartão adicionado!")
                    st.rerun()

# --- CONTEÚDO PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>💰 Finanças Compartilhadas</h1>", unsafe_allow_html=True)
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    col1, col2 = st.columns([1, 1.3])
    
    with col1:
        st.subheader("Registrar Gasto")
        with st.form("form_compra", clear_on_submit=True):
            nome_compra = st.text_input("O que você comprou?")
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            
            lista_cartoes = df_cartoes['nome'].tolist() if not df_cartoes.empty else ["Nenhum"]
            cartao_sel = st.selectbox("Cartão utilizado", options=lista_cartoes)
            
            # SELEÇÃO DINÂMICA DE QUEM VAI DIVIDIR
            quem_participa = st.multiselect("Dividir com:", options=LISTA_NOMES)
            
            if st.form_submit_button("🚀 Salvar Gasto"):
                if nome_compra and valor_total > 0 and quem_participa:
                    # Divisão dinâmica baseada na quantidade de pessoas selecionadas
                    valor_indiv = round(valor_total / len(quem_participa), 2)
                    
                    supabase.table("compras").insert({
                        "nome": nome_compra,
                        "valor_total": valor_total,
                        "cartao": cartao_sel,
                        "participes": ",".join(quem_participa),
                        "valor_por_pessoa": valor_indiv,
                        "data": datetime.now().strftime("%d/%m/%Y")
                    }).execute()
                    st.success("Gasto registrado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha todos os campos e selecione os participantes.")

    with col2:
        st.subheader("📋 Histórico")
        if not df_compras.empty:
            dict_cores = dict(zip(df_cartoes['nome'], df_cartoes['cor']))
            
            for idx, r in df_compras.iloc[::-1].iterrows():
                cor_card = dict_cores.get(r['cartao'], "#8A05BE")
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <b>{r['nome']}</b>
                        <span style="color:{cor_card}; font-weight:bold;">{format_real(r['valor_total'])}</span>
                    </div>
                    <div style="font-size:0.85em; color:#8b949e; margin-top:5px;">
                        {r['data']} | Cada um paga: {format_real(r['valor_por_pessoa'])}
                    </div>
                    <div style="font-size:0.8em; color:#adbac7; margin-top:3px; border-top: 1px solid #333; padding-top: 3px;">
                        Participantes: {str(r['participes']).replace(',', ', ')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Apagar Registro", key=f"del_h_{r['id']}"):
                    supabase.table("compras").delete().eq("id", r['id']).execute()
                    st.rerun()

with tabs[2]:
    st.subheader("📊 Resumo de Dívidas Totais")
    if not df_compras.empty:
        cols = st.columns(len(LISTA_NOMES))
        for i, nome in enumerate(LISTA_NOMES):
            # Soma as participações individuais (valor_por_pessoa) onde o nome consta na lista
            total_pessoa = sum([r['valor_por_pessoa'] for _, r in df_compras.iterrows() if nome in str(r['participes']).split(',')])
            
            with cols[i]:
                st.markdown(f"""
                <div class="card-resumo">
                    <small style="color:#768390; text-transform:uppercase; letter-spacing:1px;">{nome}</small><br>
                    <b style="font-size:1.6em; color:#adbac7;">{format_real(total_pessoa)}</b>
                    <div style="font-size:0.7em; color:#555; margin-top:5px;">TOTAL ACUMULADO</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Registre gastos para visualizar o resumo mensal.")
