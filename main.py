import pyodbc
import sys
import undetected_chromedriver as uc
import time
from bs4 import BeautifulSoup
import statistics

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
        select id_sprzetu, nazwa_modelu, url_allegro 
        from slownik_podzespolow 
        where aktywny = 1 and url_allegro is not null
        """
kursor.execute(zapytanie)

# mapowanie wynikow do listy
lista=[]
for wiersz in kursor.fetchall():
    sprzet = {
        "id_sprzetu":wiersz[0],
        "nazwa_modelu":wiersz[1],
        "url_allegro":wiersz[2]
    }
    lista.append(sprzet)

def pobierz_ceny_z_allegro(lista_zakupow):
    # inicjalizacja przegladarki
    print("\nodpalam przegladarke")
    driver = uc.Chrome(version_main=149)

    for przedmiot in lista_zakupow:
        print(f"\nsprawdzam: {przedmiot['nazwa_modelu']}")
        driver.get(przedmiot['url_allegro'])
        time.sleep(2)

        # parsowanie html
        html = driver.page_source
        zupa = BeautifulSoup(html, 'html.parser')
        oferty = zupa.find_all('article')

        # ekstrakcja brudnych cen
        ceny_z_tej_strony = []
        klasa_ceny = "mli8_k4 msa3_z4 mqu1_1 mp0t_ji m9qz_yo mgmw_qw mgn2_27 mgn2_30_s"

        if oferty:
            for oferta in oferty:
                element_ceny = oferta.find(class_=klasa_ceny)
                if element_ceny:
                    ceny_z_tej_strony.append(element_ceny.text)

        if len(ceny_z_tej_strony) > 0:
            # czyszczenie danych
            czyste_ceny = []
            for brudna_cena in ceny_z_tej_strony:
                czysty_string = brudna_cena.replace(" ", "").replace("\xa0", "").replace("zł", "").replace(",", ".").strip()
                czysta_liczba = float(czysty_string)
                czyste_ceny.append(czysta_liczba)

            # agregacja i statystyki
            wolumen = len(czyste_ceny)
            cena_min = min(czyste_ceny)
            cena_max = max(czyste_ceny)
            cena_srednia = round(sum(czyste_ceny) / wolumen, 2)
            mediana = statistics.median(czyste_ceny)

            print(f"  -> Ofert: {wolumen} | Min: {cena_min} | Max: {cena_max} | Śred. : {cena_srednia} | Mediana: {mediana}")

        else:
            print("  -> Błąd: Nie znalazłem żadnych ofert z ceną na tej stronie.")

    # zamykanie sesji
    driver.quit()

# uruchomienie procesu
pobierz_ceny_z_allegro(lista)