import os
import json
import requests
import logging
from pathlib import Path
from PySide6.QtCore import QThread, Signal

# Absolute paths
BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "app.log"
DATA_DIR = BASE_DIR / "data" / "online"

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def detect_origin_language(original_title):
    if not original_title:
        return "Other", False

    if any('\u4e00' <= ch <= '\u9fff' for ch in original_title):
        return "Chinese", True

    if any(
        '\u3040' <= ch <= '\u309f' or
        '\u30a0' <= ch <= '\u30ff' or
        '\u4e00' <= ch <= '\u9fff'
        for ch in original_title
    ):
        return "Japanese", False

    return "Other", False


def fix_image_url(url):
    if not url:
        return "default.jpg"
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/") and not url.startswith("//"):
        return "https://anilibria.tv" + url
    return url


def safe_rating(value):
    try:
        return round(float(value) / 2, 1) if value else "Н/Д"
    except (TypeError, ValueError):
        return "Н/Д"


class AnimeLoaderThread(QThread):
    error_occurred = Signal(str)
    finished = Signal()
    random_data_loaded = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = "https://api.anilibria.tv/v3/"
        self.mode = "top"

    def run(self):
        try:
            if self.mode == "top":
                self.load_top_anime_week()
            elif self.mode == "random":
                data = self.load_random_anime(count=12)
                self.random_data_loaded.emit(data)
        except Exception as e:
            error_msg = f"Error in thread: {str(e)}"
            self.error_occurred.emit(error_msg)
            logging.error(error_msg, exc_info=True)
        finally:
            self.finished.emit()

    def load_random_anime(self, count=12):
        try:
            url = f"{self.base_url}title/random"
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }

            formatted_data = []

            for _ in range(count):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    item = response.json()

                    names = item.get('names', {})
                    title_original = names.get('original', '')
                    origin_lang, is_donghua = detect_origin_language(title_original)

                    image_url = fix_image_url(item.get('posters', {}).get('original', {}).get('url'))

                    genres = item.get('genres', [])
                    genre_str = ", ".join(genres) if isinstance(genres, list) else "Жанр не вказано"

                    rating_value = safe_rating(item.get('rating', {}).get('average'))

                    formatted_data.append({
                        "title": names.get('ru') or names.get('en') or "No title",
                        "title_original": title_original,
                        "origin_lang": origin_lang,
                        "is_donghua": is_donghua,
                        "image": image_url,
                        "description": item.get('description', 'No description')[:200] + "..."
                        if item.get('description') else "No description",
                        "genre": genre_str,
                        "rating": rating_value
                    })

                except Exception as item_error:
                    logging.warning(f"Error loading random anime item: {item_error}")
                    continue

            if not formatted_data:
                raise ValueError("No valid random anime data retrieved.")

            DATA_DIR.mkdir(parents=True, exist_ok=True)
            output_file = DATA_DIR / "random.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_data, f, ensure_ascii=False, indent=2)
            except Exception as save_err:
                logging.error(f"Failed to save random.json: {save_err}")

            return formatted_data

        except Exception as e:
            error_msg = f"Unexpected error while loading random anime: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise

    def load_top_anime_week(self):
        try:
            url = f"{self.base_url}title/updates"
            params = {'limit': 8}
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json'
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            data = response.json()
            items = data.get('list', [])
            new_data = []

            for item in items:
                if not isinstance(item, dict):
                    continue

                names = item.get('names') or {}
                title_original = names.get('original', '')
                origin_lang, is_donghua = detect_origin_language(title_original)

                title = names.get('ru') or names.get('en') or item.get('code') or "Без назви"
                title_ru = names.get('ru', 'Без названия')

                image_url = fix_image_url(item.get('posters', {}).get('original', {}).get('url') or item.get('poster'))

                genres = item.get('genres', []) if isinstance(item.get('genres'), list) else []
                genre_str = ", ".join([g for g in genres if isinstance(g, str)]) or "Жанр не вказано"

                status_str = item.get('status', {}).get('string', 'Невідомо')

                description = str(item.get('description', '')).strip() or 'Опис відсутній'
                description_ru = description or 'Описание отсутствует'

                rating_5 = safe_rating(item.get('rating', {}).get('average'))

                episodes_info = []
                episodes = item.get('player', {}).get('list') or {}
                for episode_num, episode_data in episodes.items():
                    try:
                        episodes_info.append({
                            "episode": episode_num,
                            "title": episode_data.get('name', f"Серія {episode_num}"),
                            "opening": episode_data.get('opening', []),
                            "ending": episode_data.get('ending', []),
                            "video": episode_data.get('hls'),
                            "navi": episode_data.get('navi'),
                            "preview": episode_data.get('preview')
                        })
                    except Exception as ep_err:
                        logging.warning(f"Не вдалося обробити епізод {episode_num}: {ep_err}")

                new_data.append({
                    "title": title,
                    "title_ru": title_ru,
                    "title_original": title_original,
                    "origin_lang": origin_lang,
                    "is_donghua": is_donghua,
                    "image": image_url,
                    "genre": genre_str,
                    "status": status_str,
                    "description": description,
                    "description_ru": description_ru,
                    "rating": rating_5,
                    "episodes": episodes_info
                })

            DATA_DIR.mkdir(parents=True, exist_ok=True)
            output_file = DATA_DIR / "rec_anime.json"
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, ensure_ascii=False, indent=2)
            except Exception as save_err:
                logging.error(f"Failed to save rec_anime.json: {save_err}")

        except requests.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise
        except json.JSONDecodeError as e:
            error_msg = f"JSON decode error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            raise