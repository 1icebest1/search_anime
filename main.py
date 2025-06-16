import json
import sys
import random
import os
from pathlib import Path

from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                               QStackedWidget, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPixmap, QFontDatabase, QFont

from menu.side_panel import RoundedPanel
from menu.account import AccountPage
from menu.explore import ExplorePage
from menu.library import LibraryPage
from menu.recommendation import RecommendationPage
from menu.setting import SettingsPage
from menu.help import HelpPage
from menu.detail import DetailPage

from script.pars import AnimeLoaderThread
from script.splash import SplashScreen, LoaderThread

# Get absolute path to data directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "online"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 120);")
        self.resize(parent.size())
        self.move(0, 0)
        self.show()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Viewer")
        self.setGeometry(200, 0, 1366, 768)

        # Theme and effects
        self.current_theme = "space"
        self.stars = []
        self.background_pixmap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_stars)
        self.anime_loader = None
        self.loading_overlay = None
        self.star_count = 15

        # Font management
        self.current_font = "Anime Ace"
        self.available_fonts = []
        self.load_custom_fonts()
        self.apply_font(self.current_font)

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Side panel
        self.panel = RoundedPanel(self)
        self.main_layout.addWidget(self.panel)
        self.panel.apply_theme(self.current_theme)
        self.panel.setFixedWidth(self.panel.panel_width + self.panel.handle_width)

        # Content area
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.stacked_widget = QStackedWidget()

        # Pages
        self.pages = {
            "home": RecommendationPage(self),
            "explore": ExplorePage(self),
            "library": LibraryPage(self),
            "account": AccountPage(),
            "settings": SettingsPage(self),
            "help": HelpPage(),
            "detail": DetailPage()
        }

        for name, widget in self.pages.items():
            self.stacked_widget.addWidget(widget)

        self.content_layout.addWidget(self.stacked_widget)
        self.main_layout.addWidget(self.content_area)

        # Connect signals
        self.pages["detail"].back_callback = lambda: self.switch_page("home")
        self.switch_page("home")

        # Initialize theme
        QTimer.singleShot(100, lambda: self.apply_theme("space"))

    def propagate_font(self, widget=None):
        widget = widget or self
        try:
            widget.setFont(QFont(self.current_font))
        except:
            pass

        for child in widget.children():
            if isinstance(child, QWidget):
                self.propagate_font(child)

    def load_custom_fonts(self):
        fonts_dir = BASE_DIR / "data" / "fonts"
        self.available_fonts = []

        anime_fonts = [
            "anime-ace.bold.ttf",
            "anime-ace.italic.ttf",
            "anime-ace.regular.ttf"
        ]

        if fonts_dir.exists() and fonts_dir.is_dir():
            for font_file in anime_fonts:
                font_path = fonts_dir / font_file
                if font_path.exists():
                    try:
                        font_id = QFontDatabase.addApplicationFont(str(font_path))
                        if font_id != -1:
                            families = QFontDatabase.applicationFontFamilies(font_id)
                            if families:
                                for family in families:
                                    if family not in self.available_fonts:
                                        self.available_fonts.append(family)
                    except:
                        pass

            for ext in ["*.ttf", "*.otf"]:
                for font_file in fonts_dir.glob(ext):
                    if font_file.name not in anime_fonts:
                        try:
                            font_id = QFontDatabase.addApplicationFont(str(font_file))
                            if font_id != -1:
                                families = QFontDatabase.applicationFontFamilies(font_id)
                                if families:
                                    for family in families:
                                        if family not in self.available_fonts:
                                            self.available_fonts.append(family)
                        except:
                            pass

        if not self.available_fonts:
            self.available_fonts.extend(["Arial", "Times New Roman", "Courier New", "Comic Sans MS"])

        self.available_fonts = sorted(set(self.available_fonts))

    def apply_font(self, font_name):
        self.current_font = font_name
        font = QFont(font_name)
        QApplication.instance().setFont(font)
        self.propagate_font()

    def show_anime_details(self, anime_data):
        detail_page = self.pages["detail"]
        detail_page.set_data(anime_data)
        detail_page.apply_theme(self.current_theme)
        self.switch_page("detail")
        detail_page.back_callback = lambda: self.switch_page("home")
        detail_page.main_window = self

    def on_parsing_finished(self):
        self.pages["home"].load_anime_data()
        self.cleanup_loader()

    def load_random_anime(self):
        try:
            # Only create new overlay if needed
            if not hasattr(self, 'loading_overlay') or not self.loading_overlay:
                self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.show()

            # Create new loader instance for random anime
            random_loader = AnimeLoaderThread()
            random_loader.mode = "random"
            random_loader.random_data_loaded.connect(self.handle_random_data)
            random_loader.error_occurred.connect(self.show_error)
            random_loader.finished.connect(self.cleanup_loader)
            random_loader.start()

        except Exception as e:
            self.cleanup_loader()
            self.show_error(str(e))
            self.pages["explore"].load_demo_data()

    def cleanup_loader(self):
        """Clean up loader resources"""
        if self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.deleteLater()
            self.loading_overlay = None

    def handle_random_data(self, data):
        self.pages["explore"].create_anime_cards(data)

    def show_error(self, message):
        QMessageBox.critical(self, "Error",
                             f"An error occurred:\n{message}\n\nLoading demo data instead.")

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        theme_styles = {
            "dark": """
                * { color: white; }
                QWidget { background: #1a1a1a; }
                QFrame, QPushButton, QComboBox, QLineEdit { 
                    background: #404040;
                    border-radius: 15px;
                }
                QPushButton:hover { background: #505050; }
            """,
            "light": """
                * { color: #333; }
                QWidget { background: #f0f0f0; }
                QFrame, QPushButton, QComboBox, QLineEdit {
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 15px;
                }
                QPushButton:hover { background: #f0f0f0; }
            """,
            "space": """
                * { color: white; }
                QFrame, QPushButton, QComboBox, QLineEdit {
                    background: rgba(43, 43, 43, 200);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                }
                QPushButton:hover { background: rgba(65, 65, 65, 200); }
            """
        }
        self.setStyleSheet(theme_styles[theme_name])
        self.update_background_pixmap()
        self.update_space_effect()
        self.panel.apply_theme(theme_name)
        self.propagate_font()

        if "detail" in self.pages:
            self.pages["detail"].apply_theme(theme_name)

    def update_background_pixmap(self):
        if self.current_theme == "space" and self.width() > 0 and self.height() > 0:
            self.background_pixmap = QPixmap(self.size())
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor("#0c1445"))
            gradient.setColorAt(0.5, QColor("#301959"))
            gradient.setColorAt(1, QColor("#5a1464"))

            painter = QPainter(self.background_pixmap)
            painter.fillRect(QRect(0, 0, self.width(), self.height()), gradient)
            painter.end()

    def update_space_effect(self):
        if self.current_theme == "space":
            self.stars = [QPoint(random.randint(0, self.width()),
                             random.randint(0, self.height()))
                      for _ in range(self.star_count)]
            self.timer.start(50)
        else:
            self.timer.stop()

    def move_stars(self):
        if self.isVisible() and self.current_theme == "space":
            for i in range(len(self.stars)):
                self.stars[i].setX((self.stars[i].x() + 2) % self.width())
            self.update()
        else:
            self.timer.stop()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_background_pixmap()
        if self.current_theme == "space":
            self.update_space_effect()

    def paintEvent(self, event):
        if self.current_theme == "space":
            painter = QPainter(self)
            if self.background_pixmap:
                painter.drawPixmap(0, 0, self.background_pixmap)
            painter.setPen(QColor(255, 255, 255, 200))
            painter.drawPoints(self.stars)
        else:
            super().paintEvent(event)

    def switch_page(self, page_name):
        self.stacked_widget.setCurrentWidget(self.pages[page_name])


if __name__ == "__main__":
    # Configure high DPI settings properly
    if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)

    # Create demo data with absolute path
    demo_file = DATA_DIR / "random.json"
    if not demo_file.exists() or os.path.getsize(demo_file) == 0:
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
        with open(demo_file, 'w', encoding='utf-8') as f:
            json.dump(demo_data, f, ensure_ascii=False, indent=2)

    # Splash screen
    splash = SplashScreen()
    splash.show()
    app.processEvents()

    # Main window
    window = MainWindow()
    window.setVisible(False)

    loader = LoaderThread()


    def handle_finish():
        splash.close()
        window.showMaximized()
        window.activateWindow()

        # Create and start loader
        window.anime_loader = AnimeLoaderThread()
        window.anime_loader.error_occurred.connect(window.show_error)
        window.anime_loader.finished.connect(window.on_parsing_finished)
        window.anime_loader.mode = "top"
        window.anime_loader.start()


    def handle_progress(value, message):
        splash.progress_bar.setValue(value)
        splash.status_label.setText(message)
        app.processEvents()
        if value == 100:
            QTimer.singleShot(300, handle_finish)


    loader.progress_updated.connect(handle_progress)
    loader.start()

    sys.exit(app.exec())