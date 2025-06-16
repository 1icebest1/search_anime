from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QGraphicsView, QScrollArea, QLineEdit, QPushButton, QGraphicsScene,
    QGraphicsPixmapItem, QComboBox, QFrame
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor
from PySide6.QtCore import Qt, QRectF, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json
import os
import random
import requests
from pathlib import Path


class RoundedImageLabel(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self.setFixedSize(240, 360)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setAlignment(Qt.AlignCenter)
        self.set_placeholder()

    def set_image(self, image_path):
        # Clear existing items
        self.scene.clear()

        pixmap = self.load_pixmap(image_path)
        if pixmap.isNull():
            pixmap = self.create_placeholder()

        pixmap = pixmap.scaled(240, 360, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # Create mask for rounded corners
        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, 15, 15)
        painter.end()

        # Apply mask
        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))

        self.scene.addItem(QGraphicsPixmapItem(pixmap))

    def load_pixmap(self, image_path):
        # Handle relative paths
        if not image_path or not isinstance(image_path, str):
            return self.create_placeholder()

        # Fix relative URLs
        if image_path.startswith("//"):
            image_url = "https:" + image_path
        elif image_path.startswith("/") and not image_path.startswith("//"):
            image_url = "https://anilibria.tv" + image_path
        elif image_path.startswith("http"):
            return self.create_placeholder()  # Don't load network images here
        else:
            # Try local file
            base_dir = Path(__file__).parent.parent
            local_path = base_dir / image_path
            if local_path.exists():
                return QPixmap(str(local_path))
        return self.create_placeholder()

    def create_placeholder(self):
        pixmap = QPixmap(240, 360)
        pixmap.fill(QColor(60, 60, 80))
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 255))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Loading...")
        painter.end()
        return pixmap

    def set_placeholder(self):
        self.set_image("")


class AnimeCard(QFrame):
    def __init__(self, parent, data, main_window):
        super().__init__(parent)
        self.data = data
        self.main_window = main_window
        self.setup_ui()
        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):
        self.setFixedSize(240, 360)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background: transparent;
            border-radius: 15px;
            border: none;
        """)

        # Create rounded mask
        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, 15, 15)
        painter.end()
        self.setMask(mask.mask())

        container = QWidget(self)
        container.setGeometry(0, 0, 240, 360)

        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)

        # Add genre label
        self.genre_label = QLabel(self.data.get("genre", "Жанр невідомий"))
        self.genre_label.setAlignment(Qt.AlignCenter)
        self.genre_label.setStyleSheet("""
            color: #FFD700;
            font-size: 12px;
            background: rgba(0, 0, 0, 0.6);
            padding: 3px;
            border-radius: 5px;
        """)
        grid.addWidget(self.genre_label, 0, 0)

        # Image placeholder
        self.rounded_image = RoundedImageLabel()
        grid.addWidget(self.rounded_image, 0, 0)

        title = self.data.get("title", "Назва відсутня")
        if len(title) > 23:
            title = title[:20] + "..."

        self.text_label = QLabel(title)
        self.text_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.text_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            padding: 5px;
            border-radius: 5px;
        """)
        grid.addWidget(self.text_label, 0, 0)

    def update_image(self, pixmap):
        self.rounded_image.set_image("")
        self.rounded_image.set_image(pixmap)

    def mousePressEvent(self, event):
        self.main_window.show_anime_details(self.data)


class ExplorePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.network_manager = QNetworkAccessManager(self)
        self.current_data = []
        self.all_anime_data = []
        self.init_ui()
        self.connect_signals()
        self.load_initial_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        # Search and Filter Panel
        search_filter_layout = QHBoxLayout()
        search_filter_layout.setSpacing(15)

        # Search Field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Пошук аніме, жанрів, студій...")
        self.search_field.setStyleSheet("""
            QLineEdit {
                padding: 12px 20px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
            }
        """)
        search_filter_layout.addWidget(self.search_field, stretch=2)

        # Genre Filter
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Усі жанри")
        self.genre_combo.addItems(["Екшн", "Романтика", "Комедія", "Драма", "Фентезі", "Наукова фантастика",
                                   "Детектив", "Трилер", "Ісекай", "Школа", "Пригоди"])
        self.genre_combo.setStyleSheet("""
            QComboBox {
                padding: 12px 20px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                min-width: 180px;
            }
        """)
        search_filter_layout.addWidget(self.genre_combo, stretch=1)

        # Category Filter
        self.category_combo = QComboBox()
        self.category_combo.addItem("Усі категорії")
        self.category_combo.addItems(["Топ тижня", "Нові релізи", "Популярні", "Класика", "Онгоінги", "Завершені"])
        self.category_combo.setStyleSheet("""
            QComboBox {
                padding: 12px 20px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                min-width: 180px;
            }
        """)
        search_filter_layout.addWidget(self.category_combo, stretch=1)

        main_layout.addLayout(search_filter_layout)

        # Control Panel
        control_panel = QHBoxLayout()
        control_panel.setSpacing(15)

        # Filter Buttons
        filter_buttons = QHBoxLayout()
        filter_buttons.setSpacing(10)

        self.top_btn = QPushButton("🏆 Топ тижня")
        self.top_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                background: rgba(16, 185, 129, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                color: white;
                min-width: 140px;
            }
            QPushButton:hover { background: rgba(16, 185, 129, 0.9); }
            QPushButton:pressed { background: rgba(16, 185, 129, 1.0); }
        """)

        self.random_btn = QPushButton("🎲 Випадкове")
        self.random_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                background: rgba(99, 102, 241, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                color: white;
                min-width: 140px;
            }
            QPushButton:hover { background: rgba(99, 102, 241, 0.9); }
            QPushButton:pressed { background: rgba(99, 102, 241, 1.0); }
        """)

        self.best_by_genre_btn = QPushButton("⭐ Кращі за жанром")
        self.best_by_genre_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                background: rgba(236, 201, 75, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                color: white;
                min-width: 180px;
            }
            QPushButton:hover { background: rgba(236, 201, 75, 0.9); }
            QPushButton:pressed { background: rgba(236, 201, 75, 1.0); }
        """)

        self.true_random_btn = QPushButton("🎭 Випадкові аніме")
        self.true_random_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                background: rgba(155, 89, 182, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.4);
                border-radius: 8px;
                color: white;
                min-width: 180px;
            }
            QPushButton:hover { background: rgba(155, 89, 182, 0.9); }
            QPushButton:pressed { background: rgba(155, 89, 182, 1.0); }
        """)

        filter_buttons.addWidget(self.top_btn)
        filter_buttons.addWidget(self.random_btn)
        filter_buttons.addWidget(self.best_by_genre_btn)
        filter_buttons.addWidget(self.true_random_btn)
        control_panel.addLayout(filter_buttons)
        main_layout.addLayout(control_panel)

        # Cards Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(25)
        scroll_area.setWidget(self.content)
        main_layout.addWidget(scroll_area)

    def connect_signals(self):
        self.top_btn.clicked.connect(self.show_top)
        self.random_btn.clicked.connect(self.show_random)
        self.best_by_genre_btn.clicked.connect(self.show_best_by_genre)
        self.true_random_btn.clicked.connect(self.show_true_random)
        self.search_field.textChanged.connect(self.search_anime)
        self.genre_combo.currentIndexChanged.connect(self.filter_anime)
        self.category_combo.currentIndexChanged.connect(self.filter_anime)

    def load_initial_data(self):
        file_path = Path("data/online/random.json")
        try:
            os.makedirs("data/online", exist_ok=True)

            if not file_path.exists() or file_path.stat().st_size == 0:
                self.load_demo_data()
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    raise ValueError("Empty data file")
                self.all_anime_data = data
                self.create_anime_cards(data)

        except json.JSONDecodeError:
            print("Invalid JSON data, loading demo data")
            self.load_demo_data()
        except Exception as e:
            print(f"Error loading data: {e}, loading demo data")
            self.load_demo_data()

    def create_anime_cards(self, anime_list):
        # Clear existing widgets
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create new cards
        for i, item in enumerate(anime_list[:12]):
            row, col = i // 4, i % 4
            card = AnimeCard(self, item, self.main_window)
            self.grid.addWidget(card, row, col)

            # Load images only if they are network URLs
            if "image" in item and item["image"].startswith("http"):
                self.load_image_async(item["image"], card)

    def load_image_async(self, image_url, card):
        request = QNetworkRequest(QUrl(image_url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self.handle_image_response(reply, card))

    def handle_image_response(self, reply, card):
        if reply.error() == QNetworkReply.NoError:
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            card.update_image(pixmap)
        reply.deleteLater()

    def load_demo_data(self):
        demo_data = [
            {"image": "test.png", "title": "Космічні Мандрівники", "genre": "Фентезі/Пригоди", "rating": 9.2},
            {"image": "test.png", "title": "Таємничий Ліс", "genre": "Детектив/Трилер", "rating": 8.7},
            {"image": "test.png", "title": "Мечі Долі", "genre": "Екшн/Фентезі", "rating": 9.0},
            {"image": "test.png", "title": "Магічний Світ", "genre": "Фентезі/Романтика", "rating": 8.5},
            {"image": "test.png", "title": "Зоряні Війни", "genre": "Наукова фантастика/Екшн", "rating": 9.1},
            {"image": "test.png", "title": "Підземний Світ", "genre": "Трилер/Драма", "rating": 8.3},
            {"image": "test.png", "title": "Небесний Замок", "genre": "Фентезі/Пригоди", "rating": 8.9},
            {"image": "test.png", "title": "Океанські Глибини", "genre": "Наукова фантастика/Трилер", "rating": 8.6},
            {"image": "test.png", "title": "Квіти Сакури", "genre": "Романтика/Драма", "rating": 8.8},
            {"image": "test.png", "title": "Легенда про Дракона", "genre": "Фентезі/Екшн", "rating": 9.3},
            {"image": "test.png", "title": "Темний Лицар", "genre": "Трилер/Екшн", "rating": 8.4},
            {"image": "test.png", "title": "Місто Мрій", "genre": "Драма/Романтика", "rating": 8.7}
        ]
        self.all_anime_data = demo_data
        self.create_anime_cards(demo_data)

    def show_top(self):
        if self.main_window:
            self.main_window.switch_page("home")

    def show_random(self):
        if self.main_window:
            self.main_window.load_random_anime()

    def show_true_random(self):
        """Fetch completely new random anime from API"""
        if self.main_window:
            self.main_window.load_random_anime()

    def show_best_by_genre(self):
        selected_genre = self.genre_combo.currentText()
        if selected_genre == "Усі жанри":
            sorted_data = sorted(self.all_anime_data,
                                 key=lambda x: self.get_rating_value(x),
                                 reverse=True)
            self.create_anime_cards(sorted_data[:12])
            return

        filtered_data = [anime for anime in self.all_anime_data
                         if selected_genre.lower() in anime.get("genre", "").lower()]
        sorted_data = sorted(filtered_data,
                             key=lambda x: self.get_rating_value(x),
                             reverse=True)
        self.create_anime_cards(sorted_data[:12])

    def get_rating_value(self, anime):
        rating = anime.get("rating", 0)
        if isinstance(rating, (int, float)):
            return rating
        try:
            return float(rating)
        except (TypeError, ValueError):
            return 0

    def search_anime(self):
        search_text = self.search_field.text().lower().strip()
        if not search_text:
            self.create_anime_cards(self.all_anime_data[:12])
            return

        filtered_data = [
            anime for anime in self.all_anime_data
            if (search_text in anime.get("title", "").lower() or
                search_text in anime.get("genre", "").lower())
        ]
        self.create_anime_cards(filtered_data[:12])

    def filter_anime(self):
        selected_genre = self.genre_combo.currentText()
        selected_category = self.category_combo.currentText()

        filtered_data = self.all_anime_data

        if selected_genre != "Усі жанри":
            filtered_data = [anime for anime in filtered_data
                             if selected_genre.lower() in anime.get("genre", "").lower()]

        if selected_category != "Усі категорії":
            if selected_category == "Топ тижня":
                filtered_data = sorted(filtered_data,
                                       key=lambda x: self.get_rating_value(x),
                                       reverse=True)
            elif selected_category == "Популярні":
                filtered_data = sorted(filtered_data,
                                       key=lambda x: self.get_rating_value(x),
                                       reverse=True)
            elif selected_category == "Нові релізи":
                filtered_data = filtered_data[:8]
            elif selected_category == "Класика":
                filtered_data = filtered_data[4:12]
            elif selected_category == "Онгоінги":
                filtered_data = filtered_data[:6]
            elif selected_category == "Завершені":
                filtered_data = filtered_data[6:12]

        self.create_anime_cards(filtered_data[:12])