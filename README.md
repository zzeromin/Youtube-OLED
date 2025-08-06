# Raspberry Pi YouTube Music Spectrum & Now Playing Display

라즈베리파이에서 YouTube Music(또는 Chromium 기반 재생)의 현재 재생 중인 곡 정보(가수 - 곡 제목)와 오디오 스펙트럼을 SSD1306 OLED에 실시간으로 표시하는 프로젝트입니다.

---

## 주요 기능

- YouTube Music 또는 Chromium 기반 미디어 재생곡 정보를 `playerctl`을 이용해 자동으로 가져와 OLED 상단에 표시  
- CAVA를 사용해 오디오 스펙트럼 데이터를 실시간으로 읽어 OLED 하단에 막대 그래프로 표시  
- 긴 곡 제목 및 가수명은 OLED 화면에 맞게 자동 좌우 스크롤 처리  
- config.json을 통한 스펙트럼 바 개수, 바 폭, FPS, 헤더 텍스트 설정 가능  
- OLED에 한글 정상 출력 (나눔고딕 TTF 폰트 사용)  
- graceful 종료 시 CAVA 프로세스 자동 종료 및 리소스 정리  



## 하드웨어 요구사항

- Raspberry Pi (3 이상 권장)  
- 0.96 또는 2.3인치 OLED 디스플레이 (SSD1306 I2C 방식 128x64)  
- 라즈베리파이 OS 설치 및 네트워크 연결  


## 소프트웨어 요구사항

- Python 3.7 이상  
- Raspberry Pi OS (Debian 기반)  
- Chromium 브라우저 (YouTube Music 재생 가능)  



## 설치 방법

### 1. 시스템 패키지 설치
```bash
sudo apt update
sudo apt install -y playerctl fonts-nanum
```

### 2. Python 가상환경 및 필수 라이브러리 설치
```bash
python3 -m venv cava_env
source cava_env/bin/activate
pip install --upgrade pip
pip install numpy pillow adafruit-circuitpython-ssd1306 watchdog
```

### 3. 프로젝트 클론 또는 복사
```bash
git clone https://github.com/zzeromin/Youtube-OLED.git
cd Youtube-OLED
```

### 4. cava 설치
```bash
sudo apt install cava
```
또는 소스 빌드:
https://github.com/karlstav/cava

---

## 사용 방법
1. OLED, I2C 연결 확인
2. Chromium 브라우저로 YouTube Music 접속 후 음악 재생
3. Python 가상환경 활성화 후 실행
```bash
source cava_env/bin/activate
python youtube_oled.py
```
4. 프로그램 종료: Ctrl+C

## config.json 옵션 예시
```json
{
  "spectrum_bars": 16,
  "bar_width": 6,
  "bar_spacing": 1,
  "spectrum_fps": 20,
  "header_text": "YouTube Spectrum"
}
```
- `spectrum_bars`: 스펙트럼 바 개수 (기본 16)
- `bar_width`: 막대 폭 (픽셀 단위)
- `bar_spacing`: 막대 간 간격
- `spectrum_fps`: 화면 업데이트 속도 (FPS)
- `header_text`: 기본 헤더 텍스트 (실제 사용 시 현재 재생곡으로 자동 변경)

## 한글 폰트 변경 방법
- `/usr/share/fonts/truetype/nanum/NanumGothic.ttf` 경로를 기준으로 TTF 폰트를 지정
- 다른 폰트 사용 시, `youtube-oled.py` 내 `ImageFont.truetype()` 경로 수정

## 주의사항
- `playerctl`은 Chromium의 MPRIS 지원에 의존합니다. 최신 버전 Chromium 사용 권장
- YouTube Music이 아닌 다른 플레이어 재생 시 동작하지 않을 수 있음
- OLED 해상도는 128x64 기준입니다. 다른 모델은 코드 수정 필요

