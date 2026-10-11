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

# Glavni link tvog Google Sheeta
SHEET_URL = "https://docs.google.com/spreadsheets/d/1NzbUwGxIYuK0bTRTdJ_1903gju30pd4AG41LZpMq0KM/edit?usp=sharing"

# Pretvaranje običnog linka u direktni CSV link za čitanje
def get_csv_url(sheet_url, sheet_name):
    base_id = sheet_url.split("/d/")[1].split("/")[0]
    return f"https://docs.google.com/spreadsheets/d/{base_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

@st.cache_data(ttl=1)
def load_data():
    try:
        url_lager = get_csv_url(SHEET_URL, "lager")
        df_lager = pd.read_csv(url_lager)
        # Očistimo nazive stupaca od suvišnih razmaka
        df_lager.columns = df_lager.columns.str.strip()
    except Exception as e:
        df_lager = pd.DataFrame(columns=["naziv", "predviđena količina", "JM", "Kategorija"])
        
    try:
        url_arhiva = get_csv_url(SHEET_URL, "arhiva")
        df_arhiva = pd.read_csv(url_arhiva)
        df_arhiva.columns = df_arhiva.columns.str.strip()
    except Exception as e:
        df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
        
    return df_lager, df_arhiva

# Pomoćna funkcija za spajanje preko gspread-a samo za upis/ažuriranje
def get_gspread_worksheet(tab_name):
    gc = gspread.no_service_account() if hasattr(gspread, 'no_service_account') else gspread.Client(auth=None)
    sh = gspread.open_by_url(SHEET_URL)
    return sh.worksheet(tab_name)

def save_to_sheet(df_lager, df_arhiva):
    ws_lager = get_gspread_worksheet("lager")
    ws_lager.clear()
    ws_lager.update([df_lager.columns.values.tolist()] + df_lager.values.tolist())
    
    ws_arhiva = get_gspread_worksheet("arhiva")
    ws_arhiva.clear()
    ws_arhiva.update([df_arhiva.columns.values.tolist()] + df_arhiva.values.tolist())

def posalji_email_obavijest(naziv_artikla, kolicina, jm, broj_ponude):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = EMAIL_PRIMATELJ
        msg['Subject'] = f"📦 Prodaja s lagera - Ponuda br. {broj_ponude}"

        body = f"""
        Pozdrav Željko,

        Upravo je proknjižena prodaja artikla sa slobodnog lagera:

        - Artikal: {naziv_artikla}
        - Količina: {kolicina} {jm}
        - Broj ponude: {broj_ponude}
        - Vrijeme: {datetime.now().strftime("%Y-%m-%d %H:%M")}

        Ova poruka je automatski generirana iz aplikacije.
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_PRIMATELJ, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Greška kod slanja maila: {e}")
        return False

df_lager, df_arhiva = load_data()

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
    if search_query and not filtered_df.empty and "naziv" in filtered_df.columns:
        filtered_df = filtered_df[
            filtered_df["naziv"].astype(str).str.contains(search_query, case=False, na=False)
        ]
    st.dataframe(filtered_df, use_container_width=True)

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
                new_row = pd.DataFrame({
                    "naziv": [novi_naziv], 
                    "predviđena količina": [nova_kolicina], 
                    "JM": [nova_jm], 
                    "Kategorija": [nova_kategorija]
                })
                updated_lager = pd.concat([df_lager, new_row], ignore_index=True)
                save_to_sheet(updated_lager, df_arhiva)
                st.cache_data.clear()
                st.success("Uspješno dodano na lager!")
                st.rerun()

with tab_prodaja:
    st.header("Evidencija prodaje i razduženje")
    if df_lager.empty:
        st.warning("Lager je prazan.")
    else:
        opcije_artikala = df_lager.apply(lambda row: f"{row['naziv']} (Dostupno: {row['predviđena količina']} {row['JM']})", axis=1).tolist()
        odabrani_artikal = st.selectbox("Izaberi prodani artikal:", opcije_artikala)
        
        broj_ponude = st.text_input("📝 Unesi broj ponude / računa (Obavezno):")
        
        if odabrani_artikal:
            puni_naziv_iz_selecta = odabrani_artikal.split(" (Dostupno:")[0]
            red_artikla = df_lager[df_lager["naziv"].astype(str) == puni_naziv_iz_selecta].iloc[0]
            trenutna_kolicina = float(red_artikla["predviđena količina"])
            jm_artikla = str(red_artikla["JM"])
            
            kolicina_za_maknuti = st.number_input(f"Količina za maknuti ({jm_artikla}):", min_value=0.5, max_value=max(0.5, trenutna_kolicina), value=1.0, step=1.0)
            
            if st.button("💾 Proknjiži prodaju i pošalji obavijest", type="primary"):
                if not broj_ponude.strip():
                    st.error("Greška: Trgovac mora upisati broj ponude prije skidanja s lagera!")
                else:
                    if kolicina_za_maknuti >= trenutna_kolicina:
                        updated_lager = df_lager[df_lager["naziv"].astype(str) != puni_naziv_iz_selecta]
                    else:
                        df_lager.loc[df_lager["naziv"].astype(str) == puni_naziv_iz_selecta, "predviđena količina"] = trenutna_kolicina - kolicina_za_maknuti
                        updated_lager = df_lager
                    
                    vrijeme_sada = datetime.now().strftime("%Y-%m-%d %H:%M")
                    nova_stavka_arhiva = pd.DataFrame({
                        "Datum": [vrijeme_sada],
                        "naziv": [puni_naziv_iz_selecta],
                        "količina": [kolicina_za_maknuti],
                        "JM": [jm_artikla],
                        "Broj Ponude": [broj_ponude]
                    })
                    updated_arhiva = pd.concat([df_arhiva, nova_stavka_arhiva], ignore_index=True)
                    
                    save_to_sheet(updated_lager, updated_arhiva)
                    posalji_email_obavijest(puni_naziv_iz_selecta, kolicina_za_maknuti, jm_artikla, broj_ponude)
                    
                    st.cache_data.clear()
                    st.success(f"Uspješno prodano! Ponuda: {broj_ponude}. Mail poslan.")
                    st.rerun()

with tab_arhiva:
    st.header("📊 Pregled prodane robe")
    if df_arhiva.empty:
        st.info("Još nema zabilježene prodaje.")
    else:
        q_ponuda = st.text_input("🔍 Pretraži po broju ponude:", "")
        filtered_arhiva = df_arhiva.copy()
        if q_ponuda and "Broj Ponude" in filtered_arhiva.columns:
            filtered_arhiva = filtered_arhiva[filtered_arhiva["Broj Ponude"].astype(str).str.contains(q_ponuda, case=False, na=False)]
        st.dataframe(filtered_arhiva, use_container_width=True)
