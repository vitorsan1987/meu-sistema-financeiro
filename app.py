import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Finanças Pro Cloud", page_icon="💰", layout="wide")

# Conexão Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

LISTA_NOMES = ["Vitor", "Edvirge", "Adriana", "Duda"]
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

# --- FUNÇÕES DE SUPORTE ---
def get_data(tabela):
    try:
        res = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(res.data)
    except Exception:
        return pd.DataFrame()

def format_real(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 300px; }
    div[data-baseweb="select"] { background-color: #1c2128 !important; border-radius: 8px !important; border: 1px solid #444c56 !important; }
    .historico-container { background: #1c2128; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 12px; }
    .card-resumo { background: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #444c56; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- FILTROS ---
st.markdown("## 📊 Controle Financeiro")
col_m1, col_m2 = st.columns([1, 1])
with col_m1:
    mes_selecionado = st.selectbox("📅 Selecione o Mês", MESES, index=datetime.now().month - 1)
with col_m2:
    data_ano = st.date_input("📅 Selecione o Ano", value=datetime.now())
    ano_selecionado = data_ano.year

mes_idx = str(MESES.index(mes_selecionado) + 1).zfill(2)
filtro_data = f"/{mes_idx}/{ano_selecionado}"

# --- CARREGAR DADOS ---
df_cartoes = get_data("cartoes")
df_compras_raw = get_data("compras")
df_fixos_raw = get_data("fixos")

df_compras = df_compras_raw[df_compras_raw['data'].str.contains(filtro_data)] if not df_compras_raw.empty else pd.DataFrame()
df_fixos = df_fixos_raw[df_fixos_raw['data'].str.contains(filtro_data)] if not df_fixos_raw.empty else pd.DataFrame()

# --- BARRA LATERAL (CARTÕES) ---
with st.sidebar:
    st.markdown("<h3 style='color:#8A05BE;'>Meus Cartões</h3>", unsafe_allow_html=True)
    if not df_cartoes.empty:
        for _, r in df_cartoes.iterrows():
            st.markdown(f'<div style="padding:15px; border-radius:10px; background:{r["cor"]}; margin-bottom:10px;"><b>{r["nome"]}</b><br>**** {r["final"]}</div>', unsafe_allow_html=True)
    
    with st.expander("➕ Novo Cartão"):
        with st.form("add_card"):
            n = st.text_input("Banco")
            c = st.color_picker("Cor", "#8A05BE")
            f = st.text_input("Final", max_chars=4)
            if st.form_submit_button("Salvar"):
                supabase.table("cartoes").insert({"nome": n, "cor": c, "final": f}).execute()
                st.rerun()

# --- ABAS ---
tabs = st.tabs(["🛒 Compras", "🏠 Contas Fixas", "📊 Resumo Mensal"])

with tabs[0]:
    st.subheader("Registrar Compra no Cartão")
    # (Lógica de compras mantida conforme versões anteriores...)
    # [Omitido aqui para brevidade, mas deve permanecer no seu arquivo principal]

with tabs[1]:
    st.subheader("🏠 Gestão de Contas Fixas e Moradia")
    c1, c2 = st.columns([1, 1.4])
    
    with c1:
        st.markdown("### Lançar Gasto Fixo")
        with st.form("form_fixo", clear_on_submit=True):
            tipo_fixo = st.selectbox("Categoria", [
                "Parcela Financiamento AP", 
                "Amortização Financiamento", 
                "Condomínio", 
                "Luz", 
                "Internet", 
                "Outros"
            ], index=None, placeholder="Selecione o tipo...")
            
            valor_fixo = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", value=None)
            quem_fixo = st.multiselect("Responsáveis pelo Pagamento", LISTA_NOMES)
            obs = st.text_area("Observações (Ex: Amortização extra)", placeholder="Opcional")
            
            if st.form_submit_button("💾 Salvar Conta Fixa"):
                if tipo_fixo and valor_fixo and quem_fixo:
                    data_s = f"01/{mes_idx}/{ano_selecionado}"
                    supabase.table("fixos").insert({
                        "item": tipo_fixo,
                        "valor": valor_fixo,
                        "participes": ",".join(quem_fixo),
                        "data": data_s,
                        "obs": obs
                    }).execute()
                    st.success("Lançado com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha o tipo, valor e responsáveis.")

    with c2:
        st.markdown(f"### Detalhes de {mes_selecionado}")
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                participantes = r['participes'].split(',')
                st.markdown(f"""
                <div class="historico-container">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <b>{r['item']}</b><br>
                            <small style="color:#8b949e;">{r['obs'] if r['obs'] else ''}</small>
                        </div>
                        <div style="text-align:right;">
                            <b style="font-size:1.1em; color:#58a6ff;">{format_real(r['valor'])}</b><br>
                            <small>{len(participantes)} pessoa(s)</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_fixo_{r['id']}"):
                    supabase.table("fixos").delete().eq("id", r['id']).execute()
                    st.rerun()
        else:
            st.info("Nenhuma conta fixa lançada para este período.")

with tabs[2]:
    st.subheader(f"📊 Resumo Geral - {mes_selecionado}")
    r_cols = st.columns(len(LISTA_NOMES))
    
    for i, nome in enumerate(LISTA_NOMES):
        # Cálculo Compras
        total_c = 0.0
        if not df_compras.empty:
            for _, r in df_compras.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    total_c += (float(r['valor_total']) / int(r['parcelas_total'])) / len(parts)
        
        # Cálculo Contas Fixas
        total_f = 0.0
        if not df_fixos.empty:
            for _, r in df_fixos.iterrows():
                parts = [p.strip() for p in str(r['participes']).split(',')]
                if nome in parts:
                    total_f += float(r['valor']) / len(parts)
        
        with r_cols[i]:
            st.markdown(f"""
            <div class="card-resumo">
                <small>{nome.upper()}</small><br>
                <b style="font-size:1.5em;">{format_real(total_c + total_f)}</b><br>
                <hr style="margin:10px 0; border:0.5px solid #333;">
                <div style="font-size:0.8em; color:#8b949e;">
                    🛒 Cartão: {format_real(total_c)}<br>
                    🏠 Fixas/AP: {format_real(total_f)}
                </div>
            </div>
            """, unsafe_allow_html=True)
