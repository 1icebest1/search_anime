import requests
from bs4 import BeautifulSoup
import demjson3

HEADERS = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://video.ufdub.com/'
}

def extract_js_array(script_text):
    """
    Витягує JS-масив a = [...] з тексту скрипта.
    """
    start = script_text.find('a=[')
    if start == -1:
        return None
    start += 2  # позиція після "a="
    end = script_text.find('];', start)
    if end == -1:
        return None
    array_str = script_text[start:end+1]  # включає закриваючу "]"
    return array_str

def get_player_url_and_series(anime_url):
    # Отримуємо сторінку аніме
    r = requests.get(anime_url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    iframe = soup.find('iframe', id='input_video_player')
    if not iframe or 'src' not in iframe.attrs:
        print("Плеєр iframe не знайдено")
        return None, []

    player_url = iframe['src']

    # Отримуємо сторінку плеєра
    r2 = requests.get(player_url, headers=HEADERS)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, 'html.parser')

    # Знаходимо JS-скрипт з масивом a
    scripts = soup2.find_all('script')
    series_list = []

    for script in scripts:
        if script.string and 'a=[' in script.string:
            array_str = extract_js_array(script.string)
            if array_str:
                try:
                    series_list = demjson3.decode(array_str)
                except Exception as e:
                    print(f"Помилка парсингу масиву серій: {e}")
                break

    return player_url, series_list

def check_video_exists(url, timeout=10):
    """
    Виконує HEAD-запит із редіректами.
    Якщо кінцева відповідь — відео (content-type) або посилання на хмару UFDUB, повертає кінцевий URL.
    Інакше None.
    """
    try:
        resp = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    final_url = resp.url
    content_type = resp.headers.get("Content-Type", "").lower()

    if "video/" in content_type or "octet-stream" in content_type:
        return final_url

    if "api.ufdub.com/UFDUB_UPLOAD/VIDEO" in final_url:
        return final_url

    return None

if __name__ == "__main__":
    anime_url = "https://ufdub.com/anime/336-agenty-chasu-rozdil-indu-shiguang-dailiren-yingdu-pian.html"
    player_url, series = get_player_url_and_series(anime_url)

    print("Посилання на плеєр:", player_url)
    print("Серії (назва, тип, посилання, статус відео):")

    for title, typ, link in series:
        mp4_url = check_video_exists(link)
        status = "[OK]" if mp4_url else "[X]"
        # Якщо хочеш, можеш виводити саме пряме посилання mp4:
        # print(f" - {title} | {typ} | {mp4_url if mp4_url else link} | {status}")
        print(f" - {title} | {typ} | {link} | {status}")