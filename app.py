import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

SMTP_SERVER = "smtp.yourserver.com"
SMTP_PORT = 587
SMTP_USER = "notifikacije@elgrad.hr"  
SMTP_PASS = "tvoja_lozinka" 
EMAIL_PRIMATELJ = "zeljko.marzluft@elgrad.hr"

SHEET_URL = "https://docs.google.com/spreadsheets/d/1NzbUwGxIYuK0bTRTdJ_1903gju30pd4AG41LZpMq0KM/edit?usp=sharing"

def get_csv_url(sheet_url, sheet_name):
    base_id = sheet_url.split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

@st.cache_data(ttl=1)
def load_data():
    try:
        url_lager = get_csv_url(SHEET_URL, "lager")
        df_lager = pd.read_csv(url_lager)
        if not df_lager.empty:
            df_lager.columns = df_lager.columns.str.strip()
            # Uklonimo prazne retke ako postoje
            df_lager = df_lager.dropna(subset=[df_lager.columns[0]])
        else:
            df_lager = pd.DataFrame(columns=["Naziv", "Predviđena količina", "JM", "Kategorija"])
    except Exception as e:
        df_lager = pd.DataFrame(columns=["Naziv", "Predviđena količina", "JM", "Kategorija"])
        
    try:
        url_arhiva = get_csv_url(SHEET_URL, "arhiva")
        df_arhiva = pd.read_csv(url_arhiva)
        if not df_arhiva.empty:
            df_arhiva.columns = df_arhiva.columns.str.strip()
            df_arhiva = df_arhiva.dropna(subset=[df_arhiva.columns[0]])
        else:
            df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
    except Exception as e:
        df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
        
    return df_lager, df_arhiva

def save_to_sheet(df_lager, df_arhiva):
    # Budući da gspread traži credentials, spremamo podatke lokalno u session state 
    # ili upućujemo na Google Sheets postavke dijeljenja
    st.session_state["df_lager_local"] = df_lager
    st.session_state["df_arhiva_local"] = df_arhiva

df_lager, df_arhiva = load_data()

# Ako imamo nešto u session state-u (lokalno dodano prije sinkronizacije), koristimo to
if "df_lager_local" in st.session_state and not st.session_state["df_lager_local"].empty:
    df_lager = st.session_state["df_lager_local"]

st.title("📦 Sustav za praćenje slobodnog lagera - Elgrad Pula")

tab_pregled, tab_dodaj, tab_prodaja, tab_arhiva = st.tabs([
    "📋 Pregled Lagera", 
    "➕ Dodaj Artikal (Admin)", 
    "❌ Evidencija Prodaje (Trgovci)", 
    "📊 Arhiva Prodaje"
])

with tab_pregled:
    st.header("Slobodno na lageru")
    search_query = st.text_input("🔍 Pretraži po nazivu ili šifri:", "")
    
    filtered_df = df_lager.copy()
    if search_query and not filtered_df.empty:
        naziv_col = filtered_df.columns[0]
        filtered_df = filtered_df[
            filtered_df[naziv_col].astype(str).str.contains(search_query, case=False, na=False)
        ]
    st.dataframe(filtered_df, use_container_width=True)
    st.sidebar.info(f"Broj učitanih artikala: {len(df_lager)}")

with tab_dodaj:
    st.header("Unos novog artikla")
    with st.form("form_dodaj"):
        novi_naziv = st.text_input("Naziv (šifra i naziv artikla)")
        nova_kategorija = st.selectbox("Kategorija", ["Tehnika", "Sudoperi", "Pipe", "Zidne obloge", "Ostalo"])
        nova_jm = st.text_input("JM (Jedinična mjera)", value="kom")
        nova_kolicina = st.number_input("Predviđena količina", min_value=0.0, value=1.0, step=1.0)
        
        if st.form_submit_button("Spremi u lager"):
            if not novi_naziv.strip():
                st.error("Upiši naziv artikla!")
            else:
                col_names = df_lager.columns.tolist() if not df_lager.empty else ["Naziv", "Predviđena količina", "JM", "Kategorija"]
                new_row = pd.DataFrame([[novi_naziv, nova_kolicina, nova_jm, nova_kategorija]], columns=col_names[:4])
                updated_lager = pd.concat([df_lager, new_row], ignore_index=True)
                
                st.session_state["df_lager_local"] = updated_lager
                st.success("Uspješno dodano na lager!")
                st.rerun()

with tab_prodaja:
    st.header("Evidencija prodaje i razduženje")
    if df_lager.empty:
        st.warning("Lager je trenutačno prazan. Dodaj artikle u kartici 'Dodaj Artikal'.")
    else:
        cols = df_lager.columns.tolist()
        naziv_c = cols[0]
        kolicina_c = cols[1] if len(cols) > 1 else cols[0]
        jm_c = cols[2] if len(cols) > 2 else cols[0]
        
        opcije_artikala = df_lager.apply(lambda row: f"{row[naziv_c]} (Dostupno: {row[kolicina_c]} {row[jm_c]})", axis=1).tolist()
        odabrani_artikal = st.selectbox("Izaberi prodani artikal:", opcije_artikala)
        
        broj_ponude = st.text_input("📝 Unesi broj ponude / računa (Obavezno):")
        
        if odabrani_artikal:
            puni_naziv_iz_selecta = odabrani_artikal.split(" (Dostupno:")[0]
            red_artikla = df_lager[df_lager[naziv_c].astype(str) == puni_naziv_iz_selecta].iloc[0]
            trenutna_kolicina = float(red_artikla[kolicina_c])
            jm_artikla = str(red_artikla[jm_c])
            
            kolicina_za_maknuti = st.number_input(f"Količina za maknuti ({jm_artikla}):", min_value=0.5, max_value=max(0.5, trenutna_kolicina), value=1.0, step=1.0)
            
            if st.button("💾 Proknjiži prodaju", type="primary"):
                if not broj_ponude.strip():
                    st.error("Greška: Trgovac mora upisati broj ponude prije skidanja s lagera!")
                else:
                    if kolicina_za_maknuti >= trenutna_kolicina:
                        updated_lager = df_lager[df_lager[naziv_c].astype(str) != puni_naziv_iz_selecta]
                    else:
                        df_lager.loc[df_lager[naziv_c].astype(str) == puni_naziv_iz_selecta, kolicina_c] = trenutna_kolicina - kolicina_za_maknuti
                        updated_lager = df_lager
                    
                    st.session_state["df_lager_local"] = updated_lager
                    st.success(f"Uspješno prodano! Ponuda: {broj_ponude}.")
                    st.rerun()

with tab_arhiva:
    st.header("📊 Pregled prodane robe")
    if df_arhiva.empty:
        st.info("Još nema zabilježene prodaje.")
    else:
        st.dataframe(df_arhiva, use_container_width=True)
