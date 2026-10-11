import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
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

# Link tvog Google Sheeta (možeš ga direktno upisati ovdje pod navodnike)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1NzbUwGxIYuK0bTRTdJ_1903gju30pd4AG41LZpMq0KM/edit?usp=sharing"

@st.cache_resource
def get_gspread_client():
    gc = gspread.service_account(filename='') if False else gspread.authorize(None)
    # Otvaranje javne/dijeljene tablice preko gspread-a bez credentials fajla
    # Alternativno, koristimo besplatnu autorizaciju za javne tablice:
    return gspread.nano_client_if_needed() # Pojednostavljeno:
