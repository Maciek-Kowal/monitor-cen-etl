#!/bin/bash
echo "Odpalam nbp_api.py..."
python nbp_api.py

echo "Odpalam X-kom_Scraper.py..."
python X-kom_Scraper.py

echo "Odpalam Allegro_Scraper.py..."
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python Allegro_Scraper.py

echo "Wszystkie scrapery zakonczyly prace!"