import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import urllib.parse
import time
import pandas as pd


def testuj_czystosc_wynikow(baza_frazy):
    print("1. Buduję hermetyczny link...")

    # Kategoria 4228 to sztywno "Podzespoły komputerowe"
    id_kategorii = "4228"

    # Dodajemy filtry słowne wykluczające śmieci
    fraza_z_filtrami = f"{baza_frazy} -komputer -zestaw -pc"

    # Zamieniamy spacje na '%20' (wymóg przeglądarek internetowych)
    zakodowana_fraza = urllib.parse.quote(fraza_z_filtrami)

    # Sklejamy ostateczny link. Zwróć uwagę na &stan=nowe na samym końcu.
    url = "https://allegro.pl/kategoria/podzespoly-komputerowe-karty-graficzne-260019?stan=nowe&string=rtx%204060&seria=GeForce%20RTX%204xxx"

    print(f"Wygenerowany URL:\n{url}\n")
    print("2. Uruchamiam przeglądarkę stealth i wchodzę na stronę...")

    driver = uc.Chrome()
    try:
        driver.get(url)
        time.sleep(5)  # Czekamy na ominięcie zabezpieczeń
        html = driver.page_source
    finally:
        driver.quit()

    print("3. Analizuję zwrócone tytuły ofert...\n")
    zupa = BeautifulSoup(html, 'html.parser')
    oferty = zupa.find_all('article')

    lista_wynikow = []

    # Wyciągamy pierwsze 10 ofert z góry
    for oferta in oferty[:10]:
        # Tniemy tekst do pierwszych 70 znaków dla samej czytelności w konsoli
        czysty_tekst = " ".join(oferta.text.split())[:70]
        lista_wynikow.append({"Znaleziony Tytuł": czysty_tekst})

    df = pd.DataFrame(lista_wynikow)
    print("--- WYNIKI TESTU (Pierwsze 10 ofert) ---")
    print(df.to_string(index=False))


if __name__ == '__main__':
    # Możesz tu wpisać dowolną kartę lub procesor z naszej listy
    testuj_czystosc_wynikow("rtx 4060 8gb")