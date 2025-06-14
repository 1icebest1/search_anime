import os
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QComboBox, QListWidget, QListWidgetItem, QSizePolicy, QSplitter, QSlider
)
from PySide6.QtGui import QPixmap, QPainter, Qt, QAction, QColor
from PySide6.QtCore import QUrl, Qt, QTime
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import sys

BASE_URL = "https://anilibria.tv"
CACHE_URL = "https://cache.libria.fun"


class RoundedImageLabel(QGraphicsView):
    def __init__(self, image_path, radius, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self.setFixedSize(240, 360)

        pixmap = self.load_pixmap(image_path)
        pixmap = pixmap.scaled(240, 360, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, radius, radius)
        painter.end()

        pixmap.setMask(mask.createMaskFromColor(Qt.transparent))

        scene = QGraphicsScene()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        self.setScene(scene)
        self.setAlignment(Qt.AlignCenter)

    def load_pixmap(self, image_path):
        if image_path.startswith("/"):
            image_path = f"{BASE_URL}{image_path}"

        if image_path.startswith("http"):
            try:
                response = requests.get(image_path, timeout=10)
                response.raise_for_status()
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap
            except Exception as e:
                print(f"Error loading image: {e}")
                return self.create_default_pixmap()
        else:
            full_path = os.path.abspath(image_path)
            if not os.path.exists(full_path):
                return self.create_default_pixmap()
            return QPixmap(full_path)

    def create_default_pixmap(self):
        pixmap = QPixmap(240, 360)
        pixmap.fill(QColor(60, 60, 60))
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "No Image")
        painter.end()
        return pixmap


class AnimeCard(QFrame):
    def __init__(self, parent, data, main_window):
        super().__init__(parent)
        self.data = data
        self.main_window = main_window
        self.setup_ui()
        self.setCursor(Qt.PointingHandCursor)

    def setup_ui(self):
        self.setFixedSize(240, 360)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            background: transparent;
            border-radius: 15px;
            border: none;
        """)

        mask = QPixmap(240, 360)
        mask.fill(Qt.transparent)
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.drawRoundedRect(0, 0, 240, 360, 15, 15)
        painter.end()
        self.setMask(mask.mask())

        container = QWidget(self)
        container.setGeometry(0, 0, 240, 360)

        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)

        rounded_image = RoundedImageLabel(self.data.get("image", ""), radius=20)
        grid.addWidget(rounded_image, 0, 0)

        title = self.data.get("title", "No Title")
        if len(title) > 23:
            title = title[:20] + "..."

        text_label = QLabel(title)
        text_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        text_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.5);
            color: white;
            font-size: 17px;
            padding: 5px;
            border-radius: 5px;
        """)
        grid.addWidget(text_label, 0, 0)

    def mousePressEvent(self, event):
        self.main_window.show_anime_details(self.data)


