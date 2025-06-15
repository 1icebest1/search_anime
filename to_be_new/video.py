import requests
import urllib.parse
import time
import json

def check_video_url(series_url, timeout=10):
    """
    Перевіряє URL серії:
    - Виконує HEAD-запит з allow_redirects=True.
    - Перевіряє статус (200–399).
    - Перевіряє Content-Type: якщо містить 'video' або 'octet-stream', або кінцевий URL містить 'api.ufdub.com/UFDUB_UPLOAD/VIDEO',
      вважаємо, що це реальне відео.
    Повертає кінцевий URL (resp.url) якщо валідно, інакше None.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.head(series_url, headers=headers, allow_redirects=True, timeout=timeout)
    except requests.RequestException:
        return None

    status = resp.status_code
    if not (200 <= status < 400):
        return None

    final_url = resp.url  # кінцевий після редиректів

    # Перевірка Content-Type
    content_type = resp.headers.get("Content-Type", "").lower()
    # Якщо Content-Type вказує на HTML, скоріш за все це сторінка, а не відео
    # Часто відео віддається як 'video/mp4', 'application/octet-stream' тощо
    if "video" in content_type or "octet-stream" in content_type:
        return final_url

    # Додаткова перевірка: якщо кінцевий URL явно веде на api.ufdub.com/UFDUB_UPLOAD/VIDEO
    # (з вашого логу: реальні відео мають URL виду https://api.ufdub.com/UFDUB_UPLOAD/VIDEO/...)
    if "api.ufdub.com/UFDUB_UPLOAD/VIDEO" in final_url:
        return final_url

    # Якщо немає ознак реального відеофайлу, вважаємо, що серія відсутня
    return None

def parse_series_auto(base_id, tab="Основа", delay=1.0, timeout=10, safety_limit=1000):
    """
    Автоматично перебирає серії починаючи з 1 доти, доки є відео.
    Використовує check_video_url для перевірки наявності реального відео.
    Зупиняється, щойно check_video_url повертає None.
    Має safety_limit, щоб уникнути нескінченних циклів (але зазвичай зупиняється раніше).
    Повертає структуру:
      {
        "anime_id": base_id,
        "tab": tab,
        "total_series": N,
        "series": {
           "1": "url1",
           "2": "url2",
           ...
        }
      }
    """
    result = {
        "anime_id": base_id,
        "tab": tab,
        "total_series": 0,
        "series": {}
    }
    base_url = "https://ufdub.com/video/VIDEOS.php"
    encoded_tab = urllib.parse.quote(tab, safe="")

    ser_num = 1
    while ser_num <= safety_limit:
        seriya_val = f"Серія {ser_num}"
        encoded_seriya = urllib.parse.quote(seriya_val, safe="")
        pos = ser_num  # POS = номер серії
        url = f"{base_url}?ID={base_id}&TAB={encoded_tab}&Seriya={encoded_seriya}&POS={pos}"
        print(f"[INFO] Перевірка: Серія {ser_num} -> {url}")

        video_url = check_video_url(url, timeout=timeout)
        if video_url:
            print(f"  [OK] Серія {ser_num}: знайдено відео -> {video_url}")
            result["series"][str(ser_num)] = video_url
            result["total_series"] = ser_num
            ser_num += 1
            time.sleep(delay)
        else:
            print(f"  [X] Серія {ser_num}: відео не знайдено або недоступно. Завершення пошуку.")
            break

    if ser_num > safety_limit:
        print(f"[WARN] Досягнуто safety_limit ({safety_limit}). Перевір, чи дійсно стільки серій.")
    return result

def save_to_json(data, filename=None):
    """
    Зберігає результат у JSON-файл.
    Якщо filename не задано, створює 'anime_<id>_<tab>.json'
    """
    anime_id = data.get("anime_id")
    tab = data.get("tab", "").replace(" ", "_")
    if not filename:
        filename = f"anime_{anime_id}_{tab}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Збережено результати у {filename}")

if __name__ == "__main__":
    # Налаштування
    anime_id = 348          # Заміни на потрібний ID
    tab = "Основа"          # Вкладка: "Основа" або інша, якщо треба
    delay_between = 1.0     # Пауза між запитами (сек)
    timeout = 10            # Таймаут для HEAD-запиту
    safety_limit = 1000     # Максимальний номер серії для перевірки

    result = parse_series_auto(
        base_id=anime_id,
        tab=tab,
        delay=delay_between,
        timeout=timeout,
        safety_limit=safety_limit
    )
    print(f"\nЗагалом знайдено серій: {result['total_series']}")
    save_to_json(result)
