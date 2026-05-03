import streamlit as st
import pandas as pd
import datetime
import sqlite3
from auth import register_user, login_user

conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

st.set_page_config(page_title="AI Expense Tracker", layout="wide")

# ---------- LOGIN ----------
if "user" not in st.session_state:
    st.title("🔐 Smart Expense Tracker")

    choice = st.radio("Select", ["Login", "Register"])

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if choice == "Register":
        if st.button("Register"):
            if register_user(username, password):
                st.success("Account created!")
            else:
                st.error("User exists")

    if choice == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid login")

# ---------- MAIN APP ----------
else:
    st.sidebar.title(f"👋 {st.session_state.user}")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Add Expense", "Manage", "Insights", "Logout"])

    # ---------- DASHBOARD ----------
    if menu == "Dashboard":
        st.title("📊 Dashboard")

        data = cursor.execute(
            "SELECT * FROM expenses WHERE user=?",
            (st.session_state.user,)
        ).fetchall()

        df = pd.DataFrame(data, columns=["ID", "User", "Title", "Amount", "Category", "Date"])

        if df.empty:
            st.info("Start adding expenses!")
        else:
            df["Date"] = pd.to_datetime(df["Date"])

            col1, col2, col3 = st.columns(3)
            col1.metric("Total", f"₹ {df['Amount'].sum():.2f}")
            col2.metric("Transactions", len(df))
            col3.metric("Highest", f"₹ {df['Amount'].max():.2f}")

            st.divider()

            st.subheader("📊 Category Distribution")
            st.bar_chart(df.groupby("Category")["Amount"].sum())

            st.subheader("📈 Monthly Trend")
            df["Month"] = df["Date"].dt.to_period("M")
            st.line_chart(df.groupby("Month")["Amount"].sum())

    # ---------- ADD ----------
    elif menu == "Add Expense":
        st.title("➕ Add Expense")

        with st.form("form"):
            title = st.text_input("Expense Title")
            amount = st.number_input("Amount", min_value=0.0)
            category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Other"])
            date = st.date_input("Date", datetime.date.today())

            if st.form_submit_button("Add"):
                cursor.execute(
                    "INSERT INTO expenses (user, title, amount, category, date) VALUES (?, ?, ?, ?, ?)",
                    (st.session_state.user, title, amount, category, str(date))
                )
                conn.commit()
                st.success("Added successfully!")

    # ---------- MANAGE ----------
    elif menu == "Manage":
        st.title("🧾 Manage Expenses")

        data = cursor.execute(
            "SELECT * FROM expenses WHERE user=?",
            (st.session_state.user,)
        ).fetchall()

        df = pd.DataFrame(data, columns=["ID", "User", "Title", "Amount", "Category", "Date"])
        st.dataframe(df, use_container_width=True)

        ids = {f"{row[0]} - {row[2]}": row[0] for row in data}
        selected = st.selectbox("Delete Expense", list(ids.keys()))

        if st.button("Delete"):
            cursor.execute("DELETE FROM expenses WHERE id=?", (ids[selected],))
            conn.commit()
            st.success("Deleted")

    # ---------- AI INSIGHTS ----------
    elif menu == "Insights":
        st.title("🤖 Smart Insights")

        data = cursor.execute(
            "SELECT * FROM expenses WHERE user=?",
            (st.session_state.user,)
        ).fetchall()

        df = pd.DataFrame(data, columns=["ID", "User", "Title", "Amount", "Category", "Date"])

        if df.empty:
            st.warning("No data for insights")
        else:
            df["Date"] = pd.to_datetime(df["Date"])
            df["Month"] = df["Date"].dt.to_period("M")

            monthly = df.groupby("Month")["Amount"].sum()

            # Insight 1
            if len(monthly) > 1:
                if monthly.iloc[-1] > monthly.iloc[-2]:
                    st.error("⚠️ Your spending increased this month!")
                else:
                    st.success("✅ You reduced spending this month!")

            # Insight 2
            top_category = df.groupby("Category")["Amount"].sum().idxmax()
            st.info(f"💡 Most spending category: {top_category}")

            # Insight 3
            avg = df["Amount"].mean()
            st.write(f"📊 Average transaction: ₹ {avg:.2f}")

    # ---------- LOGOUT ----------
    elif menu == "Logout":
        st.session_state.clear()
        st.rerun()