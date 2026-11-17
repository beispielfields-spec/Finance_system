#---------------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      BEISP
#
# Created:     17/11/2026
# Copyright:   (c) BEISP 2026
# Licence:     <your licence>
#---------------------------------------------------------------------------------------

def main():
    pass

if __name__ == '__main__':
    main()



# finance_dashboard.py
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------------
# 1. Configurações iniciais
# ------------------------------------------------------------------
st.set_page_config(page_title="Controle Financeiro",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Estilo CSS do menu lateral azul escuro
st.markdown(
    """
    <style>
    .css-1lcbmhc {background-color: #001f3f; color: #fff;}
    .css-1d391kg {color: #fff;}
    .stSidebar {background-color: #001f3f;}
    .stSidebar .sidebar-content {color: #fff;}
    .stButton>button {background-color: #0074D9; color: #fff;}
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------
# 2. Conexão e criação de tabelas (se ainda não existirem)
# ------------------------------------------------------------------
@st.cache_resource
def get_connection():
    conn = sqlite3.connect("financas.db", check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data DATE NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data DATE NOT NULL
        )
    """)
    conn.commit()

init_db()

# ------------------------------------------------------------------
# 3. Funções auxiliares
# ------------------------------------------------------------------
def inserir_receita(descricao, valor, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO receitas (descricao, valor, data) VALUES (?, ?, ?)",
        (descricao, valor, data)
    )
    conn.commit()

def inserir_despesa(descricao, valor, data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO despesas (descricao, valor, data) VALUES (?, ?, ?)",
        (descricao, valor, data)
    )
    conn.commit()

def obter_dados(tabela, mes=None):
    conn = get_connection()
    query = f"SELECT descricao, valor, data FROM {tabela}"
    if mes:
        query += " WHERE strftime('%m', data) = ?"
        cursor = conn.execute(query, (mes,))
    else:
        cursor = conn.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=["Descrição", "Valor", "Data"])
    return df

def obter_total(tabela, mes=None):
    conn = get_connection()
    query = f"SELECT SUM(valor) FROM {tabela}"
    if mes:
        query += " WHERE strftime('%m', data) = ?"
        cursor = conn.execute(query, (mes,))
    else:
        cursor = conn.execute(query)
    total = cursor.fetchone()[0]
    return total or 0.0

# ------------------------------------------------------------------
# 4. Layout da aplicação
# ------------------------------------------------------------------
def main():
    # ------------------------------------------------------------------
    # 4.1 Menu lateral
    # ------------------------------------------------------------------
    st.sidebar.title("Menu")
    opcao = st.sidebar.radio(
        "Selecione a ação",
        ("Dashboard", "Cadastrar Receita", "Cadastrar Despesa", "Relatório Mensal")
    )

    # ------------------------------------------------------------------
    # 4.2 Dashboard
    # ------------------------------------------------------------------
    if opcao == "Dashboard":
        st.title("📊 Dashboard Financeiro")

        # Indicadores
        total_receitas = obter_total("receitas")
        total_despesas = obter_total("despesas")
        saldo = total_receitas - total_despesas

        col1, col2, col3 = st.columns(3)
        col1.metric("Receitas Totais", f"R$ {total_receitas:,.2f}")
        col2.metric("Despesas Totais", f"R$ {total_despesas:,.2f}")
        col3.metric("Saldo", f"R$ {saldo:,.2f}")

        # Gráficos mensais
        meses = ["01", "02", "03", "04", "05", "06",
                 "07", "08", "09", "10", "11", "12"]
        df_receitas = pd.DataFrame({
            "Mês": meses,
            "Receitas": [obter_total("receitas", m) for m in meses],
            "Despesas": [obter_total("despesas", m) for m in meses]
        })

        st.subheader("Receitas vs Despesas Mensais")
        st.line_chart(df_receitas.set_index("Mês"))

    # ------------------------------------------------------------------
    # 4.3 Cadastro de Receita
    # ------------------------------------------------------------------
    elif opcao == "Cadastrar Receita":
        st.title("🟢 Cadastrar Receita")
        with st.form("form_receita"):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            data = st.date_input("Data", datetime.today())
            submitted = st.form_submit_button("Salvar")
            if submitted:
                inserir_receita(descricao, valor, data.isoformat())
                st.success("Receita cadastrada com sucesso!")

    # ------------------------------------------------------------------
    # 4.4 Cadastro de Despesa
    # ------------------------------------------------------------------
    elif opcao == "Cadastrar Despesa":
        st.title("🔴 Cadastrar Despesa")
        with st.form("form_despesa"):
            descricao = st.text_input("Descrição")
            valor = st.number_input("Valor", min_value=0.0, format="%.2f")
            data = st.date_input("Data", datetime.today())
            submitted = st.form_submit_button("Salvar")
            if submitted:
                inserir_despesa(descricao, valor, data.isoformat())
                st.success("Despesa cadastrada com sucesso!")

    # ------------------------------------------------------------------
    # 4.5 Relatório Mensal
    # ------------------------------------------------------------------
    elif opcao == "Relatório Mensal":
        st.title("📅 Relatório Mensal")
        mes = st.selectbox(
            "Selecione o mês",
            options=[f"{i:02d}" for i in range(1, 13)],
            format_func=lambda x: datetime.strptime(x, "%m").strftime("%B")
        )
        df_receitas = obter_dados("receitas", mes)
        df_despesas = obter_dados("despesas", mes)

        st.subheader(f"Receitas - {datetime.strptime(mes, '%m').strftime('%B')}")
        st.dataframe(df_receitas)

        st.subheader(f"Despesas - {datetime.strptime(mes, '%m').strftime('%B')}")
        st.dataframe(df_despesas)

        total_receitas = obter_total("receitas", mes)
        total_despesas = obter_total("despesas", mes)
        saldo = total_receitas - total_despesas

        st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")
        st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
        st.metric("Saldo", f"R$ {saldo:,.2f}")

if __name__ == "__main__":
    main()