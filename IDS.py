import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
pd.set_option("display.max_columns", None)
import openpyxl
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog
import threading
import time

def tekil_degerler(satirlar, sutun):
    return set([satir[sutun] for satir in satirlar])

def sinif_sayilari(satirlar):
    sayimlar = {} 
    for satir in satirlar:
        etiket = satir[-1]
        if etiket not in sayimlar:
            sayimlar[etiket] = 0
        sayimlar[etiket] += 1
    return sayimlar

def sayisal_mi(deger):
    return isinstance(deger, int) or isinstance(deger, float)

class Soru:
    def __init__(self, sutun, deger):
        self.sutun = sutun
        self.deger = deger

    def eslesiyor_mu(self, ornek):
        deger = ornek[self.sutun]
        if sayisal_mi(deger):
            return deger >= self.deger
        else:
            return deger == self.deger

def bolumle(satirlar, soru):
    dogru_satirlar, yanlis_satirlar = [], []
    for satir in satirlar:
        if soru.eslesiyor_mu(satir):
            dogru_satirlar.append(satir)
        else:
            yanlis_satirlar.append(satir)
    return dogru_satirlar, yanlis_satirlar

def gini(satirlar):
    sayimlar = sinif_sayilari(satirlar)
    saflik = 1
    for lbl in sayimlar:
        etiket_olasiligi = sayimlar[lbl] / float(len(satirlar))
        saflik -= etiket_olasiligi**2
    return saflik

def bilgi_kazanci(sol, sag, mevcut_belirsizlik):
    p = float(len(sol)) / (len(sol) + len(sag))
    return mevcut_belirsizlik - p * gini(sol) - (1 - p) * gini(sag)

def en_iyi_bolumlemeyi_bul(satirlar):
    en_iyi_kazanc = 0  
    en_iyi_soru = None  
    mevcut_belirsizlik = gini(satirlar)
    n_ozellikler = len(satirlar[0]) - 1 

    for sutun in range(n_ozellikler):  
        degerler = set([satir[sutun] for satir in satirlar]) 
        for deger in degerler: 
            soru = Soru(sutun, deger)

            dogru_satirlar, yanlis_satirlar = bolumle(satirlar, soru)

            if len(dogru_satirlar) == 0 or len(yanlis_satirlar) == 0:
                continue

            kazanc = bilgi_kazanci(dogru_satirlar, yanlis_satirlar, mevcut_belirsizlik)

            if kazanc >= en_iyi_kazanc:
                en_iyi_kazanc, en_iyi_soru = kazanc, soru

    return en_iyi_kazanc, en_iyi_soru

class Yaprak:
    def __init__(self, satirlar):
        self.tahminler = sinif_sayilari(satirlar)

class Karar_Dugumu:
    def __init__(self,
                 soru,
                 dogru_dal,
                 yanlis_dal):
        self.soru = soru
        self.dogru_dal = dogru_dal
        self.yanlis_dal = yanlis_dal

def agac_olustur(satirlar):
    kazanc, soru = en_iyi_bolumlemeyi_bul(satirlar)
    if kazanc == 0:
        return Yaprak(satirlar)
    
    dogru_satirlar, yanlis_satirlar = bolumle(satirlar, soru)

    dogru_dal = agac_olustur(dogru_satirlar)
    yanlis_dal = agac_olustur(yanlis_satirlar)

    return Karar_Dugumu(soru, dogru_dal, yanlis_dal)

def siniflandir(satir, dugum):
    if isinstance(dugum, Yaprak):
        return dugum.tahminler

    if dugum.soru.eslesiyor_mu(satir):
        return siniflandir(satir, dugum.dogru_dal)
    else:
        return siniflandir(satir, dugum.yanlis_dal)
    
  
sonuclar = defaultdict(list)

df = pd.read_pickle('dataset-dtree.pkl')
df = df.sample(frac=1).reset_index(drop=True)

# Büyük veri setinde eğitim yapmak zaman alır, bu nedenle eğitim setini azaltıyoruz
egitim_verisi = df.iloc[:10000, :].values.tolist()
benim_agacim = agac_olustur(egitim_verisi)


file_path = ""  # global olarak tanımladık

def select_file():
    global file_path  
    file_path = filedialog.askopenfilename(filetypes=[("Veri Seti", "*.xlsx"), ("All Files", "*.*")])
    # Seçilen dosya ile yapmak istediğiniz işlemleri gerçekleştirin
    console_text.insert(tk.END, f"Seçilen dosya: {file_path}\n")
    console_text.see(tk.END)  # Konsolu otomatik olarak aşağı kaydır


