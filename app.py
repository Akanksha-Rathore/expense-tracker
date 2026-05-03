import streamlit as st
import sqlite3
import pandas as pd
import datetime

# DB connection
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    amount REAL,
    category TEXT,
    date TEXT
)
""")
conn.commit()

# UI
st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("💸 Smart Expense Tracker")

# Sidebar
menu = st.sidebar.radio("Navigation", ["Dashboard", "Add Expense", "Manage Expenses"])

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.subheader("📊 Overview")

    data = cursor.execute("SELECT * FROM expenses").fetchall()
    df = pd.DataFrame(data, columns=["ID", "Title", "Amount", "Category", "Date"])

    if df.empty:
        st.info("No data yet. Add expenses first.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Spending", f"₹ {df['Amount'].sum():.2f}")
        col2.metric("Max Expense", f"₹ {df['Amount'].max():.2f}")
        col3.metric("Transactions", len(df))

        st.divider()

        # Category chart
        st.subheader("Spending by Category")
        category_data = df.groupby("Category")["Amount"].sum()
        st.bar_chart(category_data)

        # Monthly trend
        st.subheader("Monthly Trend")
        df["Month"] = df["Date"].dt.to_period("M")
        monthly = df.groupby("Month")["Amount"].sum()
        st.line_chart(monthly)

# ---------------- ADD ----------------
elif menu == "Add Expense":
    st.subheader("➕ Add Expense")

    with st.form("expense_form"):
        title = st.text_input("What did you spend on?")
        amount = st.number_input("Amount", min_value=0.0)
        category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Other"])
        date = st.date_input("Date", datetime.date.today())

        submitted = st.form_submit_button("Add Expense")

        if submitted:
            cursor.execute(
                "INSERT INTO expenses (title, amount, category, date) VALUES (?, ?, ?, ?)",
                (title, amount, category, str(date))
            )
            conn.commit()
            st.success("Expense added successfully 🎉")

# ---------------- MANAGE ----------------
elif menu == "Manage Expenses":
    st.subheader("🧾 Manage Expenses")

    data = cursor.execute("SELECT * FROM expenses").fetchall()
    df = pd.DataFrame(data, columns=["ID", "Title", "Amount", "Category", "Date"])

    if df.empty:
        st.warning("No expenses found")
    else:
        st.dataframe(df, use_container_width=True)

        # Filter
        category_filter = st.selectbox("Filter by Category", ["All"] + list(df["Category"].unique()))

        if category_filter != "All":
            df = df[df["Category"] == category_filter]
            st.dataframe(df)

        # Delete
        ids = {f"{row[0]} - {row[1]}": row[0] for row in data}
        selected = st.selectbox("Delete Expense", list(ids.keys()))

        if st.button("Delete"):
            cursor.execute("DELETE FROM expenses WHERE id=?", (ids[selected],))
            conn.commit()
            st.success("Deleted successfully")

        # Export
        st.download_button(
            label="📥 Download CSV",
            data=df.to_csv(index=False),
            file_name="expenses.csv",
            mime="text/csv"
        )