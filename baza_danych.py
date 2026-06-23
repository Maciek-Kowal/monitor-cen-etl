import pyodbc
import os
import sys
import logging
from dotenv import load_dotenv

# Ładowanie z pliku .env
load_dotenv()


def polacz_z_baza():
    serwer = os.getenv('DB_SERVER')
    baza = os.getenv('DB_DATABASE')
    uzytkownik = os.getenv('DB_USER')
    haslo = os.getenv('DB_PASSWORD')

    logging.info(f"Parametry z .env -> Serwer: {serwer} | Baza: {baza} | Uzytkownik: {uzytkownik}")

    # Logowanie przez haslo
    conn_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={serwer};"
        f"Database={baza};"
        f"UID={uzytkownik};"
        f"PWD={haslo};"
    )

    try:
        logging.info("Próbuję połączyć się z bazą danych MS SQL.")
        polaczenie = pyodbc.connect(conn_string)
        logging.info("Połączono pomyślnie z bazą danych.")
        return polaczenie
    except Exception as ex:
        logging.critical(f"Błąd krytyczny przy połączeniu z bazą danych: {ex}")
        sys.exit(1)