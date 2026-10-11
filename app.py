import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

# Konfiguracija za e-mail obavijesti (ovdje možeš kasnije upisati vaše SMTP postavke)
SMTP_SERVER = "smtp.yourserver.com"
SMTP_PORT = 587
SMTP_USER = "notifikacije@elgrad.hr"  
SMTP_PASS = "tvoja_lozinka" 
EMAIL_PRIMATELJ = "zeljko.marzluft@elgrad.hr"

# Spajanje na Google Sheets preko Streamlit konekcije
conn = st.connection("gsheets", type=GSheetsConnection)

# Učitavanje lagera
@st.cache_data(ttl=1)
def load_lager():
    return conn.read(worksheet="lager", ttl=1)

# Učitavanje arhive
@st.cache_data(ttl=1)
def load_arhiva():
    return conn.read(worksheet="arhiva", ttl=1)

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

# Učitavanje podataka
try:
    df_lager = load_lager()
except Exception as e:
    st.error(f"Greška pri spajanju na Google Sheet 'lager': {e}")
    st.stop()

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
    if search_query and "naziv" in filtered_df.columns:
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
                updated_df = pd.concat([df_lager, new_row], ignore_index=True)
                conn.update(worksheet="lager", data=updated_df)
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
                    # 1. Ažuriranje lagera
                    if kolicina_za_maknuti >= trenutna_kolicina:
                        updated_lager = df_lager[df_lager["naziv"].astype(str) != puni_naziv_iz_selecta]
                    else:
                        df_lager.loc[df_lager["naziv"].astype(str) == puni_naziv_iz_selecta, "predviđena količina"] = trenutna_kolicina - kolicina_za_maknuti
                        updated_lager = df_lager
                    
                    conn.update(worksheet="lager", data=updated_lager)
                    
                    # 2. Zapis u arhivu
                    try:
                        df_arhiva = load_arhiva()
                    except:
                        df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
                        
                    vrijeme_sada = datetime.now().strftime("%Y-%m-%d %H:%M")
                    nova_stavka_arhiva = pd.DataFrame({
                        "Datum": [vrijeme_sada],
                        "naziv": [puni_naziv_iz_selecta],
                        "količina": [kolicina_za_maknuti],
                        "JM": [jm_artikla],
                        "Broj Ponude": [broj_ponude]
                    })
                    updated_arhiva = pd.concat([df_arhiva, nova_stavka_arhiva], ignore_index=True)
                    conn.update(worksheet="arhiva", data=updated_arhiva)
                    
                    # 3. Slanje maila
                    posalji_email_obavijest(puni_naziv_iz_selecta, kolicina_za_maknuti, jm_artikla, broj_ponude)
                    
                    st.cache_data.clear()
                    st.success(f"Uspješno prodano! Ponuda: {broj_ponude}. Mail poslan.")
                    st.rerun()

with tab_arhiva:
    st.header("📊 Pregled prodane robe")
    try:
        df_arhiva_prikaz = load_arhiva()
        if df_arhiva_prikaz.empty:
            st.info("Još nema zabilježene prodaje.")
        else:
            q_ponuda = st.text_input("🔍 Pretraži po broju ponude:", "")
            if q_ponuda and "Broj Ponude" in df_arhiva_prikaz.columns:
                df_arhiva_prikaz = df_arhiva_prikaz[df_arhiva_prikaz["Broj Ponude"].astype(str).str.contains(q_ponuda, case=False, na=False)]
            st.dataframe(df_arhiva_prikaz, use_container_width=True)
    except Exception as e:
        st.info("Arhiva je trenutno prazna ili se učitava.")