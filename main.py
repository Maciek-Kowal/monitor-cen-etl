#import bibliotek
from base64 import b64encode

import pyodbc #polaczenie
import sqlalchemy
import sys #wychodzenie przy bledzie
from dotenv import load_dotenv
import os
import base64
#connection string do bazy danych
try:
    conn = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=Maciek\\SQLEXPRESS;"
        "Database=Monitor_Cen;"
        "Trusted_Connection=yes;"
    )
except Exception as ex:
    print(f"Błąd przy połączeniu z bazą danych, opis: {ex}")
    sys.exit(1)
#pobieranie loginu i haslo do API
load_dotenv()
Allegro_ID = os.getenv("CLIENT_ID")
Allegro_Pass = os.getenv("CLIENT_SECRET")

Polaczone_klucze = Allegro_ID + ':' + Allegro_Pass
klucze_bajty =Polaczone_klucze.encode("utf-8")
kodowanie_b64 = base64.b64encode(klucze_bajty)
autoryzacja = kodowanie_b64.decode("utf-8")

moje_naglowki = {
    "Authorization": f"Basic {autoryzacja}",
}