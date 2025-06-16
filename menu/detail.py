from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QComboBox, QScrollArea, QLabel, QTextBrowser
)
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PySide6.QtCore import Qt, QRectF, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply


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
        self.main_window = None
        self.theme = "space"
        self.setup_ui()
        self.network_manager = QNetworkAccessManager(self)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        self.btn_back = QPushButton("← Назад")
        self.btn_back.setFixedHeight(40)
        self.btn_back.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                padding: 0 20px;
            }
            QPushButton:hover { background: #444444; }
        """)
        self.btn_back.clicked.connect(self.go_back)
        layout.addWidget(self.btn_back, alignment=Qt.AlignLeft)

        main_container = QHBoxLayout()
        main_container.setSpacing(40)

        self.poster = RoundedImageWidget()
        self.poster.setMinimumSize(600, 800)
        main_container.addWidget(self.poster, alignment=Qt.AlignTop)

        right_col = QVBoxLayout()
        right_col.setSpacing(25)

        self.title = QLabel()
        self.title.setStyleSheet("""
            font-weight: bold;
            padding: 15px;
            border-radius: 15px;
        """)
        self.title.setWordWrap(True)
        right_col.addWidget(self.title)

        info_container = QWidget()
        info_container.setObjectName("infoContainer")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(20, 15, 20, 15)
        info_layout.setSpacing(12)

        self.genre = QLabel()
        self.genre.setObjectName("genreLabel")
        self.status = QLabel()
        self.status.setObjectName("statusLabel")
        self.status.setStyleSheet("""
            padding: 10px 15px;
            border-radius: 10px;
        """)

        info_layout.addWidget(self.genre)
        info_layout.addWidget(self.status)
        right_col.addWidget(info_container)

        ctrl_container = QWidget()
        ctrl_container.setObjectName("ctrlContainer")
        ctrl_layout = QHBoxLayout(ctrl_container)
        ctrl_layout.setContentsMargins(15, 15, 15, 15)
        ctrl_layout.setSpacing(20)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Переглядаю", "Заплановано", "Кинуто", "Завершено"])
        self.status_combo.setStyleSheet("""
            QComboBox {
                border-radius: 10px;
                padding: 12px 20px;
                min-width: 200px;
            }
            QComboBox::drop-down { border: none; }
        """)

        self.watch_btn = QPushButton("Дивитись")
        self.watch_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 40px;
                border-radius: 10px;
            }
            QPushButton:hover { background: #009900; }
        """)

        ctrl_layout.addWidget(self.status_combo)
        ctrl_layout.addWidget(self.watch_btn)
        right_col.addWidget(ctrl_container)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.desc_container = QWidget()
        self.desc_container.setObjectName("descContainer")
        self.desc_layout = QVBoxLayout(self.desc_container)
        self.desc_layout.setContentsMargins(20, 20, 20, 20)

        self.description = QTextBrowser()
        self.description.setObjectName("descriptionText")
        self.description.setOpenExternalLinks(True)
        self.description.setStyleSheet("""
            background: transparent;
            border: none;
            font-size: 28px;
            line-height: 1.6;
        """)
        self.description.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.description.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.desc_layout.addWidget(self.description)
        self.scroll_area.setWidget(self.desc_container)
        right_col.addWidget(self.scroll_area)

        main_container.addLayout(right_col)
        layout.addLayout(main_container)

        self.apply_theme(self.theme)

    def set_data(self, data):
        self.title.setText(data.get("title", "Назва відсутня"))
        self.genre.setText(f"Жанр: {data.get('genre', 'Невідомо')}")
        self.status.setText(f"Статус: {data.get('status', 'Невідомо')}")
        self.description.setText(data.get("description", "Опис відсутній"))

        image_path = data.get("image", "")
        self.load_image_async(image_path)

        if self.main_window:
            self.apply_font(self.main_window.current_font)

    def apply_theme(self, theme_name):
        self.theme = theme_name
        theme_styles = {
            "dark": {
                "container": "background: #333333;",
                "text": "color: #AAAAAA;",
                "button": "background: #444444; color: white;",
                "watch_btn": "background: #00AA00; color: white;",
                "title_bg": "background: #333333;"
            },
            "light": {
                "container": "background: #f0f0f0;",
                "text": "color: #333333;",
                "button": "background: #e0e0e0; color: #222222;",
                "watch_btn": "background: #00AA00; color: white;",
                "title_bg": "background: #e0e0e0;"
            },
            "space": {
                "container": "background: rgba(43, 43, 43, 200);",
                "text": "color: #AAAAAA;",
                "button": "background: rgba(65, 65, 65, 200); color: white;",
                "watch_btn": "background: #00AA00; color: white;",
                "title_bg": "background: rgba(43, 43, 43, 200);"
            }
        }

        style = theme_styles.get(theme_name, theme_styles["space"])

        # Apply styles to containers
        container_style = f"""
            #infoContainer, #ctrlContainer, #descContainer {{
                {style['container']}
                border-radius: 15px;
            }}
            #genreLabel, #statusLabel, #descriptionText {{
                {style['text']}
            }}
            .QPushButton {{
                {style['button']}
            }}
            #titleLabel {{
                {style['title_bg']}
                {style['text']}
            }}
        """

        self.setStyleSheet(container_style)

        # Special style for watch button
        self.watch_btn.setStyleSheet(f"""
            QPushButton {{
                {style['watch_btn']}
                padding: 12px 40px;
                border-radius: 10px;
            }}
            QPushButton:hover {{ background: #009900; }}
        """)

        # Style for back button
        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                {style['button']}
                border-radius: 15px;
                padding: 0 20px;
            }}
            QPushButton:hover {{ background: #444444; }}
        """)

        # Style for title
        self.title.setStyleSheet(f"""
            font-weight: bold;
            padding: 15px;
            border-radius: 15px;
            {style['title_bg']}
            {style['text']}
        """)

    def apply_font(self, font_name):
        base_font = QFont(font_name)
        base_font.setPointSize(12)

        bold_font = QFont(font_name)
        bold_font.setBold(True)
        bold_font.setPointSize(14)

        desc_font = QFont(font_name)
        desc_font.setPointSize(20)

        self.btn_back.setFont(base_font)
        self.title.setFont(bold_font)
        self.genre.setFont(base_font)
        self.status.setFont(bold_font)
        self.status_combo.setFont(base_font)
        self.watch_btn.setFont(base_font)

        for i in range(self.status_combo.count()):
            self.status_combo.setItemData(i, base_font, Qt.FontRole)

        self.description.setFont(desc_font)
        self.description.setStyleSheet(f"""
            background: transparent;
            border: none;
            font-size: 24pt;
            font-family: "{font_name}";
        """)

    def load_image_async(self, image_path):
        if not image_path:
            self.set_default_image()
            return

        if image_path.startswith("http") or image_path.startswith("/"):
            url = self.resolve_url(image_path)
            request = QNetworkRequest(QUrl(url))
            reply = self.network_manager.get(request)
            reply.finished.connect(lambda: self.handle_image_response(reply))
        else:
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.set_default_image()
            else:
                self.set_poster_pixmap(pixmap)

    def resolve_url(self, path):
        if path.startswith("//"):
            return "https:" + path
        elif path.startswith("/"):
            return "https://anilibria.tv" + path
        return path

    def handle_image_response(self, reply):
        if reply.error() == QNetworkReply.NoError:
            pixmap = QPixmap()
            pixmap.loadFromData(reply.readAll())
            self.set_poster_pixmap(pixmap)
        else:
            self.set_default_image()
        reply.deleteLater()

    def set_poster_pixmap(self, pixmap):
        if pixmap.isNull():
            self.set_default_image()
            return

        scaled = pixmap.scaled(
            self.poster.width(),
            self.poster.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.poster.set_pixmap(scaled)

    def set_default_image(self):
        pixmap = QPixmap("images/default_image.jpg")
        if pixmap.isNull():
            pixmap = QPixmap(600, 800)
            pixmap.fill(QColor(60, 60, 80))
        self.set_poster_pixmap(pixmap)

    def start_watching(self):
        pass

    def go_back(self):
        if self.back_callback:
            self.back_callback()