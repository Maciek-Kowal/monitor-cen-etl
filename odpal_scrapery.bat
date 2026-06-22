@echo off
cd "C:\Users\macie\PycharmProjects\Monitor_Cen"

:: Aktywacja wirtualnego środowiska PyCharma
call .venv\Scripts\activate

:: Odpalanie skryptów po kolei
echo Odpalam nbp_api.py...
python "nbp_api.py"

echo Odpalam X-Kom Scraper.py...
python "X-Kom_Scraper.py"

echo Odpalam Allegro_Scraper.py...
python "Allegro_Scraper.py"

echo Wszystkie scrapery zakonczyly prace!

pause