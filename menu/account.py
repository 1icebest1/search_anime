from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QPointF
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QLineSeries, QValueAxis, QPieSlice
from PySide6.QtGui import QPainter, QColor, QBrush, QFont, QPen

class AccountPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)


        top_bar = QHBoxLayout()
        top_bar.addStretch()

        self.btn_quit = QPushButton("🚪 Вийти")
        self.btn_login = QPushButton("🔑 Увійти")
        for btn in [self.btn_quit, self.btn_login]:
            btn.setMinimumSize(120, 40)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(80, 80, 80, 150);
                    color: white;
                    border-radius: 15px;
                    font-size: 14px;
                    padding: 8px;
                    border: 2px solid #4CAF50;
                }
                QPushButton:hover {
                    background: rgba(96, 96, 96, 200);
                    border-color: #45a049;
                }
            """)
        top_bar.addWidget(self.btn_login)
        top_bar.addWidget(self.btn_quit)
        main_layout.addLayout(top_bar)


        profile_frame = QFrame()
        profile_frame.setStyleSheet("""
            background: rgba(43, 43, 43, 150);
            border-radius: 20px;
            border: none;
        """)
        profile_layout = QVBoxLayout(profile_frame)
        profile_layout.setContentsMargins(30, 30, 30, 30)
        profile_layout.setSpacing(20)
        profile_layout.setAlignment(Qt.AlignCenter)

        self.avatar = QLabel("🎮")
        self.avatar.setStyleSheet("""
            font-size: 120px;
            color: #7f8c8d;
            padding: 20px;
            background: rgba(52, 73, 94, 150);
            border-radius: 50%;
            border: 3px solid #2ecc71;
        """)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setMinimumSize(200, 200)
        profile_layout.addWidget(self.avatar, alignment=Qt.AlignCenter)

        stats_text = QLabel("🎬 Загалом переглянуто: 142 серії")
        stats_text.setStyleSheet("""
            color: #bdc3c7;
            font-size: 16px;
            padding: 15px;
            background: rgba(52, 73, 94, 100);
            border-radius: 15px;
            line-height: 1.8;
        """)
        profile_layout.addWidget(stats_text)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: #3498db; margin: 15px 50px; height: 2px;")
        profile_layout.addWidget(separator)

        self.nickname = QLabel("Cyber")
        self.nickname.setStyleSheet("""
            color: #ecf0f1;
            font-size: 28px;
            font-weight: bold;
            padding: 10px;
            background: rgba(44, 62, 80, 150);
            border-radius: 10px;
        """)
        profile_layout.addWidget(self.nickname, alignment=Qt.AlignCenter)

        main_layout.addWidget(profile_frame)


        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            background: rgba(43, 43, 43, 150);
            border-radius: 20px;
            border: none;
        """)
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 20, 20, 20)

        stats_title = QLabel("📊 Детальна статистика")
        stats_title.setStyleSheet("""
            color: #2ecc71;
            font-size: 22px;
            font-weight: bold;
            padding-bottom: 15px;
            border-bottom: 2px solid #3498db;
        """)
        stats_layout.addWidget(stats_title)

        charts_container = QWidget()
        charts_layout = QHBoxLayout(charts_container)
        charts_layout.addWidget(self.create_pie_chart())
        charts_layout.addWidget(self.create_line_chart())
        stats_layout.addWidget(charts_container)
        main_layout.addWidget(stats_frame)


    def create_pie_chart(self):
        series = QPieSeries()
        data = [
            ("Переглянуто", 65, 142, "#2ecc71"),
            ("В процесі", 15, 33, "#3498db"),
            ("В планах", 10, 22, "#f1c40f"),
            ("Кинуто", 10, 18, "#e74c3c")
        ]

        for label, percent, value, color in data:
            slice = QPieSlice(f"{label}\n{value} серій ({percent}%)", percent)
            slice.setColor(QColor(color))
            slice.setLabelColor(Qt.white)
            slice.setLabelFont(QFont("Arial", 10, QFont.Bold))
            slice.setLabelPosition(QPieSlice.LabelOutside)
            slice.setBorderColor(QColor(color))
            slice.setBorderWidth(2)
            series.append(slice)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Прогрес переглядів (загалом: 220 серій)")
        chart.setTitleFont(QFont("Arial", 12, QFont.Bold))
        chart.setTitleBrush(QColor("#ffffff"))
        chart.setBackgroundBrush(QBrush(Qt.transparent))
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.legend().setLabelColor(QColor("#ffffff"))

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumSize(400, 300)
        return chart_view

    def create_line_chart(self):
        series = QLineSeries()
        series.setName("Активність")
        data = [(0, 4), (1, 7), (2, 2), (3, 9), (4, 5), (5, 11), (6, 6)]

        for x, y in data:
            series.append(QPointF(x, y))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Щоденна активність")
        chart.setTitleFont(QFont("Arial", 12, QFont.Bold))
        chart.setTitleBrush(QColor("#ffffff"))
        chart.setAnimationOptions(QChart.SeriesAnimations)

        axis_x = QValueAxis()
        axis_x.setTitleText("Дні")
        axis_x.setRange(0, 6)
        axis_x.setLabelsColor(QColor("#ffffff"))
        chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setTitleText("Серії")
        axis_y.setRange(0, 12)
        axis_y.setLabelsColor(QColor("#ffffff"))
        chart.addAxis(axis_y, Qt.AlignLeft)

        chart.setBackgroundBrush(QBrush(Qt.transparent))
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumSize(400, 300)
        return chart_view