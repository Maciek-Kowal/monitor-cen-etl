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

    # Wypisanie co wziął z pliku
    logging.info(f"Parametry z .env -> Serwer: {serwer} | Baza: {baza}")

    conn_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        f"Server={serwer};"
        f"Database={baza};"
        "Trusted_Connection=yes;"
    )

    try:
        logging.info("Próbuję połączyć się z bazą danych MS SQL.")
        polaczenie = pyodbc.connect(conn_string)
        logging.info("Połączono pomyślnie z bazą danych.")
        return polaczenie
    except Exception as ex:
        logging.critical(f"Błąd krytyczny przy połączeniu z bazą danych: {ex}")
        sys.exit(1)