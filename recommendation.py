# recommendation.py
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QWidget, QVBoxLayout,
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsView
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt
import json
import os
import requests


class RoundedImageLabel(QGraphicsView):
    def __init__(self, image_path, radius, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self.setFixedSize(240, 360)

        pixmap = self.load_pixmap(image_path)
        pixmap = pixmap.scaled(240, 360, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

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

    def load_pixmap(self, image_path):
        # Додаємо базовий URL для шляхів з anilibria.tv
        if image_path.startswith("/"):
            image_path = f"https://anilibria.tv{image_path}"

        if image_path.startswith("http"):
            try:
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap
            except Exception as e:
                print(f"Помилка завантаження зображення: {e}")
                return QPixmap("images/default_image.jpg")
        else:
            # Обробка локальних шляхів
            full_path = os.path.abspath(image_path)
            if not os.path.exists(full_path):
                return QPixmap("images/default_image.jpg")
            return QPixmap(full_path)


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

        rounded_image = RoundedImageLabel(self.data.get("image", ""), radius=20)
        grid.addWidget(rounded_image, 0, 0)

        title = self.data.get("title", "Назва відсутня")
        if len(title) > 23:
            title = title[:20] + "..."

        text_label = QLabel(title)
        text_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        text_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            font-size: 17px;
            padding: 5px;
            border-radius: 5px;
        """)
        grid.addWidget(text_label, 0, 0)

    def mousePressEvent(self, event):
        self.main_window.show_anime_details(self.data)


class RecommendationPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setStyleSheet("background: transparent;")
        self.anime_list = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(0)

        label = QLabel('RECOMMEND')
        label.setStyleSheet("""
            color: black;
            font-size: 42px;
            font-weight: bold;
            background: transparent;
            margin-bottom: -20px;
        """)
        label.setAlignment(Qt.AlignHCenter)
        label.setMinimumWidth(500)
        layout.addWidget(label, alignment=Qt.AlignTop)

        self.label = label
        self.label.raise_()

        spacer = QWidget()
        spacer.setFixedHeight(60)
        layout.addWidget(spacer)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(50)
        self.grid.setVerticalSpacing(20)
        self.grid.setContentsMargins(0, -50, 0, 100)
        layout.addLayout(self.grid)

        self.load_anime_data()

        self.overlay_label = QLabel("RECOMMEND", self)
        self.overlay_label.setStyleSheet("""
            color: black;
            font-size: 42px;
            font-weight: bold;
            background: transparent;
        """)
        self.overlay_label.setFixedHeight(60)
        self.overlay_label.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_label.setGeometry(0, 0, self.width(), 60)
        self.overlay_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.overlay_label.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_label.setGeometry(0, 0, self.width(), 60)

    def load_anime_data(self):
        for i in reversed(range(self.grid.count())):
            if widget := self.grid.itemAt(i).widget():
                widget.deleteLater()

        file_path = "data/online/rec_anime.json"
        self.anime_list = []

        try:
            if not os.path.exists(file_path):
                return

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return

                self.anime_list = json.loads(content)
                if not isinstance(self.anime_list, list):
                    raise ValueError("Дані не є списком")

            for i, anime in enumerate(self.anime_list[:8]):
                card = AnimeCard(self, anime, self.parent)
                self.grid.addWidget(card, i // 4, i % 4)

        except Exception as e:
            print(f"Помилка: {e}")