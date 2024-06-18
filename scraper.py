import os
import time
import requests
import argparse
import logging
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import unquote
from datetime import datetime
import json

# Globalne zmienne konfiguracyjne
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
CHROME_OPTIONS = ['--headless']  # For headless browser operation
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def setup_logging(devmode):
    logging.basicConfig(level=logging.DEBUG if devmode else logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def save_image(img_url, save_path):
    img_name = os.path.basename(unquote(img_url)).split('?')[0]
    img_folder_path = os.path.join(save_path, os.path.splitext(img_name)[0])
    os.makedirs(img_folder_path, exist_ok=True)
    img_path = os.path.join(img_folder_path, img_name)

    if os.path.isfile(img_path):
        logging.info(f"Plik {img_path} już istnieje, pomijanie pobierania pliku.")
        return img_name

    response = requests.get(img_url, stream=True, headers=HEADERS)
    response.raise_for_status()

    with open(img_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return img_name

def download_post(post_url, save_path):
    logging.info(f"Pobieranie: {post_url}")
    response = requests.get(post_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    img_elem = soup.find('img', id='show_pic_viewer')
    date_elem = soup.find('span', class_='date')
    title_elem = soup.select_one('h1.title .inplace_item_width')
    content_elem = soup.find('div', id='photo_note')

    title_text = title_elem.get_text(strip=True) if title_elem else "Brak tytułu"

    if img_elem:
        img_url = img_elem['src']
        img_name = save_image(img_url, save_path)
        img_md_path = f"/{os.path.join(save_path, img_name)}"

        date_text = date_elem.get_text(strip=True) if date_elem else "Brak daty"
        content_text = content_elem.get_text(strip=True) if content_elem else "Brak treści"

        metadata = {
            "title": title_text,
            "date": date_text,
            "content": content_text,
            "image": img_md_path
        }

        metadata_path = os.path.join(save_path, f"{os.path.splitext(img_name)[0]}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

def get_driver():
    chrome_service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    for option in CHROME_OPTIONS:
        options.add_argument(option)
    driver = webdriver.Chrome(service=chrome_service, options=options)
    return driver

def get_all_post_links(driver, profile_name):
    try:
        archive_url = f"https://www.photoblog.pl/{profile_name}/archiwum"
        logging.debug(f"Przechodzenie do: {archive_url}")
        driver.get(archive_url)

        # Przewijanie strony w dół, aby załadować wszystkie posty
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Czekanie na załadowanie strony
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:  # Jeśli nie ma więcej do załadowania, przerywamy pętlę
                break
            last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        post_links = [a['href'] for a in soup.select(f'div.arch_post a[href^="https://www.photoblog.pl/{profile_name}/"]')]

        logging.debug(f"Znaleziono {len(post_links)} linków do postów.")
        return post_links
    except Exception as e:
        logging.error(f"Błąd: {e}. Sprawdź, czy nazwa profilu jest poprawna.")
        return None

def main(profile_name=None, save_path=None, devmode=False):
    setup_logging(devmode)

    if profile_name is None:
        profile_name = input("Podaj nazwę profilu: ").strip()
    if save_path is None:
        save_path = input("Podaj ścieżkę do zapisu (np. _AssetsLinks): ").strip()

    driver = get_driver()

    try:
        post_links = get_all_post_links(driver, profile_name)

        if post_links is not None and len(post_links) > 0:
            logging.info(f"Znaleziono {len(post_links)} linków do postów.")

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            for link in post_links:
                download_post(link, save_path)
        elif post_links is not None and len(post_links) == 0:
            logging.info("Nie znaleziono postów dla tego profilu.")
        else:
            logging.info("Podaj poprawną nazwę profilu.")
    except Exception as e:
        logging.error(f"Wystąpił wyjątek: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pobieranie postów z profilu.')
    parser.add_argument('profile_name', type=str, nargs='?', help='Nazwa profilu')
    parser.add_argument('save_path', type=str, nargs='?', help='Ścieżka do zapisu')
    parser.add_argument('--devmode', action='store_true', help='Włącza tryb deweloperski')
    args = parser.parse_args()

    main(args.profile_name, args.save_path, args.devmode)
