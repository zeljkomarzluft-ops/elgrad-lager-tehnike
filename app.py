import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(page_title="Upravljanje Lagerom - Elgrad Pula", layout="wide")

SMTP_SERVER = "smtp.yourserver.com"
SMTP_PORT = 587
SMTP_USER = "notifikacije@elgrad.hr"  
SMTP_PASS = "tvoja_lozinka" 
EMAIL_PRIMATELJ = "zeljko.marzluft@elgrad.hr"

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
    {"Naziv": "[RO20802777] FRANKE inox krema 250 gr.", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Ostalo"},
    {"Naziv": "[RO20802783] PIPA FRANKE NOVARA PLUS krom", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20820368] SUDOPER ELLECI EASY 300 NERO", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20820618] ELLECI potiskivač otpada", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20820680] Sudoper SHR Lines 30", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20820691] ELLECI koljeno izljeva", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20852044] NAPA FABER Inka Smart HCS X A52", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20852049] Napa Faber Inka Smart C LG A52", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20853178] Set Cadit 40 G91 + Delos-P G91", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20853183] PIPA ALVEUS armatura ROXA CHR - G81", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20853257] DOZATOR DETERDŽENTA CALLAS 0,32L CHR", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Ostalo"},
    {"Naziv": "[RO20857125] PIPA ALVEUS ZINA CHR-G05M", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO20864050] LIEBHERR ugradbeni hladnjak ICBb 5152 - Prime Line", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20873231] BOSCH Kombinirana ploča za kuhanje, nehrđajući čelik", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20889113] Ugradbeni Hladnjak SMEG C8175TNE, No Frost", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20889116] Ugradbena ploča SMEG SI4642D Universal, indukcija", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20889117] Ugradbena perilica posuda SMEG STL362DQ", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20889378] FABER UGLJENI FILTER Ugljeni filter VRT, TSPG, TGL, TSP", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO21728422] PIPA FRANKE LINA-XL GRAFIT", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO21728457] FRANKE SUDOPER SMART SRX 620-86", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO21758697] Sudoper FRANKE Maris Quiet MQX 110-82, inox", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853297] PIPA ALVEUS Swan Monarch, copper", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Pipe"},
    {"Naziv": "[RO22853371] ALVEUS SET Sudoper Cadit 20 A90 black edition + Pipa Jana black matte + Gratis AllRound black", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853372] ALVEUS SET Sudoper Atrox 30 A90 black edition + Pipa Jana black matte + Gratis AllRound black", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853378] Sudoper ALVEUS Cadit 100 A91 Carbon", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853385] Sudoper ALVEUS Cadit 40 A90 BLACK EDITION", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853396] Sudoper ALVEUS Elegant 110, inox", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO22853401] Sudoper ALVEUS Pure-G 70 D A20 Ivory", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO25512835] Napa FABER Flexa NG BK A60, crna", "Predviđena količina": 1.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20551663] Faber F23 - Ugljeni filter Inka Smart C-HC-HCS", "Predviđena količina": 2.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20820029] SUDOPER AQUASANITA-HELIKA ECO 2 crni", "Predviđena količina": 2.0, "JM": "kom", "Kategorija": "Sudoperi"},
    {"Naziv": "[RO20551302] FABER UGLJENI FILTER F8 BELLE, COCKTAIL, MAXIMA, SYNTHESIS, CUBIA, DAISY, LITHOS (par)", "Predviđena količina": 3.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO20551548] Faber ugljeni filter F3 Flexa Glass lux- Hip, Value, Intra (par)", "Predviđena količina": 5.0, "JM": "kom", "Kategorija": "Tehnika"},
    {"Naziv": "[RO22853368] ALVEUS kruna za bušenje sudopera 35mm", "Predviđena količina": 17.0, "JM": "kom", "Kategorija": "Ostalo"}
]

@st.cache_data(ttl=1)
def load_data():
    if os.path.exists(LAGER_FILE):
        try:
            df_lager = pd.read_csv(LAGER_FILE)
            df_lager.columns = df_lager.columns.str.strip()
            if df_lager.empty:
                df_lager = pd.DataFrame(POZNATI_ARTIKLI)
        except:
            df_lager = pd.DataFrame(POZNATI_ARTIKLI)
    else:
        df_lager = pd.DataFrame(POZNATI_ARTIKLI)
        df_lager.to_csv(LAGER_FILE, index=False)
        
    if os.path.exists(ARHIVA_FILE):
        try:
            df_arhiva = pd.read_csv(ARHIVA_FILE)
            df_arhiva.columns = df_arhiva.columns.str.strip()
        except:
            df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
    else:
        df_arhiva = pd.DataFrame(columns=["Datum", "naziv", "količina", "JM", "Broj Ponude"])
        
    return df_lager, df_arhiva

