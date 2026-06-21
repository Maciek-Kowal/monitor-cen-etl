import sys
import time
import statistics
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
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
    zapytanie = "select count(*) from xkom_przejsciowy where data_pobrania = cast(getdate() as date)"
    kursor.execute(zapytanie)
    if kursor.fetchone()[0] > 0:
        logging.warning("Dzisiaj dane z X-Kom były pobierane.")
        return True
    return False

def pobierz_slownik(kursor):
    zapytanie = """
        select id_sprzetu, nazwa_modelu, url_xkom 
        from slownik_podzespolow 
        where aktywny = 1 and url_xkom is not null
    """
    kursor.execute(zapytanie)
    return [{"id_sprzetu": w[0], "nazwa_modelu": w[1], "url_xkom": w[2]} for w in kursor.fetchall()]

def pobierz_ceny_z_xkom(lista_zakupow, polaczenie, kursor):
    logging.info("Odpalam przeglądarkę Playwright...")

    with sync_playwright() as p:
        # Otwarcie przeglądarki
        przegladarka = p.chromium.launch(headless=True)
        strona = przegladarka.new_page()

        for przedmiot in lista_zakupow:
            logging.info(f"--- Sprawdzam: {przedmiot['nazwa_modelu']} ---")
            bazowy_url = przedmiot['url_xkom']

            czyste_ceny_dla_sprzetu = []
            numer_strony = 1
            poprzednie_brudne_ceny = []

            # Przechodzenie przez strony
            while numer_strony <= 10:  # Limiter

                # Doklejanie numeru strony
                if "?" in bazowy_url:
                    aktualny_url = f"{bazowy_url}&page={numer_strony}"
                else:
                    aktualny_url = f"{bazowy_url}?page={numer_strony}"

                logging.info(f"Ładuję stronę nr {numer_strony}.")
                strona.goto(aktualny_url)

                strona.wait_for_timeout(2000)

                klasa_ceny = ".parts__Price-sc-fd70cef5-1"

                try:
                    strona.wait_for_selector(klasa_ceny, timeout=3000)
                except PlaywrightTimeoutError:
                    logging.info("Brak wyników na tej stronie (koniec ofert).")
                    break

                brudne_ceny = strona.locator(klasa_ceny).all_inner_texts()

                # Zabezpieczenie przed zapętlaniem stron przez X-Kom
                if brudne_ceny == poprzednie_brudne_ceny:
                    logging.info("Przerywam!")
                    break

                # Ostatnia strona ma mniej niż 30 produktów
                czy_ostatnia_strona = len(brudne_ceny) < 30

                for brudna_cena in brudne_ceny:
                    try:
                        czysty_string = brudna_cena.replace(" ", "").replace("\xa0", "").replace("zł", "").replace(",", ".").strip()
                        czysta_liczba = float(czysty_string)
                        czyste_ceny_dla_sprzetu.append(czysta_liczba)
                    except ValueError:
                        pass  # Ignorujemy błędy

                poprzednie_brudne_ceny = brudne_ceny
                numer_strony += 1

                if czy_ostatnia_strona:
                    logging.info("Pomyślnie zescrapowano ostatnią stronę ofert.")
                    break

            # Przygotowanie danych do sqla
            wolumen = len(czyste_ceny_dla_sprzetu)

            if wolumen > 0:
                cena_min = min(czyste_ceny_dla_sprzetu)
                cena_max = max(czyste_ceny_dla_sprzetu)
                cena_srednia = round(sum(czyste_ceny_dla_sprzetu) / wolumen, 2)
                mediana = statistics.median(czyste_ceny_dla_sprzetu)

                logging.info(f"Ofert łącznie: {wolumen} | Min: {cena_min} | Max: {cena_max} | Śred. : {cena_srednia} | Mediana: {mediana}")

                # Zapis do bazy
                zapytanie_insert = """
                    insert into xkom_przejsciowy (id_sprzetu, data_pobrania, wolumen, cena_min, cena_max, srednia, mediana)
                    values (?, getdate(), ?, ?, ?, ?, ?)
                """
                wartosci = (przedmiot['id_sprzetu'], wolumen, cena_min, cena_max, cena_srednia, mediana)

                try:
                    kursor.execute(zapytanie_insert, wartosci)
                    polaczenie.commit()
                    logging.info("Zapisano pomyślnie w SQL")
                except Exception as e:
                    polaczenie.rollback()
                    logging.error(f"Błąd przy zapisie do bazy: {e}")
            else:
                logging.warning("Błąd: Nie było żadnych ofert dla tego podzespołu na żadnej stronie.")

        przegladarka.close()

# Odpalenie skryptu
if __name__ == "__main__":
    polaczenie = polacz_z_baza()
    kursor = polaczenie.cursor()

    if not sprawdz_czy_pobrano_dzisiaj(kursor):
        lista = pobierz_slownik(kursor)
        pobierz_ceny_z_xkom(lista, polaczenie, kursor)

    kursor.close()
    polaczenie.close()