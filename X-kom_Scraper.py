import pyodbc
import sys
import time
import statistics
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# polaczenie z baza
conn_string = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=Maciek\\SQLEXPRESS;"
    "Database=Monitor_Cen;"
    "Trusted_Connection=yes;"
)

try:
    print("Próbuję połączyć się z bazą danych")
    polaczenie = pyodbc.connect(conn_string)
    print("Połączono pomyślnie")
except Exception as ex:
    print(f"Błąd przy połączeniu z bazą danych, opis: {ex}")
    sys.exit(1)

# pobranie slownika podzespolow
kursor = polaczenie.cursor()
zapytanie ="""
        select id_sprzetu, nazwa_modelu, url_xkom 
        from slownik_podzespolow 
        where aktywny = 1 and url_xkom is not null
        """
kursor.execute(zapytanie)

# mapowanie wynikow do listy
lista=[]
for wiersz in kursor.fetchall():
    sprzet = {
        "id_sprzetu":wiersz[0],
        "nazwa_modelu":wiersz[1],
        "url_xkom":wiersz[2]
    }
    lista.append(sprzet)

# sprawdzenie, czy dzisiaj dane były już pobierane
zapytanie_sprawdzajace = "select count(*) from xkom_przejsciowy where data_pobrania = cast(getdate() as date)"
kursor.execute(zapytanie_sprawdzajace)
liczba_dzisiejszych_wpisow = kursor.fetchone()[0]

if liczba_dzisiejszych_wpisow > 0:
    print("\n[!] Dzisiaj dane z X-kom zostały już pobrane [!]")
    print("Zamykam skrypt, żeby nie dublować rekordów.")
    kursor.close()
    polaczenie.close()
    sys.exit(0)


def pobierz_ceny_z_xkom(lista_zakupow):
    print("\nOdpalam przeglądarkę Playwright...")

    with sync_playwright() as p:
        # Otwarcie przegladarki
        przegladarka = p.chromium.launch(headless=False)
        strona = przegladarka.new_page()

        # definiowanie "przedmiot"
        for przedmiot in lista_zakupow:
            print(f"\n--- Sprawdzam: {przedmiot['nazwa_modelu']} ---")
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

                print(f"  -> Ładuję stronę nr {numer_strony}...")
                strona.goto(aktualny_url)

                strona.wait_for_timeout(2000)

                klasa_ceny = ".parts__Price-sc-fd70cef5-1"

                try:
                    strona.wait_for_selector(klasa_ceny, timeout=8000)
                except PlaywrightTimeoutError:
                    print("  -> Brak wyników na tej stronie (koniec ofert).")
                    break

                brudne_ceny = strona.locator(klasa_ceny).all_inner_texts()

                # te same ceny
                if brudne_ceny == poprzednie_brudne_ceny:
                    print("  -> Osiągnięto koniec paginacji (sklep zapętla wyniki). Przerywam!")
                    break

                # mniej niz 30 obiektow
                czy_ostatnia_strona = len(brudne_ceny) < 30

                for brudna_cena in brudne_ceny:
                    try:
                        czysty_string = brudna_cena.replace(" ", "").replace("\xa0", "").replace("zł", "").replace(",",
                                                                                                                   ".").strip()
                        czysta_liczba = float(czysty_string)
                        czyste_ceny_dla_sprzetu.append(czysta_liczba)
                    except ValueError:
                        pass  # Ignorujemy błędy

                poprzednie_brudne_ceny = brudne_ceny
                numer_strony += 1

                # Jeśli to ostatnia strona to wychodzimy
                if czy_ostatnia_strona:
                    print("  -> Pomyślnie zescrapowano ostatnią stronę ofert.")
                    break

            # Po skanie stron dla sprzętu
            wolumen = len(czyste_ceny_dla_sprzetu)

            if wolumen > 0:
                cena_min = min(czyste_ceny_dla_sprzetu)
                cena_max = max(czyste_ceny_dla_sprzetu)
                cena_srednia = round(sum(czyste_ceny_dla_sprzetu) / wolumen, 2)
                mediana = statistics.median(czyste_ceny_dla_sprzetu)

                print(f"  [+] Ofert łącznie: {wolumen} | Min: {cena_min} | Max: {cena_max} | Śred. : {cena_srednia}")

                # zapis do bazy
                zapytanie_insert = """
                                insert into xkom_przejsciowy (id_sprzetu, data_pobrania, wolumen, cena_min, cena_max, srednia, mediana)
                                values (?, getdate(), ?, ?, ?, ?, ?)
                            """
                wartosci = (przedmiot['id_sprzetu'], wolumen, cena_min, cena_max, cena_srednia, mediana)

                try:
                    kursor.execute(zapytanie_insert, wartosci)
                    polaczenie.commit()
                    print("  [+] Zapisano pomyślnie w MS SQL")
                except Exception as e:
                    polaczenie.rollback()
                    print(f"  [!] Błąd przy zapisie do bazy: {e}")
            else:
                print("  -> [!] Błąd: Nie znalazłem żadnych ofert dla tego podzespołu na żadnej stronie.")

        # Zamykamy przeglądarkę po przejrzeniu wszystkich sprzętów
        przegladarka.close()


pobierz_ceny_z_xkom(lista)
kursor.close()
polaczenie.close()