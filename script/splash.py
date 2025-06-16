import sys
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication, QSizePolicy
from PySide6.QtCore import Qt, QPropertyAnimation, Property, QThread, Signal, QEvent
from PySide6.QtGui import QPixmap, QPainter, QColor, QLinearGradient, QFont, QCursor
from pathlib import Path


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        # Налаштування вікна
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.WindowDoesNotAcceptFocus |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedSize(800, 600)
        self.show_background = False

        # Налаштування курсора
        self.setCursor(QCursor(Qt.BlankCursor))
        self.setMouseTracking(True)
        self.installEventFilter(self)

        # Основний лейаут
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.addStretch(1)  # Верхній розтягувач

        # Логотип
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.load_image("data/images/nekoice.png")
        layout.addWidget(self.logo_label)

        # Прогрес-бар
        self.progress_bar = AnimatedProgressBar()
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        # Статусний текст
        self.status_label = QLabel("Ініціалізація системи...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 16px;
            font-weight: 500;
        """)
        layout.addWidget(self.status_label)

        layout.addStretch(1)  # Нижній розтягувач
        self.recursive_disable(self)
        self.center_on_screen()

    def recursive_disable(self, widget):
        widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        widget.setFocusPolicy(Qt.NoFocus)
        widget.setContextMenuPolicy(Qt.NoContextMenu)
        widget.setToolTip("")
        for child in widget.findChildren(QWidget):
            self.recursive_disable(child)

    def eventFilter(self, obj, event):
        if event.type() in {
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
            QEvent.MouseButtonDblClick,
            QEvent.Wheel,
            QEvent.KeyPress,
            QEvent.KeyRelease,
            QEvent.HoverEnter,
            QEvent.HoverLeave,
            QEvent.HoverMove,
            QEvent.FocusIn,
            QEvent.FocusOut,
            QEvent.WindowActivate,
            QEvent.WindowDeactivate
        }:
            return True
        return super().eventFilter(obj, event)

    def load_image(self, path):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = self.create_placeholder()
        self.logo_label.setPixmap(pixmap.scaled(
            400, 400,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def create_placeholder(self):
        pixmap = QPixmap(400, 400)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 255))
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "NEKO ICE")
        painter.end()
        return pixmap

    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + (screen.height() - self.height()) // 2
        self.move(x, y)

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def paintEvent(self, event):
        if self.show_background:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            gradient = QLinearGradient(0, 0, self.width(), self.height())
            gradient.setColorAt(0, QColor(30, 30, 50, 220))
            gradient.setColorAt(1, QColor(50, 40, 60, 220))
            painter.fillRect(self.rect(), gradient)


class AnimatedProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setRange(0, 100)
        self.setMinimumHeight(14)
        self.setMaximumWidth(600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setTextVisible(False)

        self._glow_value = 0.0
        self.animation = QPropertyAnimation(self, b"glow_value")
        self.animation.setDuration(1000)
        self.animation.setLoopCount(-1)
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.setBrush(QColor(50, 50, 70, 150))
        painter.drawRoundedRect(self.rect(), 7, 7)

        # Progress
        progress_width = int(self.width() * (self.value() / 100))
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(100, 150, 255))
        gradient.setColorAt(1, QColor(200, 100, 255))
        painter.setBrush(gradient)
        painter.drawRoundedRect(0, 0, progress_width, self.height(), 7, 7)

        # Animation
        painter.setPen(QColor(255, 255, 255, int(80 * self._glow_value)))
        painter.drawRoundedRect(self.rect(), 7, 7)

    def get_glow_value(self):
        return self._glow_value

    def set_glow_value(self, value):
        self._glow_value = value
        self.update()

    glow_value = Property(float, get_glow_value, set_glow_value)


class LoaderThread(QThread):
    progress_updated = Signal(int, str)
    finished = Signal()

    def run(self):
        stages = [
            ("Перевірка системних ресурсів...", 15),
            ("Завантаження конфігурацій...", 30),
            ("Ініціалізація ядра...", 45),
            ("Підготовка інтерфейсу...", 60),
            ("Завантаження аніме-даних...", 80),
            ("Оптимізація продуктивності...", 95),
            ("Готово до використання!", 100)
        ]

        for message, progress in stages:
            self.msleep(350)
            self.progress_updated.emit(progress, message)

        self.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    loader = LoaderThread()
    loader.progress_updated.connect(splash.update_progress)
    loader.finished.connect(splash.close)
    loader.start()

    sys.exit(app.exec())