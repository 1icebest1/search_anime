import requests
from bs4 import BeautifulSoup
import demjson3
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Referer": "https://video.ufdub.com/"
}

def search_anime(query):
    url = f"https://ufdub.com/index.php?do=search&subaction=search&story={requests.utils.quote(query)}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')

    results = []
    items = soup.select("div.short.clearfix")
    for item in items:
        title_tag = item.find('a', class_='short-t')
        if not title_tag:
            continue
        url = title_tag.get('href')
        title_ukr = title_tag.text.strip().split('\n')[0]
        # жанри
        genre_div = item.find('div', class_='short-c')
        genres = []
        if genre_div:
            genres = [a.text.strip() for a in genre_div.find_all('a')]
        # опис
        desc_div = item.find('div', class_='short-d')
        description = desc_div.text.strip() if desc_div else ""

        results.append({
            "title": title_ukr,
            "url": url,
            "genres": genres,
            "description": description
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
    array_str = script_text[start:end + 1]
    return array_str

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


if __name__ == "__main__":
    print("Завантаження списку аніме з сайту...")
    query = input("Введіть назву аніме для пошуку: ").strip()
    anime_list = search_anime(query)

    if not anime_list:
        print("Аніме за вашим запитом не знайдено.")
        exit()

    # Збереження у файл JSON
    with open("search_results.json", "w", encoding="utf-8") as f:
        json.dump(anime_list, f, ensure_ascii=False, indent=4)

    print(f"Знайдено {len(anime_list)} аніме:")
    for i, anime in enumerate(anime_list, 1):
        print(f"{i}. {anime['title']}")
        print(f"   Жанри: {', '.join(anime['genres'])}")
        print(f"   Опис: {anime['description'][:150]}{'...' if len(anime['description']) > 150 else ''}")
        print(f"   Посилання: {anime['url']}")

    choice = int(input(f"Виберіть номер аніме для перегляду серій (1-{len(anime_list)}): "))
    selected = anime_list[choice - 1]

    print(f"\nПарсимо серії аніме за URL: {selected['url']}")
    player_url, series = get_player_url_and_series(selected['url'])

    print("=" * 50)
    print(f"Посилання на плеєр: {player_url}")
    print(f"Знайдено серій: {len(series)}")
    print("=" * 50)

    if series:
        series_data = []
        print("Серії (назва, тип, пряме посилання на mp4):")
        for title, typ, link in series:
            mp4_url = check_video_exists(link)
            if mp4_url:
                print(f" - {title} | {typ} | {mp4_url}")
                series_data.append({"title": title, "type": typ, "url": mp4_url})
            else:
                print(f" - {title} | {typ} | [X] Пряме посилання не знайдено")
                series_data.append({"title": title, "type": typ, "url": None})

        # Збереження серій у файл
        anime_id = selected['url'].split('/')[-1].split('-')[0]
        filename = f"series_for_{anime_id}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(series_data, f, ensure_ascii=False, indent=4)
        print(f"\nСерії збережено у файл: {filename}")

    else:
        print("Не вдалося знайти список серій")

    print("=" * 50)
    print("Перевірка завершена")
