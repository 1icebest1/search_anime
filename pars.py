import os
import json
import requests
import logging
from PySide6.QtCore import QThread, Signal

logging.basicConfig(filename='app.log', level=logging.INFO)
DATA_DIR = "data/online"


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
                data = self.load_random_anime(count=8)
                self.random_data_loaded.emit(data)
        except Exception as e:
            self.error_occurred.emit(f"Error: {str(e)}")
            logging.error(f"Error in thread: {str(e)}", exc_info=True)
        finally:
            self.finished.emit()

    def load_random_anime(self, count=8):
        try:
            url = f"{self.base_url}title/random"
            params = {'limit': count}
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            if not data.get('list'):
                raise ValueError("Empty response from API")

            formatted_data = []
            for item in data['list']:
                try:
                    names = item.get('names', {})
                    posters = item.get('posters', {})
                    formatted_data.append({
                        "title": names.get('ru') or names.get('en') or "No title",
                        "image": posters.get('original', {}).get('url') or "default.jpg",
                        "description": item.get('description', 'No description')
                    })
                except Exception as item_error:
                    logging.warning(f"Error processing item: {item_error}")

            if not formatted_data:
                raise ValueError("No valid anime data found")

            os.makedirs(DATA_DIR, exist_ok=True)
            with open(os.path.join(DATA_DIR, "random.json"), 'w', encoding='utf-8') as f:
                json.dump(formatted_data, f, ensure_ascii=False, indent=2)

            return formatted_data

        except requests.RequestException as e:
            logging.error(f"Network error: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            raise

    def load_top_anime_week(self):
        try:
            url = f"{self.base_url}title/updates"
            params = {'limit': 8}
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()

            data = response.json()
            items = data.get('list', [])
            new_data = []

            for item in items:
                if not isinstance(item, dict):
                    continue

                names = item.get('names') or {}
                title = (
                        names.get('ru')
                        or names.get('en')
                        or item.get('code')
                        or "Без назви"
                )
                title_ru = names.get('ru', 'Без названия')

                posters = item.get('posters') or {}
                image_url = (
                        posters.get('original', {}).get('url')
                        or posters.get('original', {}).get('url')
                        or item.get('poster')
                        or 'default.jpg'
                )

                genres = item.get('genres', []) if isinstance(item.get('genres'), list) else []
                genre_str = ", ".join([g for g in genres if isinstance(g, str)]) or "Жанр не вказано"

                status = item.get('status', {}) if isinstance(item.get('status'), dict) else {}
                status_str = status.get('string', 'Невідомо')

                description = str(item.get('description', '')).strip() or 'Опис відсутній'
                description_ru = str(item.get('description', '')).strip() or 'Описание отсутствует'

                rating = item.get('rating', {}) if isinstance(item.get('rating'), dict) else {}
                average = rating.get('average')
                try:
                    rating_5 = round(float(average) / 2, 1) if average else "Н/Д"
                except (TypeError, ValueError):
                    rating_5 = "Н/Д"

                player = item.get('player', {})
                episodes = player.get('list', {})
                episodes_info = []

                for episode_num, episode_data in episodes.items():
                    try:
                        opening = episode_data.get('opening', [])
                        ending = episode_data.get('ending', [])
                        hls_link = episode_data.get('hls')
                        navi = episode_data.get('navi')
                        episode_title = episode_data.get('name', f"Серія {episode_num}")
                        preview_image = episode_data.get('preview', None)

                        episodes_info.append({
                            "episode": episode_num,
                            "title": episode_title,
                            "opening": opening,
                            "ending": ending,
                            "video": hls_link,
                            "navi": navi,
                            "preview": preview_image
                        })
                    except Exception as ep_err:
                        logging.warning(f"Не вдалося обробити епізод {episode_num}: {ep_err}")

                new_data.append({
                    "title": title,
                    "title_ru": title_ru,
                    "image": image_url,
                    "genre": genre_str,
                    "status": status_str,
                    "description": description,
                    "description_ru": description_ru,
                    "rating": rating_5,
                    "episodes": episodes_info
                })

            os.makedirs(DATA_DIR, exist_ok=True)
            with open(os.path.join(DATA_DIR, "rec_anime.json"), 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logging.error(f"Помилка парсингу: {str(e)}", exc_info=True)
            raise