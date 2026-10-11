import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

# Čitanje SMTP postavki iz Streamlit Secrets
SMTP_SERVER = st.secrets["smtp"]["server"] if "smtp" in st.secrets else "smtp.gmail.com"
SMTP_PORT = int(st.secrets["smtp"]["port"]) if "smtp" in st.secrets else 587
SMTP_USER = st.secrets["smtp"]["user"] if "smtp" in st.secrets else ""
SMTP_PASS = st.secrets["smtp"]["password"] if "smtp" in st.secrets else ""
EMAIL_PRIMATELJ = st.secrets["smtp"]["recipient"] if "smtp" in st.secrets else "zeljko.marzluft@elgrad.hr"

LAGER_FILE = "lager.csv"
ARHIVA_FILE = "arhiva.csv"

POZNATI_ARTIKLI = [
    {"Naziv": "[RO20516992] PIPA BLANCOVITIS-S NT 3 cijevi", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20517348] SUDOPER BLANCOMETRA 5 S TARTUFO sa dalj.uprav.", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20517722] PIPA BLANCODARAS Silgranit-look Alumetalic VT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20517742] PIPA BLANCOMIDA KROM VT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20519416] PIPA BLANCOMIDA VT alumetalic", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20519418] PIPA BLANCOMIDA SILGRANIT BIJELA", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20521468] BLANCO FLEXON II 45/2", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20521473] Blanco Flexon II XL 60/3", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20521840] SUDOPER BLANCO ETAGON 500-IF", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20523326] SUDOPER BLANCO LEGRA XL 6 S antracit bez prib. bez dalj.", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20524254] SUDOPER BLANCO DINAS XL 6 S, bez dalj. upr.", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20525110] Sudoper Blanco LEMIS XL S-IF compact sa dalj.", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20525198] PIPA BLANCO FONTAS-S II KROM VT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20526019] BLANCO ZIA XL 6 S Compact SILGRANIT PuraDur CRNA, bez dalj. upr", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20526152] PIPA BLANCO DARAS SILGRANIT-LOOK CRNA VT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20527692] BLANCO ANDANO kadica (417x197mm), INOX", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20530571] PIPA ALVEUS AM20-PS G55 VT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20530955] AMICA ugradbena mikrovalna pećnica Integra AMMB20E1GI", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20530970] AMICA ugradbena mikrovalna pećnica AMMB25E2GI", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20540053] SUDOPER ALVEUS CADIT 40 Terra G22", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20540060] Sudoper ALVEUS Cadit 20, carbon A91", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20551270] KOLJENO FABER CRV 90", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20551635] FABER NEPOVRATNI VENTIL VR2 120", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20555031] Napa Faber Strip Smart PB X A60", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20555055] Napa Faber Value SL X A60, inox", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20557020] NAPA FABER Synthesis HiP PB X A90", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20802004] FRANKE SUDOPER NEPTUNE NEX 621", "Predviđena količina": 1.0, "JM": "set", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20802356] SUDOPER FRANKE LOGICA LINE LLX 611", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20802572] SUDOPER FRANKE ROTONDO RON 610-41", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20802625] PIPA FRANKE SINTA DOCCIA krom/grafit", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20802682] PIPA FRANKE-D SINTA krom/sahara", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20802734] SUDOPER FRANKE SKX651", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20802777] FRANKE inox krema 250 gr.", "Predviđena
