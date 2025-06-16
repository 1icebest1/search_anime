from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class HelpPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Help Center")
        label.setStyleSheet("color: white;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)