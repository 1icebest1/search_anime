# detail.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QComboBox, QScrollArea, QLabel, QApplication
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath
from PySide6.QtCore import Qt, QRectF
import requests
import sys
import os


class RoundedImageWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap()
        self.radius = 20

    def set_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(path)

        if not self.pixmap.isNull():
            scaled = self.pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)


class DetailPage(QWidget):
    def __init__(self):
        super().__init__()
        self.back_callback = None
        self.setup_ui()
        self.setStyleSheet("""
            background: #1A1A1A;
            QScrollArea { border: none; }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Кнопка "Назад"
        btn_back = QPushButton("← Назад")
        btn_back.setFixedHeight(40)
        btn_back.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                font-size: 16px;
                border-radius: 15px;
                background: #333333;
                padding: 0 20px;
            }
            QPushButton:hover { background: #444444; }
        """)
        btn_back.clicked.connect(self.go_back)
        layout.addWidget(btn_back, alignment=Qt.AlignLeft)

        # Головний контейнер
        main_container = QHBoxLayout()
        main_container.setSpacing(40)

        # Зображення
        self.poster = RoundedImageWidget()
        self.poster.setMinimumSize(600, 800)
        main_container.addWidget(self.poster, alignment=Qt.AlignTop)

        # Права колонка
        right_col = QVBoxLayout()
        right_col.setSpacing(25)

        # Заголовок
        self.title = QLabel()
        self.title.setStyleSheet("""
            color: #FFFFFF;
            font-size: 34px;
            font-weight: bold;
            padding: 15px;
            border-radius: 15px;
            background: #333333;
        """)
        self.title.setWordWrap(True)
        right_col.addWidget(self.title)

        # Інформаційний блок
        info_container = QWidget()
        info_container.setStyleSheet("background: #333333; border-radius: 15px;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(20, 15, 20, 15)
        info_layout.setSpacing(12)

        self.genre = QLabel()
        self.genre.setStyleSheet("color: #AAAAAA; font-size: 20px;")

        self.status = QLabel()
        self.status.setStyleSheet("""
            color: #FFFFFF;
            font-size: 18px;
            padding: 10px 15px;
            border-radius: 10px;
            background: #444444;
        """)

        info_layout.addWidget(self.genre)
        info_layout.addWidget(self.status)
        right_col.addWidget(info_container)

        # Керування
        ctrl_container = QWidget()
        ctrl_container.setStyleSheet("background: #333333; border-radius: 15px;")
        ctrl_layout = QHBoxLayout(ctrl_container)
        ctrl_layout.setContentsMargins(15, 15, 15, 15)
        ctrl_layout.setSpacing(20)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Переглядаю", "Заплановано", "Кинуто", "Завершено"])
        self.status_combo.setStyleSheet("""
            QComboBox {
                color: #FFFFFF;
                background: #444444;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 16px;
                min-width: 200px;
            }
            QComboBox::drop-down { border: none; }
        """)

        self.watch_btn = QPushButton("Дивитись")
        self.watch_btn.setStyleSheet("""
            QPushButton {
                color: #FFFFFF;
                background: #00AA00;
                padding: 12px 40px;
                border-radius: 10px;
                font-size: 18px;
            }
            QPushButton:hover { background: #009900; }
        """)

        ctrl_layout.addWidget(self.status_combo)
        ctrl_layout.addWidget(self.watch_btn)
        right_col.addWidget(ctrl_container)

        # Опис
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        desc_container = QWidget()
        desc_container.setStyleSheet("""
            background: #333333;
            border-radius: 15px;
            padding: 20px;
        """)
        desc_layout = QVBoxLayout(desc_container)

        self.description = QLabel()
        self.description.setStyleSheet("""
            color: #AAAAAA;
            font-size: 18px;
            line-height: 1.6;
        """)
        self.description.setWordWrap(True)
        desc_layout.addWidget(self.description)

        scroll_area.setWidget(desc_container)
        right_col.addWidget(scroll_area)

        main_container.addLayout(right_col)
        layout.addLayout(main_container)

    def set_data(self, data):
        # Оновлено: Динамічне масштабування + обробка помилок
        pixmap = QPixmap()
        image_path = data.get("image", "")

        try:
            if image_path.startswith("http"):
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                pixmap.loadFromData(response.content)
            elif image_path.startswith("/"):
                full_url = f"https://anilibria.tv{image_path}"
                response = requests.get(full_url, timeout=10)
                response.raise_for_status()
                pixmap.loadFromData(response.content)
            else:
                if os.path.exists(image_path):
                    pixmap.load(image_path)
                else:
                    raise FileNotFoundError
        except Exception as e:
            print(f"Помилка завантаження: {e}")
            pixmap = QPixmap("images/default_image.jpg")

        if pixmap.isNull():
            pixmap = QPixmap("images/default_image.jpg")

        # Масштабування під розмір віджета
        self.poster.set_pixmap(pixmap.scaled(
            self.poster.width(),
            self.poster.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

        self.title.setText(data.get("title", "Назва відсутня"))
        self.genre.setText(f"Жанр: {data.get('genre', 'Невідомо')}")
        self.status.setText(f"Статус: {data.get('status', 'Невідомо')}")
        self.description.setText(data.get("description", "Опис відсутній") * 5)

    def set_data_with_loading(self, data):
        pixmap = load_pixmap(data.get("image", ""))
        self.poster.set_pixmap(pixmap.scaled(
            self.poster.width(),
            self.poster.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.title.setText(data.get("title", "Назва відсутня"))
        self.genre.setText(f"Жанр: {data.get('genre', 'Невідомо')}")
        self.status.setText(f"Статус: {data.get('status', 'Невідомо')}")
        self.description.setText(data.get("description", "Опис відсутній") * 5)

    def start_watching(self):
        print(f"Початок перегляду: {self.title.text()}")

    def go_back(self):
        if self.back_callback:
            self.back_callback()


def load_pixmap(image_path):
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
        full_path = os.path.abspath(image_path)
        if not os.path.exists(full_path):
            return QPixmap("images/default_image.jpg")
        return QPixmap(full_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("AniLib TV")
    window.resize(1600, 900)

    test_data = {
        "title": "Цікава назва аніме",
        "image": "https://anilibria.tv/storage/releases/posters/9903/QtaSwQk5aeBqf7KrvGQD60cqRMG4eCgA.jpg",
        "genre": "Фентезі, Драма",
        "status": "Онґоїнг",
        "description": "Захоплюючий сюжет з несподіваними поворотами подій... "
    }

    page = DetailPage()
    page.set_data_with_loading(test_data)
    window.setLayout(QVBoxLayout())
    window.layout().addWidget(page)
    window.show()
    sys.exit(app.exec())