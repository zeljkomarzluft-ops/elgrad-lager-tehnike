import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

# Konfiguracija maila
SMTP_SERVER = "smtp.yourserver.com"
SMTP_PORT = 587
SMTP_USER = "notifikacije@elgrad.hr"  
SMTP_PASS = "tvoja_lozinka" 
EMAIL_PRIMATELJ = "zeljko.marzluft@elgrad.hr"

# Povezivanje na Google Sheets preko gspread (koristi javni link ili secrets)
@st.cache_resource
def get_gspread_client():
    # Ako si stavio link u Streamlit Secrets, povući će ga od tamo, inače možeš direktno unijeti link
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    except:
        sheet_url = "Ovdje_zalijepi_svoj_link_ako_ne_koristis_secrets"
    
    gc = gspread.oauth_from_dict({}) # Ili otvoreni pristup preko gspread gsheet klona
    # Najjednostavnije otvaranje po URL-u za javno/dijeljene tablice:
    sh = gspread.no_service_account().open_by_url(sheet_url)
    return sh

# Alternativno, najlakši način za čitanje/pisanje bez komplikacija s ključevima na Streamlitu:
# Koristit ćemo gspread preko public gsheet ili jednostavnog uvoza.
