import requests
from bs4 import BeautifulSoup
import demjson3
from urllib.parse import urljoin
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Referer": "https://video.ufdub.com/"
}


def split_title(title_text):
    """Розділити назву на українську та англійську (якщо є)."""
    parts = [t.strip() for t in title_text.split('/') if t.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return title_text.strip(), "Невідомо"


def search_anime(query):
    url = f"https://ufdub.com/index.php?do=search&subaction=search&story={requests.utils.quote(query)}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    anime_items = soup.select('.short')
    results = []

    for item in anime_items:
        title_tag = item.select_one('a.short-t')
        if not title_tag:
            continue

        title_text = title_tag.get_text(separator=" ").strip()
        title_uk, title_en = split_title(title_text)
        anime_url = title_tag['href']

        poster_tag = item.select_one('.short-i img')
        poster_url = poster_tag['src'] if poster_tag else ''
        if poster_url.startswith('/'):
            poster_url = urljoin("https://ufdub.com", poster_url)

        genre_tags = item.select('.short-c a')
        genres = [g.get_text(strip=True) for g in genre_tags]

        description_tag = item.select_one('.short-d')
        description = description_tag.get_text(strip=True) if description_tag else ''

        results.append({
            'title_uk': title_uk,
            'title_en': title_en,
            'title': title_text,
            'url': anime_url,
            'poster': poster_url,
            'genres': genres,
            'description': description,
        })

    return results


def extract_js_array(script_text):
    start = script_text.find('a=[')
    if start == -1:
        return None
    start += 2
    end = script_text.find('];', start)
    if end == -1:
        return None
    return script_text[start:end + 1]


def get_player_url_and_series(anime_url):
    r = requests.get(anime_url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    iframe = soup.find('iframe', id='input_video_player')
    if not iframe or 'src' not in iframe.attrs:
        print("Плеєр iframe не знайдено")
        return None, []

    player_url = iframe['src']

    r2 = requests.get(player_url, headers=HEADERS)
    r2.raise_for_status()
    soup2 = BeautifulSoup(r2.text, 'html.parser')

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
    try:
        resp = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=timeout)
    except requests.RequestException:
        return None

    if not (200 <= resp.status_code < 400):
        return None

    final_url = resp.url
    ctype = resp.headers.get("Content-Type", "").lower()

    if "video/" in ctype or "octet-stream" in ctype:
        return final_url

    if "api.ufdub.com/UFDUB_UPLOAD/VIDEO" in final_url:
        return final_url

    return None


def save_series_json(anime_id, anime_info, series):
    data = {
        'id': anime_id,
        'title': anime_info['title'],
        'title_uk': anime_info['title_uk'],
        'title_en': anime_info['title_en'],
        'url': anime_info['url'],
        'poster': anime_info['poster'],
        'genres': anime_info['genres'],
        'description': anime_info['description'],
        'series': []
    }
    for title, typ, link in series:
        data['series'].append({
            'title': title,
            'type': typ,
            'link': link
        })

    filename = f"series_for_{anime_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Інформацію збережено у {filename}")


def main():
    print("Завантаження списку аніме з сайту...")
    query = input("Введіть назву аніме для пошуку: ").strip()

    results = search_anime(query)
    if not results:
        print("Аніме за вашим запитом не знайдено.")
        return

    print(f"Знайдено аніме: {len(results)}")
    for i, anime in enumerate(results, start=1):
        print(f"{i}. {anime['title']} — {anime['url']}")

    choice = input(f"Виберіть номер аніме для перегляду серій (1-{len(results)}): ")
    try:
        choice_idx = int(choice) - 1
        if not (0 <= choice_idx < len(results)):
            raise ValueError
    except ValueError:
        print("Невірний вибір.")
        return

    selected_anime = results[choice_idx]
    print(f"\nПарсимо серії аніме за URL: {selected_anime['url']}")

    player_url, series = get_player_url_and_series(selected_anime['url'])
    print("=" * 50)
    print(f"Посилання на плеєр: {player_url}")
    print(f"Знайдено серій: {len(series)}")
    print("=" * 50)

    filtered_series = []
    if series:
        print("Серії з прямими посиланнями на mp4:")
        for title, typ, link in series:
            mp4_url = check_video_exists(link)
            if mp4_url:
                print(f" - {title} | {typ} | {mp4_url}")
                filtered_series.append((title, typ, mp4_url))
            else:
                print(f" - {title} | {typ} | [X] Пряме посилання не знайдено")
    else:
        print("Не вдалося знайти список серій")

    anime_id = selected_anime['url'].split('/')[-1].split('-')[0]
    save_series_json(anime_id, selected_anime, filtered_series)

    print("=" * 50)
    print("Перевірка завершена")


if __name__ == "__main__":
    main()
