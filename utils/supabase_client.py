import streamlit as st
from supabase import create_client

url = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
key = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]

supabase = create_client(url, key)
