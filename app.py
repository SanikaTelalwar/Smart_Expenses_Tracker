# app.py
import streamlit as st
import pandas as pd
import altair as alt
import datetime
from utils.sheets_client import add_user, validate_user, add_expense, sheet_to_df
from utils.ocr import ocr_image_to_text, parse_receipt_text  # optional OCR

st.set_page_config(page_title="Smart Expense Tracker", layout="wide")
st.title("Smart Expense Tracker")

# ---------- SESSION ----------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# ---------- AUTH ----------
if not st.session_state['logged_in']:
    st.sidebar.header("Sign in / Sign up")
    choice = st.sidebar.radio("Go to", ["Sign in", "Sign up"])
    email = st.sidebar.text_input("Email").strip()
    password = st.sidebar.text_input("Password", type="password").strip()

    if choice == "Sign up":
        if st.sidebar.button("Create account"):
            if email and password:
                res = add_user(email, password)
                if res:
                    st.success("Account created! Please sign in.")
                else:
                    st.error("User already exists!")
            else:
                st.error("Enter email and password!")
    else:  # Sign in
        if st.sidebar.button("Sign in"):
            if email and password:
                if validate_user(email, password):
                    st.session_state['logged_in'] = True
                    st.session_state['user_email'] = email
                    st.success(f"Signed in as {email}")
                else:
                    st.error("Invalid email or password!")
            else:
                st.error("Enter email and password!")

# ---------- DASHBOARD ----------
if st.session_state['logged_in']:
    st.sidebar.write(f"Signed in as: {st.session_state['user_email']}")
    if st.sidebar.button("Sign out"):
        st.session_state.clear()
        st.experimental_rerun()  # works in Streamlit <1.18; else just rerun manually

    tab1, tab2, tab3 = st.tabs(["Add Expense", "History", "Graph"])

    # ---------- Add Expense ----------
    with tab1:
        st.subheader("Add Expense")
        option = st.radio("Choose option", ["Upload Bill (OCR)", "Add Manually"])

        # ---------- Option 1: OCR ----------
        if option == "Upload Bill (OCR)":
            uploaded_file = st.file_uploader("Upload bill image (png/jpg)", type=["png","jpg","jpeg"])
            if uploaded_file:
                file_bytes = uploaded_file.getvalue()
                raw_text = ocr_image_to_text(file_bytes)
                parsed = parse_receipt_text(raw_text)

                # Extract automatically
                amount = parsed.get("total")
                date_in = parsed.get("date") or datetime.date.today()
                vendor = parsed.get("vendor") or "Unknown Vendor"
                category = st.selectbox("Category", ["Groceries","Transport","Meals","Other"])
                notes = st.text_area("Notes")

                # Fallback if OCR fails
                if amount is None:
                    amount = st.number_input("Could not detect amount. Enter manually:", min_value=0.0, step=1.0)

                if st.button("Save OCR Expense"):
                    add_expense(
                        st.session_state['user_email'],
                        amount,
                        category,
                        vendor,
                        str(date_in),
                        notes,
                        image_url="",
                        raw_text=raw_text
                    )
                    st.success(f"Saved {amount} ₹ to history!")
                    st.balloons()

        # ---------- Option 2: Manual ----------
        else:
            with st.form("manual_form"):
                amount = st.number_input("Amount", min_value=0.0, step=1.0)
                vendor = st.text_input("Vendor")
                date_in = st.date_input("Date", datetime.date.today())
                category = st.selectbox("Category", ["Groceries","Transport","Meals","Other"])
                notes = st.text_area("Notes")
                if st.form_submit_button("Save Manual Expense"):
                    add_expense(
                        st.session_state['user_email'],
                        amount,
                        category,
                        vendor,
                        str(date_in),
                        notes
                    )
                    st.success("Saved to history manually!")

    # ---------- History ----------
    with tab2:
        st.subheader("Expense History")
        df = sheet_to_df()
        if df.empty:
            st.info("No expenses yet!")
            user_df = pd.DataFrame()
        else:
            df.columns = [str(c).strip() for c in df.columns]
            if 'user_email' not in df.columns:
                st.error("Column 'user_email' not found in Expenses sheet!")
                user_df = pd.DataFrame()
            else:
                user_df = df[df['user_email'] == st.session_state['user_email']].copy()
                st.dataframe(user_df.sort_values("date", ascending=False))

    # ---------- Graph ----------
    with tab3:
        st.subheader("Monthly Expenses")
        if not user_df.empty:
            user_df['amount'] = pd.to_numeric(user_df['amount'], errors='coerce').fillna(0)
            user_df['date'] = pd.to_datetime(user_df['date'], errors='coerce')
            monthly = user_df.groupby(user_df['date'].dt.to_period("M"))['amount'].sum().reset_index()
            monthly['date'] = monthly['date'].dt.to_timestamp()
            chart = alt.Chart(monthly).mark_line(point=True).encode(
                x=alt.X("date:T", title="Month"),
                y=alt.Y("amount:Q", title="Total spent"),
                tooltip=["date","amount"]
            ).properties(width=700, height=300)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No expenses to display")
