# Web Scraper dla Photoblog.pl

Ten skrypt jest narzędziem do pobierania i zapisywania zdjęć oraz informacji z postów na stronie Photoblog.pl.

## Wymagania

* Python 3.x
* Pip (zarządca pakietów dla Pythona)

## Instalacja

Kroki instalacyjne dla użytkowników systemów uniksowych i MacOS:

### 1. Sklonuj repozytorium

Za pomocą terminala sklonuj repozytorium do lokalnego katalogu:

git clone https://github.com/czuli/PhotoBlog-Scraper.git
cd PhotoBlog-Scraper


### 2. Zainstaluj zależności

Zainstaluj wymagane pakiety używając `pip`:

pip install -r requirements.txt


### 3. Uruchomienie skryptu

Aby uruchomić skrypt, upewnij się, że jesteś w katalogu zawierającym `scraper.py` i wykonaj:

python scraper.py / python3 scraper.py

Podaj nazwę profilu: nazwa profilu na photoblog.pl (pobierz z adresu url).
Podaj ścieżkę do zapisu (np. _AssetsLinks): your_folder_name

## Struktura katalogów

Po uruchomieniu skryptu zostanie utworzona następująca struktura katalogów:



```
.
├── ...
your_folder_name/
│
├── 123/
│ ├── 123.jpg
│
├── 1231231231/
│ ├── 1231231231.jpg
│
│
├── 123.md
└── 1231231231.md
```

## Ważne informacje

* Przed uruchomieniem upewnij się, że masz prawo do pobierania i użytkowania treści z danego serwisu internetowego.
* Skrypt przeznaczony jest wyłącznie do użytku edukacyjnego.

## Licencja

O ile nie zaznaczono inaczej, kody źródłowe są udostępnione na licencji MIT.
