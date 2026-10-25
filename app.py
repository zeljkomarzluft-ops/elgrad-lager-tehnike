import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

# Spajanje na Supabase koristeći Secrets
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SMTP postavke iz Secrets
SMTP_SERVER = st.secrets["smtp"]["server"] if "smtp" in st.secrets else "smtp.gmail.com"
SMTP_PORT = int(st.secrets["smtp"]["port"]) if "smtp" in st.secrets else 587
SMTP_USER = st.secrets["smtp"]["user"] if "smtp" in st.secrets else ""
SMTP_PASS = st.secrets["smtp"]["password"] if "smtp" in st.secrets else ""
EMAIL_PRIMATELJ = st.secrets["smtp"]["recipient"] if "smtp" in st.secrets else "zeljko.marzluft@elgrad.hr"

def load_data():
    # Dohvat lagera iz Supabase
    response_lager = supabase.table("lager").select("*").execute()
    df_lager = pd.DataFrame(response_lager.data)
    
    if not df_lager.empty:
        # Preimenovanje stupaca da odgovaraju aplikaciji ako je potrebno
        if "predvidena_kolicina" in df_lager.columns:
            df_lager = df_lager.rename(columns={
                "naziv": "Naziv",
                "predvidena_kolicina": "Predviđena količina",
                "jm": "JM",
                "kategorija": "Kategorija"
            })
    else:
        df_lager = pd.DataFrame(columns=["Naziv", "Predviđena količina", "JM", "Kategorija"])

    # Dohvat arhive iz Supabase
    response_arhiva = supabase.table("arhiva_prodaje").select("*").execute()
    df_arhiva = pd.DataFrame(response_arhiva.data)
    
    if not df_arhiva.empty:
        df_arhiva = df_arhiva.rename(columns={
            "datum": "Datum",
            "naziv": "naziv",
            "kolicina": "količina",
            "jm": "JM",
            "broj_ponude": "Broj Ponude"
        })
        # Maknuti suvišni ID stupac iz prikaza ako postoji
        if "id" in df_arhiva.columns:
            df_arhiva = df_arhiva.drop(columns=["id"])
    else:
        df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
        
    return df_lager, df_arhiva

def posalji_email_obavijest(naziv_artikla, kolicina, jm, broj_ponude):
    if not SMTP_USER or not SMTP_PASS:
        return False
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

tab_pregled, tab_dodaj, tab_arhiva = st.tabs([
    "📋 Pregled i Prodaja Lagera", 
    "➕ Dodaj Artikal (Admin)", 
    "📊 Arhiva Prodaje"
])

with tab_pregled:
    st.header("Slobodno na lageru i prodaja")
    search_query = st.text_input("🔍 Pretraži po nazivu ili šifri:", "", key="search_pregled")
    
    filtered_df = df_lager.copy()
    # Ukloni ID iz prikaza ako postoji
    if "id" in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=["id"])
        
    if search_query and not filtered_df.empty:
        naziv_col = "Naziv" if "Naziv" in filtered_df.columns else filtered_df.columns[0]
        filtered_df = filtered_df[
            filtered_df[naziv_col].astype(str).str.contains(search_query, case=False, na=False)
        ]
    
    filtered_df.insert(0, "Prodaj", False)
    
    edited_df = st.data_editor(
        filtered_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={"Prodaj": st.column_config.CheckboxColumn("Odaberi za prodaju", required=True)}
    )
    
    odabrani_redci = edited_df[edited_df["Prodaj"] == True]
    
    if not odabrani_redci.empty:
        st.markdown("---")
        st.subheader("🛒 Dovršetak prodaje za odabrani artikal")
        
        puni_naziv = odabrani_redci.iloc[0]["Naziv"]
        originalni_red = df_lager[df_lager["Naziv"].astype(str) == str(puni_naziv)].iloc[0]
        
        # Dohvati ID retka u bazi za ažuriranje/brisanje
        artikal_id = originalni_red["id"] if "id" in originalni_red else None
        trenutna_kolicina = float(originalni_red["Predviđena količina"])
        jm_artikla = str(originalni_red["JM"])
        
        st.info(f"Odabran artikal: **{puni_naziv}** (Dostupno: {trenutna_kolicina} {jm_artikla})")
        
        col1, col2 = st.columns(2)
        with col1:
            kolicina_za_maknuti = st.number_input(f"Količina za skinuti ({jm_artikla}):", min_value=0.5, max_value=max(0.5, trenutna_kolicina), value=1.0, step=1.0)
        with col2:
            broj_ponude = st.text_input("📝 Broj ponude / računa (Obavezno):", key="input_ponuda_pregled")
            
        if st.button("🚀 Proknjiži prodaju", type="primary"):
            if not broj_ponude.strip():
                st.error("Greška: Unesi broj ponude prije knjiženja!")
            else:
                # Ažuriranje baze (Supabase)
                if kolicina_za_maknuti >= trenutna_kolicina:
                    if artikal_id:
                        supabase.table("lager").delete().eq("id", artikal_id).execute()
                else:
                    nova_kol = trenutna_kolicina - kolicina_za_maknuti
                    if artikal_id:
                        supabase.table("lager").update({"predvidena_kolicina": nova_kol}).eq("id", artikal_id).execute()
                
                vrijeme_sada = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Zapis u arhivu u Supabase
                supabase.table("arhiva_prodaje").insert({
                    "datum": vrijeme_sada,
                    "naziv": puni_naziv,
                    "kolicina": kolicina_za_maknuti,
                    "jm": jm_artikla,
                    "broj_ponude": broj_ponude
                }).execute()
                
                posalji_email_obavijest(puni_naziv, kolicina_za_maknuti, jm_artikla, broj_ponude)
                
                st.cache_data.clear()
                st.success(f"Uspješno proknjiženo za ponudu br. {broj_ponude}! E-mail obavijest poslana.")
                st.rerun()

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
                # Spremanje novog artikla u Supabase
                supabase.table("lager").insert({
                    "naziv": novi_naziv,
                    "predvidena_kolicina": nova_kolicina,
                    "jm": nova_jm,
                    "kategorija": nova_kategorija
                }).execute()
                
                st.cache_data.clear()
                st.success("Uspješno dodano na lager u bazu!")
                st.rerun()

with tab_arhiva:
    st.header("📊 Pregled prodane robe")
    if df_arhiva.empty:
        st.info("Još nema zabilježene prodaje.")
    else:
        st.dataframe(df_arhiva, use_container_width=True)
