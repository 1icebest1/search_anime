from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QScrollArea,
    QLineEdit, QLabel, QGraphicsView, QGraphicsScene,
    QGraphicsPixmapItem, QGridLayout, QFrame
)
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtCore import Qt


class RoundedImageLabel(QGraphicsView):
    def __init__(self, image_path, radius=20, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent;")
        self.setFixedSize(240, 360)

        pixmap = QPixmap(image_path).scaled(
            240, 360,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        mask = QPixmap(pixmap.size())
        mask.fill(Qt.GlobalColor.transparent)

        painter = QPainter(mask)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRoundedRect(0, 0, pixmap.width(), pixmap.height(), radius, radius)
        painter.end()

        pixmap.setMask(mask.createMaskFromColor(Qt.GlobalColor.transparent))

        scene = QGraphicsScene()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        self.setScene(scene)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)


class AnimeCard(QFrame):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.setup_ui()
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def setup_ui(self):
        self.setFixedSize(240, 360)
        self.setStyleSheet("""
            AnimeCard {
                background: transparent;
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                margin: 15px;
            }
        """)

        container = QWidget(self)
        container.setGeometry(0, 0, 240, 360)

        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)

        rounded_image = RoundedImageLabel(self.data["image"], parent=self)
        grid.addWidget(rounded_image, 0, 0)

        text_label = QLabel(self.data["title"])
        text_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        text_label.setStyleSheet("""
            color: white;
            font-weight: bold;
            background: transparent;
            padding: 10px;
        """)
        text_label.setWordWrap(True)
        grid.addWidget(text_label, 0, 0)


class LibraryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 40)
        layout.setSpacing(25)

        # Пошукова панель
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 Пошук аніме, жанрів, студій...")
        search_bar.setStyleSheet("""
            QLineEdit {
                padding: 16px 28px;
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 14px;
                color: white;
            }
        """)
        layout.addWidget(search_bar)

        # Налаштування вкладок
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: 10px;
            }
            QTabBar {
                background: transparent;
                spacing: 25px;
            }
            QTabBar::tab {
                background: rgba(255,255,255,0.1);
                color: rgba(255,255,255,0.8);
                padding: 18px 30px 12px 30px;
                margin: 0 120px;
                border-radius: 20px;
                min-width: 120px;
                min-height: 45px;
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255,0.2);
                color: white;
            }
        """)

        categories = ["Переглядаю", "Заплановано", "Кинуто", "Завершено"]
        sample_data = {
            "Переглядаю": [{"image": "test.png", "title": f"Переглядаю {i+1}"} for i in range(12)],
            "Заплановано": [{"image": "test.png", "title": f"Заплановано {i+1}"} for i in range(8)],
            "Кинуто": [{"image": "test.png", "title": f"Кинуто {i+1}"} for i in range(5)],
            "Завершено": [{"image": "test.png", "title": f"Завершено {i+1}"} for i in range(10)],
        }

        for status in categories:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet("background: transparent; border: none;")

            content = QWidget()
            grid = QGridLayout(content)
            grid.setContentsMargins(40, 30, 40, 50)
            grid.setHorizontalSpacing(50)
            grid.setVerticalSpacing(50)

            for i, item in enumerate(sample_data[status]):
                grid.addWidget(AnimeCard(self, item), i // 3, i % 3)

            scroll.setWidget(content)
            tabs.addTab(scroll, status)

        layout.addWidget(tabs)