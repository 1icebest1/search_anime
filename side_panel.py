from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont, QPainter, QPainterPath

class RoundedPanel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.is_open = True
        self.panel_width = 100
        self.handle_width = 30
        self.setup_ui()
        self.setAttribute(Qt.WA_TranslucentBackground)

    def setup_ui(self):
        self.setFixedSize(self.panel_width + self.handle_width, 600)

        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("""
            background: #2b2b2b;
            border-radius: 25px;
            border-left: none;
        """)
        self.main_frame.setGeometry(0, 0, self.panel_width, 600)

        self.handle = QPushButton("❯", self)
        self.handle.setFixedSize(self.handle_width, 60)
        self.handle.setFont(QFont("Arial", 16))
        self.handle.setStyleSheet("""
            QPushButton {
                background: #404040;
                color: white;
                border-radius: 0 8px 8px 0;
                margin-left: -1px;
            }
            QPushButton:hover { background: #505050; }
        """)
        self.handle.move(self.panel_width, 270)
        self.handle.clicked.connect(self.toggle_panel)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        buttons = [
            ("🏠", "home"),
            ("🔍", "explore"),
            ("📚", "library"),
            ("👤", "account"),
            ("⚙️", "settings"),
            ("❓", "help")
        ]

        for icon, page in buttons:
            btn = QPushButton(icon)
            btn.setStyleSheet("""
                QPushButton {
                    background: #404040;
                    color: white;
                    border-radius: 15px;
                    padding: 0;
                    min-width: 50px;
                    min-height: 50px;
                    font-size: 24px;
                }
                QPushButton:hover { background: #505050; }
            """)
            btn.clicked.connect(lambda _, p=page: self.parent.switch_page(p))
            layout.addWidget(btn)

        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.setDuration(700)

    def toggle_panel(self):
        if self.is_open:
            self.animation.setStartValue(QPoint(0, self.y()))
            self.animation.setEndValue(QPoint(-self.panel_width, self.y()))
            self.handle.setText("❮")
        else:
            self.animation.setStartValue(QPoint(-self.panel_width, self.y()))
            self.animation.setEndValue(QPoint(0, self.y()))
            self.handle.setText("❯")
        self.is_open = not self.is_open
        self.animation.start()

    def paintEvent(self, event):
        path = QPainterPath()
        rect = self.rect().adjusted(0, 0, -1, -1)
        radius = 25.0
        path.addRoundedRect(rect, radius, radius)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipPath(path)
        super().paintEvent(event)