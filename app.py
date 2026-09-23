import streamlit as st
import requests
import sys
import os
from supabase import create_client, Client

# --- STEP 1: DYNAMIC IN-MEMORY SECRET INJECTION ---
if "secrets" not in sys.modules:
    token = st.secrets["GITHUB_TOKEN"]
    # Be sure to replace 'your-github-username' with your actual username
    url = "https://github.com"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.raw" 
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        import types
        secrets_module = types.ModuleType("secrets")
        exec(response.text, secrets_module.__dict__)
        sys.modules["secrets"] = secrets_module
    else:
        st.error(f"Failed to fetch secrets.py from GitHub. Status Code: {response.status_code}")
        st.stop()

# Import your module exactly as you designed it
import secrets
import polars as pl
import duckdb

# --- STEP 2: INITIALIZE SUPABASE CLIENT ---
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(supabase_url, supabase_key)


# --- STEP 3: B2C AUTHENTICATION & PAYMENT STATUS GATEWAY ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False
if "is_paid_user" not in st.session_state:
    st.session_state.is_paid_user = False

# Screen A: Handing Login/Sign Up
if not st.session_state.user_authenticated:
    st.title("🔐 Client Portal Login")
    tab1, tab2 = st.tabs(["Sign In", "Create Account"])
    
    with tab1:
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                if res.user:
                    st.session_state.user_authenticated = True
                    st.rerun()
            except Exception:
                st.error("Authentication failed. Please verify your email and password.")
                
    with tab2:
        st.info("Already paid via our website? Create your account below.")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Create Password (min 6 characters)", type="password", key="reg_password")
        
        if st.button("Register Account"):
            try:
                res = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                st.success("Account created! Please check your inbox for a confirmation email, then Sign In.")
            except Exception as e:
                st.error(f"Registration error: {str(e)}")
    st.stop()

# Screen B: Checking Payment Database Status (Querying the Profiles Table)
if st.session_state.user_authenticated and not st.session_state.is_paid_user:
    try:
        user_id = supabase.auth.get_user().user.id
        # Pull the specific row for this user out of the profiles table
        profile_data = supabase.table("profiles").select("is_paid").eq("id", user_id).execute()
        
        if profile_data.data and profile_data.data[0]["is_paid"]:
            st.session_state.is_paid_user = True
            st.rerun()
        else:
            # If the row doesn't exist or is_paid is False, show the payment block screen
            st.title("💳 Payment Required")
            st.warning("Your account does not have an active subscription.")
            st.write("Please purchase a subscription on our main storefront to unlock access.")
            
            # Button allowing them to check again if they just finished paying
            if st.button("🔄 I have paid, refresh access"):
                st.rerun()
                
            if st.button("Log Out"):
                supabase.auth.sign_out()
                st.session_state.user_authenticated = False
                st.rerun()
            st.stop()
    except Exception as e:
        st.error(f"Error checking license verification profiles: {str(e)}")
        st.stop()


# --- STEP 4: LICENSED ENVIRONMENT (STAYS COMPLETELY LOCKED UNTIL IS_PAID IS TRUE) ---
st.sidebar.success(f"👤 Account: {supabase.auth.get_user().user.email}")
if st.sidebar.button("Log Out"):
    supabase.auth.sign_out()
    st.session_state.user_authenticated = False
    st.session_state.is_paid_user = False
    st.rerun()

st.title("Premium Analytics Platform")
st.write("hello worlds")

# Execution engine testing your private logic repo
st.subheader("🧮 Proprietary Module Execution")
val1 = st.number_input("Input A", value=1)
val2 = st.number_input("Input B", value=1)

if st.button("Calculate Via Secrets"):
    result = secrets.Function(val1, val2) 
    st.success(f"Result returned from private module: {result}")


# --- STEP 5: ISOLATED SESSION FILE UPLOADER ---
st.markdown("---")
st.subheader("📁 Client Session Database")
uploaded_file = st.file_uploader("Upload your local DuckDB database file to populate dashboard", type=["db", "duckdb"])

if uploaded_file is not None:
    temp_path = f"session_{supabase.auth.get_user().user.id}.db"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success("Database attached successfully for this browser session.")
    st.info("System standby: Ready for DuckDB/Polars parsing algorithms.")
    
    # Absolute file trace clean up
    if os.path.exists(temp_path):
        os.remove(temp_path)
