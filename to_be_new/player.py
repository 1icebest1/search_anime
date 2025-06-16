import os
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QSplitter, QSlider
)
from PySide6.QtGui import QPixmap, Qt, QColor
from PySide6.QtCore import QUrl, Qt, QTime, QTimer, QEvent
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import sys

BASE_URL = "https://anilibria.tv"
CACHE_URL = "https://cache.libria.fun"


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
        ep_num.setStyleSheet("font-weight: bold; color: white;")

        title = QLabel(self.episode_data['title'])
        title.setStyleSheet("color: #aaa;")
        title.setWordWrap(True)

        info_layout.addWidget(ep_num)
        info_layout.addWidget(title)
        layout.addLayout(info_layout, 1)


class VideoPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Video widget
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.setMinimumSize(640, 360)

        # Media player
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Add to layout
        main_layout.addWidget(self.video_widget)

        # Set initial volume
        self.audio_output.setVolume(0.5)

        # Create controls overlay
        self.create_overlay_controls()

        # Connect signals
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        self.media_player.errorOccurred.connect(self.handle_error)

        # Mouse tracking
        self.video_widget.setMouseTracking(True)
        self.video_widget.installEventFilter(self)

        # Timer for auto-hide controls
        self.hide_timer = QTimer(self)
        self.hide_timer.setInterval(3000)
        self.hide_timer.timeout.connect(self.hide_controls)

    def create_overlay_controls(self):
        """Create a simple overlay control panel"""
        # Container frame
        self.overlay = QFrame(self.video_widget)
        self.overlay.setStyleSheet("""
            background-color: rgba(20, 20, 20, 220); 
            border-radius: 10px;
            border: 1px solid #444;
        """)
        self.overlay.setFixedSize(500, 180)
        self.overlay.hide()

        # Layout for overlay
        layout = QVBoxLayout(self.overlay)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # Title
        self.title_label = QLabel("Now Playing")
        self.title_label.setStyleSheet("""
            color: white; 
            font-size: 18px; 
            font-weight: bold;
            qproperty-alignment: AlignCenter;
        """)
        layout.addWidget(self.title_label)

        # Play button
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(70, 70)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(50, 150, 50, 200);
                border: none;
                border-radius: 35px;
                color: white;
                font-size: 32px;
            }
            QPushButton:hover {
                background-color: rgba(70, 170, 70, 220);
            }
        """)
        layout.addWidget(self.play_button, 0, Qt.AlignCenter)

        # Progress bar and time
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)

        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("""
            color: white; 
            font-size: 14px;
            min-width: 50px;
        """)
        progress_layout.addWidget(self.time_label)

        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #444;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                height: 16px;
                margin: -4px 0;
                background: white;
                border-radius: 8px;
            }
        """)
        progress_layout.addWidget(self.position_slider, 1)

        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("""
            color: white; 
            font-size: 14px;
            min-width: 50px;
        """)
        progress_layout.addWidget(self.duration_label)

        layout.addLayout(progress_layout)

        # Connect button
        self.play_button.clicked.connect(self.toggle_play)
        self.position_slider.sliderMoved.connect(self.set_position)

    def eventFilter(self, source, event):
        """Show controls on mouse move"""
        if event.type() == QEvent.MouseMove or event.type() == QEvent.Enter:
            self.show_controls()
        return super().eventFilter(source, event)

    def show_controls(self):
        """Show controls and start auto-hide timer"""
        if self.overlay is None:
            return

        # Position overlay in center
        x = (self.video_widget.width() - self.overlay.width()) // 2
        y = (self.video_widget.height() - self.overlay.height()) // 2
        self.overlay.move(x, y)
        self.overlay.show()
        self.overlay.raise_()
        self.hide_timer.start()

    def hide_controls(self):
        """Hide controls and stop timer"""
        if self.overlay and self.overlay.isVisible():
            self.overlay.hide()
        self.hide_timer.stop()

    def play_video(self, video_url, title="Anime Episode"):
        if not video_url:
            return

        self.title_label.setText(title)
        try:
            if video_url.startswith("/"):
                video_url = f"{CACHE_URL}{video_url}"

            self.media_player.setSource(QUrl(video_url))
            self.media_player.play()
            self.play_button.setText("⏸")
            self.show_controls()
        except Exception as e:
            print(f"Error playing video: {e}")

    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_button.setText("▶")
        else:
            self.media_player.play()
            self.play_button.setText("⏸")
            self.show_controls()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def position_changed(self, position):
        # Update only if slider is not being dragged
        if not self.position_slider.isSliderDown():
            self.position_slider.setValue(position)
        self.update_time_display()

    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_display()

    def state_changed(self, state):
        if state == QMediaPlayer.PausedState:
            self.show_controls()

    def handle_error(self, error, error_string):
        print(f"Media error: {error_string}")

    def update_time_display(self):
        duration = self.media_player.duration()
        position = self.media_player.position()

        if duration > 0 and position > 0:
            position_time = QTime(0, 0).addMSecs(position).toString('mm:ss')
            duration_time = QTime(0, 0).addMSecs(duration).toString('mm:ss')

            # Only update if changed
            if self.time_label.text() != position_time:
                self.time_label.setText(position_time)
            if self.duration_label.text() != duration_time:
                self.duration_label.setText(duration_time)

    def resizeEvent(self, event):
        # Reposition overlay when window resizes
        if self.overlay and self.overlay.isVisible():
            x = (self.video_widget.width() - self.overlay.width()) // 2
            y = (self.video_widget.height() - self.overlay.height()) // 2
            self.overlay.move(x, y)
        super().resizeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anime Player")
        self.resize(1200, 700)
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
                border-radius: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #333;
                color: white;
                font-size: 14px;
            }
            QSplitter::handle {
                background-color: #333;
                width: 2px;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Top controls
        top_controls = QHBoxLayout()
        top_controls.setSpacing(15)

        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet("color: white; font-size: 14px;")

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["FHD (1080p)", "HD (720p)", "SD (480p)"])
        self.quality_combo.setCurrentIndex(0)
        self.quality_combo.currentIndexChanged.connect(self.change_quality)
        self.quality_combo.setFixedWidth(150)

        self.toggle_episodes_btn = QPushButton("Hide Episodes List")
        self.toggle_episodes_btn.clicked.connect(self.toggle_episodes_list)
        self.toggle_episodes_btn.setFixedWidth(160)

        top_controls.addWidget(quality_label)
        top_controls.addWidget(self.quality_combo)
        top_controls.addStretch()
        top_controls.addWidget(self.toggle_episodes_btn)

        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(4)
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #444;
            }
        """)

        # Video player
        self.video_player = VideoPlayer()

        # Episodes list
        self.episodes_list = QListWidget()
        self.episodes_list.setMinimumWidth(300)
        self.episodes_list.setMaximumWidth(400)
        self.episodes_list.setStyleSheet("""
            QListWidget {
                background-color: #252525;
                border: 1px solid #444;
                border-radius: 8px;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                border-bottom: 1px solid #333;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #3a3a3a;
                border-radius: 5px;
            }
        """)
        self.episodes_list.itemClicked.connect(self.on_episode_selected)

        content_splitter.addWidget(self.video_player)
        content_splitter.addWidget(self.episodes_list)
        content_splitter.setSizes([700, 300])

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

        self.quality_map = {
            "FHD (1080p)": "fhd",
            "HD (720p)": "hd",
            "SD (480p)": "sd"
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

        title = f"Episode {episode['episode']}: {episode['title']}"
        if len(title) > 60:
            title = title[:57] + "..."

        if video_url:
            self.video_player.play_video(video_url, title)
        else:
            print(f"Quality {self.current_quality} not available for episode {episode['episode']}")

    def change_quality(self, index):
        quality_text = self.quality_combo.currentText()
        self.current_quality = self.quality_map.get(quality_text, "fhd")
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