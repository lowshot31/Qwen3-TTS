import requests
import os

URL = "http://localhost:8000/voices/register"
VOICE_FILE = r"C:\음성파일\last_kids.m4a"
REF_TEXT = "근데 골반이 진짜 넓어 망내는 역시 가슴보다는골반..여러분들은 제 방송의 묘미가 뭐라고생각하세여"
VOICE_NAME = "클로에_최종본"

# 핵심: 로컬에서 성공했던 그 시간만큼만 서버에서도 딱 자릅니다!
data = {
    "voice_name": VOICE_NAME,
    "ref_text": REF_TEXT,
    "language": "Korean",
    "start_sec": 0,    # 0초부터
    "duration": 7      # 7초만!
}

print(f"🎤 '{VOICE_NAME}' 보이스를 정밀 모드(7초)로 등록합니다...")

with open(VOICE_FILE, "rb") as f:
    files = {"audio_file": (os.path.basename(VOICE_FILE), f, "audio/m4a")}
    response = requests.post(URL, data=data, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ 등록 성공! ID: {result['voice_id']}")
    else:
        print(f"❌ 실패: {response.text}")
