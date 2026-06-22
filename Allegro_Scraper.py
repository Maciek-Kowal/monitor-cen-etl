import sys
import time
import statistics
import logging
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
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
    zapytanie = "select count(*) from allegro_przejsciowy where data_pobrania = cast(getdate() as date)"
    kursor.execute(zapytanie)
    if kursor.fetchone()[0] > 0:
        logging.warning("Dzisiaj dane z Allegro były pobierane.")
        return True
    return False

def pobierz_slownik(kursor):
    zapytanie = """
        select id_sprzetu, nazwa_modelu, url_allegro 
        from slownik_podzespolow 
        where aktywny = 1 and url_allegro is not null
    """
    kursor.execute(zapytanie)
    return [{"id_sprzetu": w[0], "nazwa_modelu": w[1], "url_allegro": w[2]} for w in kursor.fetchall()]

def pobierz_ceny_z_allegro(lista_zakupow, polaczenie, kursor):
    logging.info("Odpalam przeglądarkę Undetected Chromedriver.")
    driver = uc.Chrome(version_main=149)
    driver.minimize_window()

    for przedmiot in lista_zakupow:
        logging.info(f"Sprawdzam: {przedmiot['nazwa_modelu']}")
        driver.get(przedmiot['url_allegro'])
        time.sleep(2)

        html = driver.page_source
        zupa = BeautifulSoup(html, 'html.parser')
        oferty = zupa.find_all('article')

        ceny_z_tej_strony = []
        klasa_ceny = "mli8_k4 msa3_z4 mqu1_1 mp0t_ji m9qz_yo mgmw_qw mgn2_27 mgn2_30_s"

        if oferty:
            for oferta in oferty:
                element_ceny = oferta.find(class_=klasa_ceny)
                if element_ceny:
                    ceny_z_tej_strony.append(element_ceny.text)

        if len(ceny_z_tej_strony) > 0:
            czyste_ceny = []
            for brudna_cena in ceny_z_tej_strony:
                try:
                    czysty_string = brudna_cena.replace(" ", "").replace("\xa0", "").replace("zł", "").replace(",", ".").strip()
                    czyste_ceny.append(float(czysty_string))
                except ValueError:
                    pass
            # Przygotowanie danych do sqla
            wolumen = len(czyste_ceny)
            if wolumen > 0:
                cena_min = min(czyste_ceny)
                cena_max = max(czyste_ceny)
                cena_srednia = round(sum(czyste_ceny) / wolumen, 2)
                mediana = statistics.median(czyste_ceny)

                logging.info(f"Ofert: {wolumen} | Min: {cena_min} | Max: {cena_max} | Śred.: {cena_srednia} | Med.: {mediana}")

                zapytanie_insert = """
                    insert into allegro_przejsciowy (id_sprzetu, data_pobrania, wolumen, cena_min, cena_max, srednia, mediana)
                    values (?, getdate(), ?, ?, ?, ?, ?)
                """
                try:
                    kursor.execute(zapytanie_insert, (przedmiot['id_sprzetu'], wolumen, cena_min, cena_max, cena_srednia, mediana))
                    polaczenie.commit()
                    logging.info("Zapisano pomyślnie w bazie")
                except Exception as e:
                    polaczenie.rollback()
                    logging.error(f"Błąd przy zapisie do bazy: {e}")
        else:
            logging.warning("Błąd: Nie było żadnych ofert z ceną na tej stronie.")

    driver.quit()

# Odpalenie skryptu
if __name__ == "__main__":
    polaczenie = polacz_z_baza()
    kursor = polaczenie.cursor()

    if not sprawdz_czy_pobrano_dzisiaj(kursor):
        lista = pobierz_slownik(kursor)
        pobierz_ceny_z_allegro(lista, polaczenie, kursor)

    kursor.close()
    polaczenie.close()