def save_data(df_lager, df_arhiva):
    df_lager.to_csv(LAGER_FILE, index=False)
    df_arhiva.to_csv(ARHIVA_FILE, index=False)

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

tab_pregled, tab_dodaj, tab_arhiva = st.tabs([
    "📋 Pregled i Prodaja Lagera", 
    "➕ Dodaj Artikal (Admin)", 
    "📊 Arhiva Prodaje"
])

with tab_pregled:
    st.header("Slobodno na lageru i prodaja")
    search_query = st.text_input("🔍 Pretraži po nazivu ili šifri:", "", key="search_pregled")
    
    filtered_df = df_lager.copy()
    if search_query and not filtered_df.empty:
        naziv_col = filtered_df.columns[0]
        filtered_df = filtered_df[
            filtered_df[naziv_col].astype(str).str.contains(search_query, case=False, na=False)
        ]
    
    # Dodajemo stupac za odabir u tablicu
    filtered_df.insert(0, "Prodaj", False)
    
    edited_df = st.data_editor(
        filtered_df, 
        use_container_width=True, 
        hide_index=True,
        column_config={"Prodaj": st.column_config.CheckboxColumn("Odaberi za prodaju", required=True)}
    )
    
    # Pronađi koji je artikal označen kvačicom
    odabrani_redci = edited_df[edited_df["Prodaj"] == True]
    
    if not odabrani_redci.empty:
        st.markdown("---")
        st.subheader("🛒 Dovršetak prodaje za odabrani artikal")
        
        cols = df_lager.columns.tolist()
        naziv_c = cols[0]
        kolicina_c = cols[1] if len(cols) > 1 else cols[0]
        jm_c = cols[2] if len(cols) > 2 else cols[0]
        
        puni_naziv = odabrani_redci.iloc[0][naziv_c]
        originalni_red = df_lager[df_lager[naziv_c].astype(str) == str(puni_naziv)].iloc[0]
        trenutna_kolicina = float(originalni_red[kolicina_c])
        jm_artikla = str(originalni_red[jm_c])
        
        st.info(Odabran artikal: **{puni_naziv}** (Dostupno: {trenutna_kolicina} {jm_artikla}))
        
        col1, col2 = st.columns(2)
        with col1:
            kolicina_za_maknuti = st.number_input(f"Količina za skinuti ({jm_artikla}):", min_value=0.5, max_value=max(0.5, trenutna_kolicina), value=1.0, step=1.0)
        with col2:
            broj_ponude = st.text_input("📝 Broj ponude / računa (Obavezno):", key="input_ponuda_pregled")
            
        if st.button("🚀 Proknjiži prodaju", type="primary"):
            if not broj_ponude.strip():
                st.error("Greška: Unesi broj ponude prije knjiženja!")
            else:
                if kolicina_za_maknuti >= trenutna_kolicina:
                    updated_lager = df_lager[df_lager[naziv_c].astype(str) != str(puni_naziv)]
                else:
                    df_lager.loc[df_lager[naziv_c].astype(str) == str(puni_naziv), kolicina_c] = trenutna_kolicina - kolicina_za_maknuti
                    updated_lager = df_lager
                
                vrijeme_sada = datetime.now().strftime("%Y-%m-%d %H:%M")
                nova_stavka_arhiva = pd.DataFrame({
                    "Datum": [vrijeme_sada],
                    "naziv": [puni_naziv],
                    "količina": [kolicina_za_maknuti],
                    "JM": [jm_artikla],
                    "Broj Ponude": [broj_ponude]
                })
                updated_arhiva = pd.concat([df_arhiva, nova_stavka_arhiva], ignore_index=True)
                
                save_data(updated_lager, updated_arhiva)
                posalji_email_obavijest(puni_naziv, kolicina_za_maknuti, jm_artikla, broj_ponude)
                
                st.cache_data.clear()
                st.success(f"Uspješno proknjiženo za ponudu br. {broj_ponude}! Mail poslan.")
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
