# utils/sheets_client.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid
import streamlit as st
import json

# ---------- Google Sheets auth using Streamlit secrets ----------
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from Streamlit secrets
gcp_creds = st.secrets["gcp_service_account"]
creds_dict = json.loads(json.dumps(gcp_creds))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
client = gspread.authorize(creds)

# ---------- Spreadsheet ----------
SPREADSHEET_ID = "1fBIJ16WzH0mWV8eG_zUQMkLQp-w6Cp_vjQvHod3HVHo"
sheet = client.open_by_key(SPREADSHEET_ID)

# ---------- Helper to get or create sheet ----------
def get_or_create_sheet(title, headers):
    try:
        ws = sheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows="1000", cols=str(len(headers)))
        ws.append_row(headers)
    return ws

# ---------- Sheets ----------
users_sheet = get_or_create_sheet("Users", ["email", "password"])
expenses_sheet = get_or_create_sheet("Expenses",
                                     ["id", "user_email", "amount", "category", "vendor", "date",
                                      "notes", "image_url", "raw_text", "created_at"])

# ---------- USERS ----------
def get_users_df():
    """Return Users sheet as DataFrame safely"""
    data = users_sheet.get_all_records()
    if not data:
        df = pd.DataFrame(columns=["email", "password"])
    else:
        df = pd.DataFrame(data)
        df.columns = [str(c).strip() for c in df.columns]
    return df

def add_user(email, password):
    df = get_users_df()
    if email in df['email'].values:
        return False  # user exists
    users_sheet.append_row([email, password])
    return True

def validate_user(email, password):
    df = get_users_df()
    user = df[(df['email'] == email) & (df['password'] == password)]
    return not user.empty

# ---------- EXPENSES ----------
def sheet_to_df():
    data = expenses_sheet.get_all_records()
    if not data:
        df = pd.DataFrame(columns=["id", "user_email", "amount", "category", "vendor", "date",
                                   "notes", "image_url", "raw_text", "created_at"])
    else:
        df = pd.DataFrame(data)
        df.columns = [str(c).strip() for c in df.columns]
    return df

def add_expense(user_email, amount, category, vendor, date, notes="", image_url="", raw_text=""):
    new_id = str(uuid.uuid4())
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expenses_sheet.append_row([new_id, user_email, amount, category, vendor, date,
                               notes, image_url, raw_text, created_at])
