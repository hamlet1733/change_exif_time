import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import piexif
from datetime import datetime, timedelta
import threading

ordnerpfad_global = None  # globaler Speicher für gewählten Ordner

def verarbeite_bilder(ordnerpfad, minuten_offset, kameramodell):
    dateien = [f for f in os.listdir(ordnerpfad) if f.lower().endswith(".jpg")]
    gesamt = len(dateien)
    bearbeitet = 0
    fehlerhaft = 0

    progressbar["maximum"] = gesamt
    progressbar["value"] = 0
    status_label.config(text=f"Starte Verarbeitung von {gesamt} Dateien...")
    fenster.update_idletasks()

    for i, dateiname in enumerate(dateien):
        bildpfad = os.path.join(ordnerpfad, dateiname)
        try:
            exif_dict = piexif.load(bildpfad)

            # Kameramodell prüfen (falls angegeben)
            if kameramodell:
                model_bytes = exif_dict["0th"].get(piexif.ImageIFD.Model)
                if not model_bytes:
                    continue
                model_str = model_bytes.decode("utf-8").strip()
                if kameramodell.strip().lower() not in model_str.lower():
                    continue

            alte_zeit_bytes = exif_dict["Exif"].get(piexif.ExifIFD.DateTimeOriginal)
            if not alte_zeit_bytes:
                fehlerhaft += 1
                continue

            alte_zeit_str = alte_zeit_bytes.decode("utf-8")
            alte_zeit = datetime.strptime(alte_zeit_str, "%Y:%m:%d %H:%M:%S")
            neue_zeit = alte_zeit + timedelta(minutes=minuten_offset)
            neue_zeit_str = neue_zeit.strftime("%Y:%m:%d %H:%M:%S")

            # EXIF-Zeit aktualisieren
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = neue_zeit_str.encode("utf-8")
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = neue_zeit_str.encode("utf-8")
            exif_dict["0th"][piexif.ImageIFD.DateTime] = neue_zeit_str.encode("utf-8")

            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, bildpfad)

            bearbeitet += 1

        except Exception as e:
            fehlerhaft += 1
            print(f"Fehler bei {dateiname}: {e}")

        progressbar["value"] = i + 1
        status_label.config(text=f"{i+1}/{gesamt} verarbeitet...")
        fenster.update_idletasks()

    messagebox.showinfo("Fertig!", f"{bearbeitet} Bilder erfolgreich aktualisiert.\n{fehlerhaft} Fehlerhafte Dateien.")
    start_button.config(state="normal")
    status_label.config(text="Verarbeitung abgeschlossen.")

def ordner_waehlen():
    global ordnerpfad_global
    ordnerpfad_global = filedialog.askdirectory()
    if ordnerpfad_global:
        status_label.config(text=f"Ordner gewählt: {ordnerpfad_global}")

def start_verarbeitung():
    global ordnerpfad_global
    if not ordnerpfad_global:
        messagebox.showwarning("Kein Ordner", "Bitte zuerst einen Ordner wählen!")
        return
    start_button.config(state="disabled")
    minuten_offset = zeit_offset.get()
    kameramodell = kamera_model.get().strip()
    threading.Thread(target=verarbeite_bilder, args=(ordnerpfad_global, minuten_offset, kameramodell), daemon=True).start()

def cancel_fenster():
    fenster.destroy()  # Fenster schließen

# GUI erstellen
fenster = tk.Tk()
fenster.title("EXIF-Zeit verschieben (verlustfrei)")
fenster.geometry("420x320")

label = tk.Label(fenster, text="Wähle einen Ordner mit JPG-Bildern:")
label.pack(pady=10)

ordner_button = tk.Button(fenster, text="Ordner wählen", command=ordner_waehlen)
ordner_button.pack(pady=5)

tk.Label(fenster, text="Zeitverschiebung in Minuten:").pack(pady=5)
zeit_offset = tk.IntVar(value=60)
tk.Entry(fenster, textvariable=zeit_offset, width=10).pack(pady=5)

tk.Label(fenster, text="Optional: Kameramodell filtern").pack(pady=5)
kamera_model = tk.StringVar()
tk.Entry(fenster, textvariable=kamera_model, width=25).pack(pady=5)

# Start/Cancel Buttons unterhalb des Kamera-Eingabefelds
start_button = tk.Button(fenster, text="Start", command=start_verarbeitung)
start_button.pack(pady=5)

cancel_button = tk.Button(fenster, text="Cancel", command=cancel_fenster)
cancel_button.pack(pady=5)

progressbar = ttk.Progressbar(fenster, orient="horizontal", length=340, mode="determinate")
progressbar.pack(pady=10)

status_label = tk.Label(fenster, text="Bereit")
status_label.pack(pady=5)

fenster.mainloop()
