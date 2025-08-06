import os
import json
import subprocess
import signal
import time
import numpy as np
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from PIL import Image, ImageDraw, ImageFont
import board
import busio
import adafruit_ssd1306

CONFIG_FILE = "config.json"
CAVA_CONFIG_PATH = os.path.expanduser("~/.config/cava/config")

default_config = {
    "spectrum_bars": 16,
    "bar_width": 8,
    "bar_spacing": 0,
    "spectrum_fps": 20,
    "header_text": "YouTube Spectrum"
}

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, reload_func):
        self.reload_func = reload_func
    def on_modified(self, event):
        if event.src_path.endswith(CONFIG_FILE):
            self.reload_func()

class SpectrumDisplay:
    def __init__(self):
        self.config = self.load_config()
        self.running = True
        self.proc = None
        self.latest_data = np.zeros(self.config['spectrum_bars'], dtype=np.float32)

        # OLED 초기화
        i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
        self.oled.fill(0)
        self.oled.show()
        #self.font = ImageFont.load_default()
        self.font = ImageFont.truetype("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", 12)

        # 현재 곡 정보
        self.track_info = "Loading..."
        self.track_last_update = 0

        # Config 변경 감시
        event_handler = ConfigHandler(self.reload_config)
        self.observer = Observer()
        self.observer.schedule(event_handler, ".", recursive=False)
        self.observer.start()

        # 스크롤 관련 변수
        self.scroll_offset = 0
        self.scroll_direction = 1  # 1=왼쪽, -1=오른쪽
        self.scroll_wait = 0       # 끝 도달 시 대기 시간 (프레임 단위)
        self.scroll_speed = 1      # 한 프레임당 이동 픽셀 수

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump(default_config, f, indent=2)
            return default_config.copy()
        else:
            with open(CONFIG_FILE) as f:
                return json.load(f)

    def reload_config(self):
        print("Config changed, reloading...")
        self.config = self.load_config()
        self.create_cava_config()

    def create_cava_config(self):
        os.makedirs(os.path.dirname(CAVA_CONFIG_PATH), exist_ok=True)
        cava_config = f"""
[general]
bars = {self.config['spectrum_bars']}
framerate = {self.config['spectrum_fps']}
autosens = 1

[output]
method = raw
channels = mono
raw_target = /dev/stdout
bit_format = 16bit
"""
        with open(CAVA_CONFIG_PATH, "w") as f:
            f.write(cava_config)

    def get_current_track(self):
        # 2초마다만 갱신
        now = time.time()
        if now - self.track_last_update > 2:
            try:
                result = subprocess.run(
                    ["playerctl", "metadata", "--format", "{{artist}} - {{title}}"],
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
                )
                info = result.stdout.strip()
                if info:
                    self.track_info = info
                else:
                    self.track_info = "No music playing"
            except Exception:
                self.track_info = "Error reading track"
            self.track_last_update = now
        return self.track_info

    def start_cava(self):
        self.create_cava_config()
        self.proc = subprocess.Popen(["cava", "-p", CAVA_CONFIG_PATH],
                                     stdout=subprocess.PIPE, bufsize=0)

    def read_cava(self):
        bar_count = self.config['spectrum_bars']
        alpha = 0.5
        while self.running:
            raw = self.proc.stdout.read(bar_count * 2)
            if not raw:
                break
            new_data = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            # 길이 맞추기
            if len(new_data) != bar_count:
                if len(new_data) > bar_count:
                    new_data = new_data[:bar_count]
                else:
                    padding = np.zeros(bar_count - len(new_data), dtype=np.float32)
                    new_data = np.concatenate((new_data, padding))
            self.latest_data = alpha * self.latest_data + (1 - alpha) * new_data

    def draw_spectrum(self, bars):
        image = Image.new("1", (self.oled.width, self.oled.height))
        draw = ImageDraw.Draw(image)

        # 현재 곡 정보
        track = self.get_current_track()

        # 텍스트 길이 계산
        bbox = draw.textbbox((0, 0), track, font=self.font)
        text_width = bbox[2] - bbox[0]

        # 스크롤 처리 (왼쪽 방향만)
        if text_width > self.oled.width:
            self.scroll_offset -= self.scroll_speed
            if self.scroll_offset <= -(text_width):
                # 한 바퀴 돌면 다시 처음
                self.scroll_offset = self.oled.width
        else:
            self.scroll_offset = 0

        # 텍스트 출력
        draw.text((self.scroll_offset, 0), track, font=self.font, fill=255)

        # 스펙트럼 막대
        height = self.oled.height
        max_bar_height = height - 16
        bar_w = self.config['bar_width']
        bar_spacing = self.config['bar_spacing']

        for i, val in enumerate(bars):
            x = i * (bar_w + bar_spacing)
            draw.rectangle([x, 16, x + bar_w, height], outline=0, fill=0)
            h = int(max(0, (val / 32768.0) * max_bar_height))
            y0, y1 = height - h, height
            draw.rectangle([x, y0, x + bar_w, y1], outline=255, fill=255)

        self.oled.image(image)
        self.oled.show()


    def draw_loop(self):
        target_fps = min(self.config.get('spectrum_fps', 20), 20)
        frame_time = 1.0 / target_fps
        while self.running:
            self.draw_spectrum(self.latest_data)
            time.sleep(frame_time)

    def run(self):
        self.start_cava()
        t1 = Thread(target=self.read_cava)
        t2 = Thread(target=self.draw_loop)
        t1.start()
        t2.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            self.running = False
            self.proc.send_signal(signal.SIGTERM)
            t1.join()
            t2.join()
            self.observer.stop()
            self.observer.join()
            print("Exited cleanly.")

if __name__ == "__main__":
    SpectrumDisplay().run()
