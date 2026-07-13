import streamlit as st
import pandas as pd
from PIL import Image
import os
from datetime import datetime

# --- CONFIGURATION & DATABASE SETUP ---
KATASTER_FILE = "leitern_kataster.csv"

# Falls noch kein Kataster existiert, erstellen wir ein Start-Kataster
if not os.path.exists(KATASTER_FILE):
    df_init = pd.DataFrame(columns=[
        "Leiter-ID", "Typ", "Standort", "Letzte Prüfung", "Status", "Mangel-Details"
    ])
    # Ein paar Testdaten hinzufügen
    df_init.loc[0] = ["L-001", "Stehleiter Alu", "Halle A", "2026-01-10", "Bestanden", "Keine"]
    df_init.loc[1] = ["L-002", "Anlegeleiter Holz", "Lager West", "2025-11-15", "Defekt", "Sprosse angeknackst"]
    df_init.to_csv(KATASTER_FILE, index=False)

def load_data():
    return pd.read_csv(KATASTER_FILE)

def save_data(df):
    df.to_csv(KATASTER_FILE, index=False)

# --- SIMULIERTE KI-FUNKTION ---
# In der Realität würde hier dein trainiertes YOLO-Modell aufgerufen werden
def ki_defekt_erkennung(image):
    # Einfache Logik für den Prototyp: Wir "simulieren" die KI anhand des Bildes
    # (In der echten App analysiert das Modell hier Pixelstrukturen)
    import random
    ist_defekt = random.choice([True, False])
    if ist_defekt:
        return "Defekt", "KI-Analyse: Möglicher Riss an der Holm-Sprossen-Verbindung erkannt! (Konfidenz: 89%)"
    else:
        return "Bestanden", "KI-Analyse: Keine sichtbaren Mängel gefunden."

# --- APP UI ---
st.set_page_config(page_title="LeiterPrüf Pro", page_icon="??", layout="centered")

st.title("?? LeiterPrüf Pro")
st.caption("Digitales Prüf-Kataster & KI-Defekterkennung")

# Laden der Daten
df_kataster = load_data()

# Navigation in der App
menu = ["Prüfung durchführen", "Digitales Kataster"]
choice = st.sidebar.selectbox("Menü", menu)

# --- REITER 1: PRÜFUNG DURCHFÜHREN ---
if choice == "Prüfung durchführen":
    st.header("?? Neue Leiterprüfung")
    
    # 1. Identifikation der Leiter
    leiter_id = st.text_input("Leiter-ID eingeben (oder QR-Code scannen):", placeholder="z.B. L-001")
    
    # Falls die Leiter existiert, zeigen wir die alten Daten an
    leiter_existiert = leiter_id in df_kataster["Leiter-ID"].values
    if leiter_existiert:
        aktuelle_daten = df_kataster[df_kataster["Leiter-ID"] == leiter_id].iloc[0]
        st.info(f"Gefundene Leiter: **{aktuelle_daten['Typ']}** am Standort **{aktuelle_daten['Standort']}**")
    elif leiter_id:
        st.warning("Neue Leiter-ID erkannt. Beim Speichern wird eine neue Leiter im Kataster angelegt.")
        neuer_typ = st.text_input("Leitertyp (z.B. Stehleiter 8 Sprossen):")
        neuer_standort = st.text_input("Standort (z.B. Werkstatt):")

    st.write("---")
    
    # 2. Foto aufnehmen / hochladen
    st.subheader("?? Foto für KI-Analyse aufnehmen")
    img_file = st.camera_input("Kamera öffnen") # Aktiviert die Smartphone-/Webcam-Kamera
    
    # Falls keine Kamera da ist, erlauben wir alternativ einen Upload
    if img_file is None:
        img_file = file_upload = st.file_uploader("Oder Foto hochladen", type=["jpg", "png", "jpeg"])

    if img_file is not None and leiter_id:
        image = Image.open(img_file)
        st.image(image, caption="Aufgenommenes Foto", use_column_width=True)
        
        # KI-Button
        if st.button("?? KI-Analyse starten"):
            with st.spinner("KI analysiert das Foto auf Beschädigungen..."):
                status, details = ki_defekt_erkennung(image)
                
            # Ergebnis anzeigen
            if status == "Bestanden":
                st.success(f"?? {status}")
            else:
                st.error(f"?? {status}")
            st.write(f"**Details:** {details}")
            
            # 3. Daten im Kataster aktualisieren / Speichern
            if leiter_existiert:
                df_kataster.loc[df_kataster["Leiter-ID"] == leiter_id, "Letzte Prüfung"] = datetime.now().strftime("%Y-%m-%d")
                df_kataster.loc[df_kataster["Leiter-ID"] == leiter_id, "Status"] = status
                df_kataster.loc[df_kataster["Leiter-ID"] == leiter_id, "Mangel-Details"] = details
            else:
                new_row = {
                    "Leiter-ID": leiter_id,
                    "Typ": neuer_typ if 'neuer_typ' in locals() else "Unbekannt",
                    "Standort": neuer_standort if 'neuer_standort' in locals() else "Unbekannt",
                    "Letzte Prüfung": datetime.now().strftime("%Y-%m-%d"),
                    "Status": status,
                    "Mangel-Details": details
                }
                df_kataster = pd.concat([df_kataster, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df_kataster)
            st.toast("Daten erfolgreich im Kataster gespeichert!")

# --- REITER 2: DIGITALES KATASTER ---
elif choice == "Digitales Kataster":
    st.header("?? Leiter-Kataster (Übersicht)")
    
    # Filter-Optionen
    status_filter = st.multiselect("Filtern nach Status:", options=["Bestanden", "Defekt"], default=["Bestanden", "Defekt"])
    
    filtered_df = df_kataster[df_kataster["Status"].isin(status_filter)]
    
    # Tabelle anzeigen
    st.dataframe(filtered_df, use_container_width=True)
    
    # Statistik
    st.write("---")
    st.subheader("?? Statistik")
    gesamt = len(df_kataster)
    defekt = len(df_kataster[df_kataster["Status"] == "Defekt"])
    
    col1, col2 = st.columns(2)
    col1.metric("Leitern Gesamt", gesamt)
    col2.metric("Aktuell Defekt", defekt, delta=f"{defekt/gesamt*100:.1f}% aller Leitern", delta_color="inverse")
