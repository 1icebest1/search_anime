from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QWidget, QVBoxLayout,
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsView
)
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtCore import Qt
import json
import os
import requests
from pathlib import Path


class RoundedImageLabel(QGraphicsView):
    def __init__(self, image_path, radius, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self.setFixedSize(240, 360)

        pixmap = self.load_pixmap(image_path)
        pixmap = pixmap.scaled(240, 360, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # Create mask for rounded corners
        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, radius, radius)
        painter.end()

        # Apply mask1
        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))

        scene = QGraphicsScene()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        self.setScene(scene)
        self.setAlignment(Qt.AlignCenter)

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
            image_url = image_path
        else:
            # Try local file
            base_dir = Path(__file__).parent.parent
            local_path = base_dir / image_path
            if local_path.exists():
                return QPixmap(str(local_path))
            return self.create_placeholder()

        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            pixmap = QPixmap()
            pixmap.loadFromData(response.content)
            if pixmap.isNull():
                return self.create_placeholder()
            return pixmap
        except Exception as e:
            print(f"Помилка завантаження зображення: {e}")
            return self.create_placeholder()

    def create_placeholder(self):
        pixmap = QPixmap(240, 360)
        pixmap.fill(QColor(60, 60, 80))
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 255))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "Image\nNot Found")
        painter.end()
        return pixmap


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

        # Ensure image exists
        if "image" not in self.data:
            self.data["image"] = "default.jpg"

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
        # Clear existing widgets
        for i in reversed(range(self.grid.count())):
            widget = self.grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        file_path = "data/online/rec_anime.json"
        self.anime_list = []

        try:
            base_dir = Path(__file__).parent.parent
            full_path = base_dir / file_path

            if not full_path.exists():
                raise FileNotFoundError("Data file not found")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    raise ValueError("Empty data file")

                self.anime_list = json.loads(content)
                if not isinstance(self.anime_list, list):
                    raise ValueError("Data is not a list")

            # Create cards
            for i, anime in enumerate(self.anime_list[:8]):
                if not isinstance(anime, dict):
                    continue

                # Ensure required fields
                if "image" not in anime:
                    anime["image"] = "default.jpg"
                if "title" not in anime:
                    anime["title"] = "Unknown Title"

                card = AnimeCard(self, anime, self.parent)
                self.grid.addWidget(card, i // 4, i % 4)

        except Exception as e:
            print(f"Помилка: {e}")
            # Create placeholder cards
            for i in range(8):
                card = AnimeCard(self, {
                    "title": f"Placeholder {i + 1}",
                    "image": "default.jpg"
                }, self.parent)
                self.grid.addWidget(card, i // 4, i % 4)