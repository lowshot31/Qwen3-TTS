# Qwen3-TTS FastAPI 서비스 - 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 의존성 설치

```bash
conda activate qwen3-tts
cd c:/Users/cisor/Qwen3-TTS
pip install -r requirements_api.txt
```

### 2단계: 서버 실행

```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3단계: API 문서 확인

브라우저에서 http://localhost:8000/docs 접속

---

## 📝 간단한 사용 예제

### Python으로 TTS 생성하기

```python
import requests

# 1. 보이스 등록
with open("my_voice.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/voices/register",
        files={"audio_file": f},
        data={
            "voice_name": "my_voice",
            "ref_text": "안녕하세요, 저는 커스텀 보이스입니다.",
            "language": "Korean"
        }
    )
    voice_id = response.json()["voice_id"]

# 2. TTS 생성
response = requests.post(
    "http://localhost:8000/tts/generate",
    json={
        "text": "부모님의 병원비를 위해 열심히 일하고 있습니다.",
        "voice_id": voice_id,
        "language": "Korean"
    }
)

# 3. 음성 파일 저장
with open("output.wav", "wb") as f:
    f.write(response.content)

print("✅ TTS 생성 완료!")
```

---

## 📚 자세한 문서

전체 API 문서는 [README_API.md](README_API.md)를 참조하세요.

---

## 🔧 주요 엔드포인트

| 메서드 | 엔드포인트           | 설명               |
| ------ | -------------------- | ------------------ |
| POST   | `/voices/register`   | 커스텀 보이스 등록 |
| POST   | `/tts/generate`      | TTS 생성           |
| GET    | `/voices`            | 보이스 목록 조회   |
| DELETE | `/voices/{voice_id}` | 보이스 삭제        |
| GET    | `/health`            | 헬스 체크          |

---

## ⚙️ 시스템 요구사항

- **GPU**: NVIDIA GPU (4GB+ VRAM 권장)
- **Python**: 3.12
- **CUDA**: 11.8 이상
- **모델**: Qwen3-TTS-12Hz-1.7B-Base (자동 다운로드)

---

## 🐛 문제 해결

### Flash Attention 2 오류

```bash
pip install flash-attn --no-build-isolation
```

### GPU 메모리 부족

`api/tts_service.py`에서 0.6B 모델로 변경:

```python
"Qwen/Qwen3-TTS-12Hz-0.6B-Base"
```

---

## 📞 도움말

- **API 문서**: http://localhost:8000/docs
- **상세 가이드**: [README_API.md](README_API.md)
- **GitHub**: https://github.com/QwenLM/Qwen3-TTS
