from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QPainterPath, QIcon, QColor
from pathlib import Path


class RoundedPanel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.is_open = True
        self.panel_width = 100
        self.handle_width = 30
        self.active_button = None
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setup_ui()

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 0)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

    def setup_ui(self):
        self.setFixedHeight(600)
        self.setMinimumWidth(self.handle_width)
        self.setMaximumWidth(self.panel_width + self.handle_width)

        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setGeometry(0, 0, self.panel_width, 600)

        self.handle = QPushButton("❯", self)
        self.handle.setObjectName("panelHandle")
        self.handle.setFixedSize(self.handle_width, 60)
        self.handle.setStyleSheet("font-size: 16px;")
        self.handle.clicked.connect(self.toggle_panel)

        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)

        base_dir = Path(__file__).parent.parent
        buttons = [
            ("home.png", "home"),
            ("compass.png", "explore"),
            ("library.png", "library"),
            ("profile.png", "account"),
            ("setting.png", "settings"),
            ("help.png", "help")
        ]

        self.buttons = []

        for icon_name, page in buttons:
            btn = QPushButton()
            btn.setObjectName("panelButton")
            btn.setToolTip(page.capitalize())
            btn.setFixedSize(72, 72)

            icon_path = base_dir / "data" / "pic_sys" / icon_name
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
                btn.setIconSize(QSize(48, 48))
            else:
                btn.setText(page)

            btn.clicked.connect(lambda _, p=page, b=btn: self.handle_button_click(p, b))
            layout.addWidget(btn)
            self.buttons.append(btn)

        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(500)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)

        self.apply_theme(self.parent.current_theme)

    def handle_button_click(self, page, button):
        if self.active_button:
            self.active_button.setProperty("active", False)
            self.active_button.style().unpolish(self.active_button)
            self.active_button.style().polish(self.active_button)

        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)
        self.active_button = button

        self.parent.switch_page(page)

    def apply_theme(self, theme_name):
        theme_styles = {
            "dark": """
                #mainFrame {
                    background: #2b2b2b;
                    border-radius: 25px;
                }
                #panelButton {
                    background: #404040;
                    color: white;
                    border-radius: 36px;
                    padding: 8px;
                }
                #panelButton:hover {
                    background: #505050;
                }
                #panelButton[active="true"] {
                    background: #607d8b;
                    border: 2px solid #90a4ae;
                }
            """,
            "space": """
                #mainFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(30, 30, 30, 0.9),
                        stop:1 rgba(50, 50, 50, 0.9));
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 25px;
                }
                #panelButton {
                    background: rgba(65, 65, 65, 0.85);
                    color: white;
                    border-radius: 36px;
                    padding: 8px;
                }
                #panelButton:hover {
                    background: rgba(90, 90, 90, 0.95);
                }
                #panelButton[active="true"] {
                    background: rgba(130, 170, 255, 0.3);
                    border: 2px solid rgba(130, 170, 255, 0.5);
                }
            """,
            "light": """
                #mainFrame {
                    background: #f0f0f0;
                    border-radius: 25px;
                    border: 1px solid #ccc;
                }
                #panelButton {
                    background: white;
                    color: #333333;
                    border-radius: 36px;
                    padding: 8px;
                    border: 1px solid transparent;
                }
                #panelButton:hover {
                    background: #e0e0e0;
                    border-color: #999999;
                }
                #panelButton[active="true"] {
                    background: #d0e4ff;
                    border: 2px solid #7aaaff;
                    color: #003366;
                }
            """
        }

        common_handle_style = """
            #panelHandle {
                background: #505050;
                color: white;
                border-radius: 0 8px 8px 0;
                border: none;
                padding: 0;
            }
            #panelHandle:hover {
                background: #606060;
            }
        """

        full_style = theme_styles.get(theme_name, "") + common_handle_style
        self.setStyleSheet(full_style)

    def toggle_panel(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.animation.setStartValue(self.handle_width)
            self.animation.setEndValue(self.panel_width + self.handle_width)
            self.handle.setText("❯")
        else:
            self.animation.setStartValue(self.panel_width + self.handle_width)
            self.animation.setEndValue(self.handle_width)
            self.handle.setText("❮")
        self.animation.start()

    def resizeEvent(self, event):
        width = event.size().width()
        height = event.size().height()
        self.main_frame.setFixedWidth(max(0, width - self.handle_width))
        self.handle.move(width - self.handle_width, (height - self.handle.height()) // 2)
        super().resizeEvent(event)

    def paintEvent(self, event):
        path = QPainterPath()
        rect = self.rect().adjusted(0, 0, -1, -1)
        path.addRoundedRect(rect, 25.0, 25.0)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(path, QColor(0, 0, 0, 0))
        painter.setClipPath(path)
        super().paintEvent(event)