import json
import sys
import random
import os
from PySide6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout,
                               QStackedWidget, QLabel, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QLinearGradient, QPixmap

from side_panel import RoundedPanel
from account import AccountPage
from explore import ExplorePage
from library import LibraryPage
from recommendation import RecommendationPage
from setting import SettingsPage
from help import HelpPage
from detail import DetailPage
from pars import AnimeLoaderThread

from splash import SplashScreen, LoaderThread


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

        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Side panel
        self.panel = RoundedPanel(self)
        self.main_layout.addWidget(self.panel)

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

    def show_anime_details(self, anime_data):
        self.pages["detail"].set_data(anime_data)
        self.switch_page("detail")
        self.pages["detail"].back_callback = lambda: self.switch_page("home")
        self.pages["detail"].main_window = self

    def on_parsing_finished(self):
        self.pages["home"].load_anime_data()
        if self.loading_overlay:
            self.loading_overlay.hide()
            self.loading_overlay.deleteLater()
            self.loading_overlay = None

    def load_random_anime(self):
        """Load random anime data from API with proper error handling"""
        try:
            if not hasattr(self, 'loading_overlay') or not self.loading_overlay:
                self.loading_overlay = LoadingOverlay(self)
            self.loading_overlay.show()

            self.anime_loader = AnimeLoaderThread()
            self.anime_loader.mode = "random"
            self.anime_loader.random_data_loaded.connect(self.handle_random_data)
            self.anime_loader.error_occurred.connect(self.show_error)
            self.anime_loader.finished.connect(lambda: self.loading_overlay.hide())
            self.anime_loader.start()

        except Exception as e:
            print(f"Error starting loader: {e}")
            if self.loading_overlay:
                self.loading_overlay.hide()
            self.show_error(str(e))
            self.pages["explore"].load_demo_data()

    def handle_random_data(self, data):
        """Handle received random anime data"""
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
                          for _ in range(30)]
            self.timer.start(30)
        else:
            self.timer.stop()

    def move_stars(self):
        for i in range(len(self.stars)):
            self.stars[i].setX((self.stars[i].x() + 2) % self.width())
        self.update()

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
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Ensure data directory exists with demo data
    os.makedirs("data/online", exist_ok=True)
    demo_file = os.path.join("data/online", "random.json")
    if not os.path.exists(demo_file) or os.path.getsize(demo_file) == 0:
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
        start_anime_loader()


    def handle_progress(value, message):
        splash.progress_bar.setValue(value)
        splash.status_label.setText(message)
        app.processEvents()
        if value == 100:
            QTimer.singleShot(300, handle_finish)


    def start_anime_loader():
        window.anime_loader = AnimeLoaderThread()
        window.anime_loader.finished.connect(window.on_parsing_finished)
        window.anime_loader.start()


    loader.progress_updated.connect(handle_progress)
    loader.start()

    sys.exit(app.exec())