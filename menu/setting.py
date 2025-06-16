from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from pathlib import Path


class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        base_dir = Path(__file__).parent.parent

        # Іконка по центру (без рамок)
        self.title_icon = QLabel()
        icon_path = base_dir / "data" / "pic_sys" / "setting.png"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.title_icon.setPixmap(pixmap)
        else:
            self.title_icon.setText("⚙️")
            self.title_icon.setAlignment(Qt.AlignCenter)
            self.title_icon.setStyleSheet("font-size: 48px;")
        self.title_icon.setFixedSize(70, 70)
        self.title_icon.setContentsMargins(0, 0, 0, 0)
        self.title_icon.setStyleSheet("border: none; background: none;")
        layout.addWidget(self.title_icon, alignment=Qt.AlignHCenter)

        # Заголовок
        self.title_label = QLabel("Налаштування")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(f"""
            font-weight: 500;
            color: #222;
            border: none;
            background: none;
            margin-top: 10px;
            margin-bottom: 40px;
            font-family: '{self.main_window.current_font}';
        """)
        layout.addWidget(self.title_label)

        # --- Тема (label + combo) ---
        theme_layout = QHBoxLayout()
        theme_layout.setContentsMargins(0, 0, 0, 0)
        theme_layout.setSpacing(20)

        theme_label = QLabel("Тема")
        theme_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        theme_label.setFixedWidth(80)
        theme_label.setStyleSheet("color: #444; background: none; border: none;")
        theme_label.setFont(QFont(self.main_window.current_font))

        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Космічна", "Темна", "Світла"])
        self.theme_selector.setFixedWidth(220)
        self.theme_selector.setFixedHeight(36)
        self.theme_selector.currentTextChanged.connect(self.change_theme)

        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_selector)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)

        # --- Шрифт (label + combo) ---
        font_layout = QHBoxLayout()
        font_layout.setContentsMargins(0, 0, 0, 0)
        font_layout.setSpacing(20)

        font_label = QLabel("Шрифт")
        font_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        font_label.setFixedWidth(80)
        font_label.setStyleSheet("color: #444; background: none; border: none;")
        font_label.setFont(QFont(self.main_window.current_font))

        self.font_selector = QComboBox()
        # Get fonts from main window
        if hasattr(self.main_window, "available_fonts") and self.main_window.available_fonts:
            self.font_selector.addItems(self.main_window.available_fonts)
        else:
            self.font_selector.addItems(["Arial", "Times New Roman", "Courier New", "Comic Sans MS"])
        self.font_selector.setFixedWidth(220)
        self.font_selector.setFixedHeight(36)
        self.font_selector.currentTextChanged.connect(self.change_font)

        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_selector)
        font_layout.addStretch()
        layout.addLayout(font_layout)

        # --- Інформаційний лейбл ---
        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(f"color: #888; margin-top: 50px; font-family: '{self.main_window.current_font}';")
        layout.addWidget(self.info_label)

        # Встановити початкові значення ComboBox-ів
        theme_reverse_map = {
            "dark": "Темна",
            "light": "Світла",
            "space": "Космічна"
        }
        current_theme_text = theme_reverse_map.get(self.main_window.current_theme, "Темна")
        self.theme_selector.blockSignals(True)
        self.theme_selector.setCurrentText(current_theme_text)
        self.theme_selector.blockSignals(False)

        if hasattr(self.main_window, "current_font"):
            font_in_main = self.main_window.current_font
            # Перевіряємо, чи є такий шрифт у доступних
            if font_in_main in self.main_window.available_fonts:
                self.font_selector.blockSignals(True)
                self.font_selector.setCurrentText(font_in_main)
                self.font_selector.blockSignals(False)
            elif self.main_window.available_fonts:
                # Якщо шрифт не знайдено, встановлюємо перший доступний
                self.main_window.apply_font(self.main_window.available_fonts[0])
                self.font_selector.blockSignals(True)
                self.font_selector.setCurrentText(self.main_window.available_fonts[0])
                self.font_selector.blockSignals(False)

        # Застосувати стиль під поточну тему
        self.apply_theme_to_widgets(self.main_window.current_theme)

    def apply_theme_to_widgets(self, theme_name):
        """
        Стилі ComboBox та загальних віджетів залежно від теми.
        """
        # Get current font
        current_font = self.main_window.current_font

        if theme_name == "dark":
            combo_style = f"""
                QComboBox {{
                    background-color: #505050;
                    color: white;
                    border: 1px solid #707070;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-family: '{current_font}';
                }}
                QComboBox:hover {{
                    border-color: #909090;
                }}
                QComboBox::drop-down {{
                    border: none;
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 30px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border: none;
                    width: 0; height: 0;
                }}
                QComboBox QAbstractItemView {{
                    background-color: #404040;
                    color: white;
                    selection-background-color: #606060;
                    selection-color: white;
                    font-family: '{current_font}';
                }}
            """
            info_color = "#ccc"
            title_color = "#eee"

        elif theme_name == "space":
            combo_style = f"""
                QComboBox {{
                    background-color: rgba(50, 50, 60, 200);
                    color: #c0d6ff;
                    border: 1px solid rgba(130, 170, 255, 0.6);
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-family: '{current_font}';
                }}
                QComboBox:hover {{
                    border-color: rgba(180, 200, 255, 0.8);
                }}
                QComboBox::drop-down {{
                    border: none;
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 30px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border: none;
                    width: 0; height: 0;
                }}
                QComboBox QAbstractItemView {{
                    background-color: rgba(40, 40, 50, 230);
                    color: #c0d6ff;
                    selection-background-color: rgba(80, 100, 140, 180);
                    selection-color: white;
                    font-family: '{current_font}';
                }}
            """
            info_color = "#aaccff"
            title_color = "#ddeeff"

        else:  # light
            combo_style = f"""
                QComboBox {{
                    background-color: #fff8e1;
                    color: #5d4037;
                    border: 1px solid #c69c6d;
                    border-radius: 8px;
                    padding: 4px 8px;
                    font-family: '{current_font}';
                }}
                QComboBox:hover {{
                    border-color: #a57c51;
                }}
                QComboBox::drop-down {{
                    border: none;
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 30px;
                }}
                QComboBox::down-arrow {{
                    image: none;
                    border: none;
                    width: 0; height: 0;
                }}
                QComboBox QAbstractItemView {{
                    background-color: white;
                    color: #5d4037;
                    selection-background-color: #ffe0b2;
                    selection-color: #3e2723;
                    font-family: '{current_font}';
                }}
            """
            info_color = "#666"
            title_color = "#222"

        # Застосовуємо стиль до обох ComboBox
        self.theme_selector.setStyleSheet(combo_style)
        self.font_selector.setStyleSheet(combo_style)

        # Оновлюємо кольори текстів
        self.info_label.setStyleSheet(f"color: {info_color}; margin-top: 50px; font-family: '{current_font}';")
        self.title_label.setStyleSheet(f"""
            font-weight: 500;
            color: {title_color};
            border: none;
            background: none;
            margin-top: 10px;
            margin-bottom: 40px;
            font-family: '{current_font}';
        """)

        # Propagate font changes
        self.main_window.propagate_font()

    def change_theme(self, theme_text):
        theme_map = {
            "Темна": "dark",
            "Світла": "light",
            "Космічна": "space"
        }
        theme_key = theme_map.get(theme_text, "dark")
        self.main_window.apply_theme(theme_key)
        self.apply_theme_to_widgets(theme_key)
        self.info_label.setText(f"Тема: {theme_text}")

    def change_font(self, font_name):
        self.main_window.apply_font(font_name)
        self.info_label.setText(f"Шрифт: {font_name}")