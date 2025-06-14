
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QFormLayout
from PySide6.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignTop)

        # Вибір теми
        form = QFormLayout()
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["✨ Космічна", "🌙 Темна", "☀️ Світла" ])
        self.theme_selector.currentTextChanged.connect(self.change_theme)
        form.addRow("Тема оформлення:", self.theme_selector)
        layout.addLayout(form)

        # Інший контент
        label = QLabel("Налаштування джерел даних тимчасово недоступні")
        label.setStyleSheet("color: #aaa; font-size: 16px; margin-top: 30px;")
        layout.addWidget(label)

    def change_theme(self, theme):
        theme_map = {
            "🌙 Темна": "dark",
            "☀️ Світла": "light",
            "✨ Космічна": "space"
        }
        self.main_window.apply_theme(theme_map[theme])