def perform_analysis():
    global file_path  
    global rapor
    rapor = []
    if file_path:
        test_verisi = pd.read_excel(file_path)
        sonuclar = []
        for index, satir in test_verisi.iterrows():
            sonuc = sorted(siniflandir(satir, benim_agacim).items(), key=lambda x: x[1], reverse=True)[0][0]
            sonuclar.append(sonuc)
        # Sonuçları yazdırın
        for i in range(len(test_verisi)):
            if sonuclar[i] == 0:
                normal_count = int(normal_counter["text"])
                normal_count += 1
                normal_counter.config(text=str(normal_count))

                # Çeyrek saniye (0.25 saniye) bekleme
                time.sleep(0.25)

            else:
                malware_count = int(malware_counter["text"])
                malware_count += 1
                malware_counter.config(text=str(malware_count))        
                console_text.insert(tk.END, f"Zararlı Olarak Analiz Edildi {test_verisi.iloc[i].values.tolist()}\n")

                rapor.append(test_verisi.iloc[i].values.tolist())

                time.sleep(0.25)
 
        # Analiz işlemini gerçekleştirin
        console_text.insert(tk.END, "Analiz işlemi gerçekleştirildi.\n")
    else:
        console_text.insert(tk.END, "Lütfen önce bir dosya seçin.\n")
    console_text.see(tk.END)  # Konsolu otomatik olarak aşağı kaydır

def perform_analysis_thread():
    analysis_thread = threading.Thread(target=perform_analysis)
    analysis_thread.start()

def save_report():
    file_path = filedialog.asksaveasfilename(title="Raporu Kaydet", defaultextension=".xlsx", filetypes=[("Rapor", "*.xlsx")])
    if file_path:
        with open(file_path, "w") as file:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            
        for row_idx, row_data in enumerate(rapor, start=1):
            for col_idx, cell_data in enumerate(row_data, start=1):
                sheet.cell(row=row_idx, column=col_idx, value=cell_data)

        workbook.save(file_path)

        print("Metin Dosyası Kaydedildi:", file_path)

def clear_console():
    console_text.delete('1.0', tk.END)
    normal_counter.config(text="0")
    malware_counter.config(text="0")

# Ana Tkinter penceresini oluşturun
window = tk.Tk()

# Pencere başlığını ayarlayın
window.title("Dosya Analizi")

# Pencere arkaplan rengini beyaz yapın
window.configure(background="white")

# Ekranı kaplamak için pencerenin boyutunu ve konumunu ayarlayın
window.geometry("{0}x{1}+0+0".format(window.winfo_screenwidth(), window.winfo_screenheight()))

# Ana çerçeveyi oluşturun
main_frame = tk.Frame(window, padx=20, pady=20, bg="white")
main_frame.pack()

# Analiz durumu panelini oluşturun
status_panel = tk.Frame(main_frame, pady=10, bg="white")
status_panel.pack()

# Zararlı Yazılım sayaç etiketi
malware_label = tk.Label(status_panel, text="Zararlı Paket:", font=("Arial", 14, "bold"), bg="white")
malware_label.grid(row=0, column=0, padx=5)

# Zararlı Yazılım sayaç
malware_counter = tk.Label(status_panel, text="0", font=("Arial", 16), fg="red", bg="white")
malware_counter.grid(row=0, column=1, padx=5)

# Hoşgeldiniz etiketi
welcome_label = tk.Label(main_frame, text="IDS Beta", font=("Arial", 16, "bold"), bg="white")
welcome_label.pack(side=tk.TOP, pady=10)

# Olağan Paket sayaç etiketi
normal_label = tk.Label(status_panel, text="Olağan Paket:", font=("Arial", 14, "bold"), bg="white")
normal_label.grid(row=0, column=2, padx=5)

# Olağan Paket sayaç
normal_counter = tk.Label(status_panel, text="0", font=("Arial", 16), fg="green", bg="white")
normal_counter.grid(row=0, column=3, padx=5)

# Konsol alanını oluşturun
console_frame = tk.Frame(main_frame, pady=30, bg="black")
console_frame.pack()

console_label = tk.Label(console_frame, text="Konsol:", font=("Arial", 14, "bold"), fg="white", bg="black")
console_label.pack(side=tk.TOP)

console_text = tk.Text(console_frame, width=300, height=25, font=("Courier New", 12), fg="white", bg="black")
console_text.pack(side=tk.TOP)

button_frame = tk.Frame(main_frame, bg="white")
button_frame.pack(side=tk.TOP, pady=10)


# Dosya Seç düğmesi
select_button = tk.Button(button_frame, text="Dosya Seç", font=("Arial", 12), bg="#00264d", fg="white", relief=tk.RAISED, command=select_file)
select_button.pack(side=tk.LEFT, padx=5)

# Analiz düğmesi
analyze_button = tk.Button(button_frame, text="Analiz Yap", font=("Arial", 12), bg="#00264d", fg="white", relief=tk.RAISED, command=perform_analysis)
analyze_button.pack(side=tk.LEFT, padx=5)

# Raporu Kaydet düğmesi
save_button = tk.Button(button_frame, text="Raporu Kaydet", font=("Arial", 12), bg="#00264d", fg="white", relief=tk.RAISED, command=save_report)
save_button.pack(side=tk.LEFT, padx=5)

clear_button = tk.Button(button_frame, text="Temizle", font=("Arial", 12), bg="#00264d", fg="white", relief=tk.RAISED, command=clear_console)
clear_button.pack(side=tk.LEFT, padx=5)

# Pencereyi gösterin
window.mainloop()

