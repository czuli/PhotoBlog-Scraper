import os
import time
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from urllib.parse import unquote
from datetime import datetime

# Globalne zmienne konfiguracyjne
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
CHROME_OPTIONS = ['--headless']  # For headless browser operation
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def save_image(img_url, save_path):
    img_name = os.path.basename(unquote(img_url)).split('?')[0]
    img_folder_path = os.path.join(save_path, os.path.splitext(img_name)[0])
    os.makedirs(img_folder_path, exist_ok=True)
    img_path = os.path.join(img_folder_path, img_name)

    if os.path.isfile(img_path):
        print(f"Plik {img_path} już istnieje, pomijanie pobierania pliku.")
        return img_name

    response = requests.get(img_url, stream=True, headers=HEADERS)
    response.raise_for_status()

    with open(img_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return img_name

def download_post(post_url, save_path):
    print(f"Pobieranie: {post_url}")
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
        img_md_path = f"/{os.path.join(save_path, img_name.rsplit('.', 1)[0], img_name)}"
    else:
        print(f"Nie znaleziono elementu obrazu w poście: {post_url}")
        return

    if date_elem:
        date_text = date_elem.get_text(strip=True).replace('Dodane ', '')
        # Map Polish month names to numbers
        month_mapping = {
            'STYCZNIA': '01', 'STYCZEŃ': '01', 'LUTEGO': '02', 'LUTY': '02', 'MARCA': '03', 'MARZEC': '03',
            'KWIECIEŃ': '04', 'KWIETNIA': '04', 'KWIECIENIA': '04', 'MAJA': '05', 'MAJ': '05', 'CZERWCA': '06', 'CZERWIEC': '06',
            'LIPIECA': '07', 'LIPCA': '04', 'LIPIEC': '07', 'SIERPNIA': '08', 'SIERPIEŃ': '08', 'WRZEŚNIA': '09', 'WRZESIEŃ': '09',
            'PAŹDZIERNIKA': '10', 'PAŹDZIERNIK': '10', 'LISTOPADA': '11', 'LISTOPAD': '11', 'GRUDNIA': '12', 'GRUDZIEŃ': '12'
        }
        for month_name, month_number in month_mapping.items():
            date_text = date_text.replace(month_name, month_number)
        date_obj = datetime.strptime(date_text, '%d %m %Y')
        txt_file_name = date_obj.strftime('%d-%m-%Y') + '.md'
    else:
        txt_file_name = os.path.basename(img_name).split('.')[0] + '.md'

    txt_file_path = os.path.join(save_path, txt_file_name)

    if os.path.isfile(txt_file_path):
        with open(txt_file_path, 'a', encoding='utf-8') as file:
            file.write(f"\n\n====\n\n")
            if title_elem and date_elem:
                title_text = title_elem.get_text(strip=True)
                file.write(f"### {title_text}\n\n")
            elif date_elem:
                title_text = date_obj.strftime('%d-%m-%Y')
                file.write(f"#### {title_text}\n\n")
            if post_url:
                file.write(f"Link do wpisu: [{post_url}]({post_url}) \n\n")
            if img_elem:
                file.write(f"![]({img_md_path})\n\n")
            if content_elem:
                file.write(f"{content_elem.get_text(strip=True)}\n")
        print(f"Plik {txt_file_path} już istnieje, dodawanie zawartości.")
        return

    with open(txt_file_path, 'w', encoding='utf-8') as file:
        file.write(f"---\ntagi: DailyNote\n---\n\n")
        if title_elem and date_elem:
            title_text = title_elem.get_text(strip=True)
            date_text = date_obj.strftime('%d-%m-%Y')
            file.write(f"### {title_text}\nData: {date_text}\n\n")
        elif date_elem:
            title_text = date_obj.strftime('%d-%m-%Y')
            file.write(f"#### {title_text}\n\n")
        if post_url:
            file.write(f"Link do wpisu: [{post_url}]({post_url}) \n\n")
        if img_elem:
            file.write(f"![]({img_md_path})\n\n")
        if content_elem:
            file.write(f"{content_elem.get_text(strip=True)}\n")

def get_driver():
    options = webdriver.ChromeOptions()
    for opt in CHROME_OPTIONS:
        options.add_argument(opt)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_all_post_links(driver, profile_name):
    print("Pobieranie linków do postów, proszę czekać...")
    try:
        archive_url = f"https://www.photoblog.pl/{profile_name}/archiwum"
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

        return post_links
    except Exception as e:
        print(f"Błąd: {e}. Sprawdź, czy nazwa profilu jest poprawna.")
        return None

def main():
    driver = get_driver()

    try:
        # Pobiera nazwę profilu od użytkownika
        profile_name = input("Podaj nazwę profilu: ").strip()

        post_links = get_all_post_links(driver, profile_name)

        if post_links is not None and len(post_links) > 0:
            print(f"Znaleziono {len(post_links)} linków do postów.")
            save_path = input("Podaj ścieżkę do zapisu (np. _AssetsLinks): ").strip()

            if not os.path.exists(save_path):
                os.makedirs(save_path)

            print(f"Znaleziono {len(post_links)} linków do postów")
            for link in post_links:
                download_post(link, save_path)
        elif post_links is not None and len(post_links) == 0:
            print("Nie znaleziono postów dla tego profilu.")
        else:
            print("Podaj poprawną nazwę profilu.")
    except Exception as e:
        print(f"Wystąpił wyjątek: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
