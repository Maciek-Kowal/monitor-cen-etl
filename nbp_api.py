import requests
import logging
from baza_danych import polacz_z_baza

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("historia_scraperow.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def sprawdz_czy_pobrano_dzisiaj(kursor):
    zapytanie = "select count(*) from nbp_przejsciowy where data_pobrania = cast(getdate() as date)"
    kursor.execute(zapytanie)
    if kursor.fetchone()[0] > 0:
        logging.warning("Dzisiaj dane z nbp były pobierane.")
        return True
    return False

# pobieranie danych
waluty = ["usd", "eur"]
kursy_walut = {}
logging.info("Rozpoczynam pobieranie kursów walut z API NBP.")
for i in waluty:
    usd_link = f"http://api.nbp.pl/api/exchangerates/rates/a/{i}/?format=json"
    odp = requests.get(usd_link)
    dane = odp.json()
    kurs = dane["rates"][0]["mid"]
    kursy_walut[i] = kurs
    logging.info(f"Pobrano pomyślnie kurs {i}: {kurs}")
print (kursy_walut)


polaczenie = polacz_z_baza()
kursor = polaczenie.cursor()
zapytanie_insert = "insert into nbp_przejsciowy(kurs_dolar, kurs_euro) values (?,?)"
kursor.execute(zapytanie_insert, kursy_walut["usd"], kursy_walut["eur"])


polaczenie.commit()
logging.info("Dane poprawnie zapisane w bazie MS SQL. Koniec pracy.")
polaczenie.close()