class EpisodeItemWidget(QWidget):
    def __init__(self, episode_data, parent=None):
        super().__init__(parent)
        self.episode_data = episode_data
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Episode preview image
        preview_label = QLabel()
        preview_label.setFixedSize(80, 45)

        if self.episode_data.get("preview"):
            preview_url = BASE_URL + self.episode_data["preview"]
            try:
                response = requests.get(preview_url)
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                pixmap = pixmap.scaled(80, 45, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview_label.setPixmap(pixmap)
            except:
                preview_label.setStyleSheet("background-color: #333;")
                preview_label.setText("No Preview")
                preview_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(preview_label)

        # Episode info
        info_layout = QVBoxLayout()
        ep_num = QLabel(f"Episode {self.episode_data['episode']}")
        ep_num.setStyleSheet("font-weight: bold;")

        title = QLabel(self.episode_data['title'])
        title.setStyleSheet("color: #aaa;")
        title.setWordWrap(True)

        info_layout.addWidget(ep_num)
        info_layout.addWidget(title)
        layout.addLayout(info_layout, 1)


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        self.video_widget = QVideoWidget()
        self.media_player.setVideoOutput(self.video_widget)

        # Player controls
        self.play_button = QPushButton("▶")
        self.play_button.setFixedWidth(40)
        self.play_button.clicked.connect(self.toggle_play)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self.set_position)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)

        self.status_label = QLabel("Status: Idle")
        self.time_label = QLabel("00:00 / 00:00")

        # Layout for controls
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.position_slider)
        control_layout.addWidget(QLabel("Volume:"))
        control_layout.addWidget(self.volume_slider)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.video_widget, 1)
        layout.addLayout(control_layout)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)
        self.setLayout(layout)

        # Connect signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        self.media_player.errorOccurred.connect(self.handle_error)

        # Set initial volume
        self.audio_output.setVolume(0.5)

    def play_video(self, video_url):
        """Load and play video from URL"""
        if not video_url:
            self.status_label.setText("Error: No video URL provided")
            return

        self.status_label.setText("Status: Loading...")
        QApplication.processEvents()

        try:
            # Check if URL needs base URL prepended
            if video_url.startswith("/"):
                video_url = CACHE_URL + video_url

            # Set media source
            self.media_player.setSource(QUrl(video_url))
            self.media_player.play()
            self.play_button.setText("⏸")
            self.status_label.setText("Status: Playing")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶")
            self.status_label.setText("Status: Paused")
        else:
            self.media_player.play()
            self.play_button.setText("⏸")
            self.status_label.setText("Status: Playing")

    def set_position(self, position):
        self.media_player.setPosition(position)

    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)

    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_time_display()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_display()

    def state_changed(self, state):
        states = {
            QMediaPlayer.StoppedState: "Stopped",
            QMediaPlayer.PlayingState: "Playing",
            QMediaPlayer.PausedState: "Paused"
        }
        self.status_label.setText(f"Status: {states.get(state, 'Unknown')}")

    def handle_error(self, error, error_string):
        self.status_label.setText(f"Error: {error_string}")

    def update_time_display(self):
        duration = self.media_player.duration()
        position = self.media_player.position()

        if duration > 0 and position > 0:
            duration_time = QTime(0, 0).addMSecs(duration)
            position_time = QTime(0, 0).addMSecs(position)
            self.time_label.setText(f"{position_time.toString('mm:ss')} / {duration_time.toString('mm:ss')}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Player")
        self.resize(1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
            }
            QComboBox, QPushButton {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 12px;
                background: #fff;
                border-radius: 6px;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #333;
                color: white;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top controls
        top_controls = QHBoxLayout()
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["fhd", "hd", "sd"])
        self.quality_combo.currentTextChanged.connect(self.change_quality)

        self.toggle_episodes_btn = QPushButton("Hide Episodes List")
        self.toggle_episodes_btn.clicked.connect(self.toggle_episodes_list)

        top_controls.addWidget(QLabel("Quality:"))
        top_controls.addWidget(self.quality_combo)
        top_controls.addStretch()
        top_controls.addWidget(self.toggle_episodes_btn)

        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)

        # Video player
        self.video_player = VideoPlayer()

        # Episodes list
        self.episodes_list = QListWidget()
        self.episodes_list.setMaximumWidth(300)
        self.episodes_list.itemClicked.connect(self.on_episode_selected)

        content_splitter.addWidget(self.video_player)
        content_splitter.addWidget(self.episodes_list)
        content_splitter.setStretchFactor(0, 3)
        content_splitter.setStretchFactor(1, 1)

        # Add to main layout
        main_layout.addLayout(top_controls)
        main_layout.addWidget(content_splitter, 1)

        # Sample anime data
        self.anime_data = {
            "title": "The Saint Whose Engagement Was Broken When She Became Too Perfect",
            "image": "/storage/releases/posters/9920/prJ5BnhMI4420p0KJqcoUOHqUJGXJvWB.jpg",
            "episodes": [
                {
                    "episode": "1",
                    "title": "The Saint Who Never Smiles",
                    "video": {
                        "fhd": "/videos/media/ts/9920/1/1080/da41979925670e99e9d08dbf31783b97.m3u8",
                        "hd": "/videos/media/ts/9920/1/720/23b79bc4751db36068f5a7da33e32000.m3u8",
                        "sd": "/videos/media/ts/9920/1/480/90b2aad4c7f981612e5217388fafeab5.m3u8"
                    },
                    "preview": "/storage/releases/episodes/previews/9920/1/6Hgeu7uoGpFgJy2l__d8e9669b1b5dde53463ea6ad893f4699.jpg"
                },
                {
                    "episode": "2",
                    "title": "Welcome to Parnacotta",
                    "video": {
                        "fhd": "/videos/media/ts/9920/2/1080/cf2d9a9886a19eca3c9f20b4cde75b45.m3u8",
                        "hd": "/videos/media/ts/9920/2/720/0597055506c8595b25adba9c3726be76.m3u8",
                        "sd": "/videos/media/ts/9920/2/480/cecd4524fca26c20e1026b2167cbd9f2.m3u8"
                    },
                    "preview": "/storage/releases/episodes/previews/9920/2/6tQKSrNvgKarjVj3__b65ca89306eec5cc49d004580469ebe1.jpg"
                }
            ]
        }

        self.current_quality = "fhd"
        self.current_episode_index = 0
        self.populate_episodes()
        self.play_episode(0)

    def populate_episodes(self):
        self.episodes_list.clear()
        for ep in self.anime_data["episodes"]:
            item = QListWidgetItem(self.episodes_list)
            widget = EpisodeItemWidget(ep)
            item.setSizeHint(widget.sizeHint())
            self.episodes_list.addItem(item)
            self.episodes_list.setItemWidget(item, widget)
        self.episodes_list.setCurrentRow(self.current_episode_index)

    def on_episode_selected(self, item):
        idx = self.episodes_list.row(item)
        self.play_episode(idx)

    def play_episode(self, index):
        self.current_episode_index = index
        episode = self.anime_data["episodes"][index]
        video_url = episode["video"].get(self.current_quality)

        if video_url:
            full_url = CACHE_URL + video_url
            self.video_player.play_video(full_url)
        else:
            self.video_player.status_label.setText(
                f"Quality {self.current_quality} not available for episode {episode['episode']}"
            )

    def change_quality(self, quality):
        self.current_quality = quality
        self.play_episode(self.current_episode_index)

    def toggle_episodes_list(self):
        if self.episodes_list.isVisible():
            self.episodes_list.hide()
            self.toggle_episodes_btn.setText("Show Episodes List")
        else:
            self.episodes_list.show()
            self.toggle_episodes_btn.setText("Hide Episodes List")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())