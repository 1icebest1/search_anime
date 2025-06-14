from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QGraphicsView, QScrollArea, QLineEdit, QPushButton, QGraphicsScene, QGraphicsPixmapItem
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt, QRectF, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json
import os


class RoundedImageLabel(QGraphicsView):
    def __init__(self, image_path, radius=20, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setStyleSheet("border: none; background: transparent;")
        self.setFixedSize(240, 360)
        self._load_image(image_path, radius)

    def _load_image(self, image_path, radius):
        pixmap = QPixmap(image_path).scaled(240, 360, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, radius, radius)
        painter.end()
        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))
        scene = QGraphicsScene()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        self.setScene(scene)
        self.setAlignment(Qt.AlignCenter)


class AnimeCard(QWidget):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.image_view = None
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(240, 360)
        self.setStyleSheet("""
            background: transparent;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.image_view = RoundedImageLabel("", parent=self)
        layout.addWidget(self.image_view)
        title_label = QLabel(self.data.get("title", "Без назви"))
        title_label.setAlignment(Qt.AlignBottom | Qt.AlignHCenter)
        title_label.setStyleSheet("""
            color: white; font-size: 20px; font-weight: bold;
            background: transparent; padding: 10px;
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

    def update_image(self, pixmap):
        scene = QGraphicsScene()
        scene.addItem(
            QGraphicsPixmapItem(pixmap.scaled(240, 360, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)))
        self.image_view.setScene(scene)


class ExplorePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.network_manager = QNetworkAccessManager(self)
        self.current_data = []
        self.init_ui()
        self.connect_signals()
        self.load_initial_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        # Control Panel
        control_panel = QHBoxLayout()
        control_panel.setSpacing(15)

        # Search Field
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("🔍 Пошук аніме...")
        self.search_field.setStyleSheet("""
            QLineEdit {
                padding: 12px 20px;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 16px;
            }
        """)
        control_panel.addWidget(self.search_field, stretch=1)

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
                font-size: 16px;
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
                font-size: 16px;
                min-width: 140px;
            }
            QPushButton:hover { background: rgba(99, 102, 241, 0.9); }
            QPushButton:pressed { background: rgba(99, 102, 241, 1.0); }
        """)

        filter_buttons.addWidget(self.top_btn)
        filter_buttons.addWidget(self.random_btn)
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

    def load_initial_data(self):
        file_path = os.path.join("data/online", "random.json")
        try:
            os.makedirs("data/online", exist_ok=True)

            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                self.load_demo_data()
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not data:
                    raise ValueError("Empty data file")
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
        for i, item in enumerate(anime_list[:8]):  # Limit to 8 items
            row, col = i // 3, i % 3
            card = AnimeCard(self, item)
            self.grid.addWidget(card, row, col)
            if "image" in item:
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
            {"image": "test.png", "title": "Космічні Мандрівники"},
            {"image": "test.png", "title": "Таємничий Ліс"},
            {"image": "test.png", "title": "Мечі Долі"},
            {"image": "test.png", "title": "Магічний Світ"},
            {"image": "test.png", "title": "Зоряні Війни"},
            {"image": "test.png", "title": "Підземний Світ"},
            {"image": "test.png", "title": "Небесний Замок"},
            {"image": "test.png", "title": "Океанські Глибини"}
        ]
        self.create_anime_cards(demo_data)

    def show_top(self):
        if self.main_window:
            self.main_window.switch_page("home")

    def show_random(self):
        if self.main_window:
            self.main_window.load_random_anime()