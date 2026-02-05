# Qwen3-TTS FastAPI 서비스

> **음성 복제 기능을 제공하는 TTS API 서버**

Qwen3-TTS의 Voice Clone 기능을 활용하여 커스텀 보이스 파일로 음성을 복제하고, 외부 봇에서 텍스트를 전송받아 해당 목소리로 음성을 생성하는 REST API 서비스입니다.

---

## 📋 목차

- [주요 기능](#주요-기능)
- [사용 모델](#사용-모델)
- [설치 방법](#설치-방법)
- [서버 실행](#서버-실행)
- [API 사용법](#api-사용법)
- [외부 봇 연동 예제](#외부-봇-연동-예제)
- [프로젝트 구조](#프로젝트-구조)

---

## ✨ 주요 기능

- **🎤 Voice Clone**: 3초 이상의 음성 샘플로 목소리 복제
- **🔊 TTS 생성**: 등록된 커스텀 보이스로 텍스트를 음성으로 변환
- **🌍 다국어 지원**: 한국어, 영어, 중국어, 일본어 등 10개 언어 지원
- **⚡ 성능 최적화**: Voice Clone Prompt 캐싱으로 빠른 응답 속도
- **🔌 REST API**: 외부 봇/애플리케이션에서 쉽게 연동 가능

---

## 🤖 사용 모델

### Qwen3-TTS-12Hz-1.7B-Base

- **모델 타입**: Voice Clone 전용 Base 모델
- **음성 샘플 요구사항**: 3초 이상의 깨끗한 음성
- **지원 언어**: 10개 주요 언어
  - 한국어 (Korean)
  - 영어 (English)
  - 중국어 (Chinese)
  - 일본어 (Japanese)
  - 독일어 (German)
  - 프랑스어 (French)
  - 러시아어 (Russian)
  - 포르투갈어 (Portuguese)
  - 스페인어 (Spanish)
  - 이탈리아어 (Italian)
- **GPU 메모리**: 약 4-6GB VRAM 필요
- **특징**: 빠른 음성 복제, 높은 음질, 스트리밍 지원

> **💡 모델 사용 가능 여부**: 이 모델은 3초 이상의 음성 샘플만 있으면 빠르게 음성을 복제할 수 있습니다. GPU 메모리가 4GB 이상이면 사용 가능합니다.

---

## 🚀 설치 방법

### 1. 환경 설정

```bash
# Conda 환경 활성화
conda activate qwen3-tts

# 프로젝트 디렉토리로 이동
cd c:/Users/cisor/Qwen3-TTS
```

### 2. API 서버 의존성 설치

```bash
# FastAPI 및 관련 패키지 설치
pip install -r requirements_api.txt
```

`requirements_api.txt` 내용:

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
pydantic==2.9.2
aiofiles==24.1.0
```

---

## 🏃 서버 실행

### 방법 1: Uvicorn으로 직접 실행

```bash
# 개발 모드 (자동 재시작)
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 프로덕션 모드
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 방법 2: Python으로 실행

```bash
python -m api.main
```

### 서버 접속

- **API 문서 (Swagger UI)**: http://localhost:8000/docs
- **대체 API 문서 (ReDoc)**: http://localhost:8000/redoc
- **헬스 체크**: http://localhost:8000/health

---

## 📖 API 사용법

### 1. 커스텀 보이스 등록

**Endpoint**: `POST /voices/register`

**요청 (multipart/form-data)**:

```bash
curl -X POST "http://localhost:8000/voices/register" \
  -F "audio_file=@path/to/voice_sample.wav" \
  -F "voice_name=my_custom_voice" \
  -F "ref_text=안녕하세요, 저는 커스텀 보이스입니다." \
  -F "language=Korean"
```

**응답**:

```json
{
  "voice_id": "voice_abc123def456",
  "voice_name": "my_custom_voice",
  "message": "보이스가 성공적으로 등록되었습니다. Voice ID: voice_abc123def456"
}
```

### 2. TTS 생성

**Endpoint**: `POST /tts/generate`

**요청 (JSON)**:

```bash
curl -X POST "http://localhost:8000/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "안녕하세요, 부모님의 병원비를 위해 열심히 일하고 있습니다.",
    "voice_id": "voice_abc123def456",
    "language": "Korean"
  }' \
  --output output.wav
```

**응답**: WAV 형식의 오디오 파일

### 3. 보이스 목록 조회

**Endpoint**: `GET /voices`

**요청**:

```bash
curl -X GET "http://localhost:8000/voices"
```

**응답**:

```json
{
  "voices": [
    {
      "voice_id": "voice_abc123def456",
      "voice_name": "my_custom_voice",
      "ref_text": "안녕하세요, 저는 커스텀 보이스입니다.",
      "language": "Korean",
      "created_at": "2026-02-05T02:00:00"
    }
  ],
  "total": 1
}
```

### 4. 보이스 삭제

**Endpoint**: `DELETE /voices/{voice_id}`

**요청**:

```bash
curl -X DELETE "http://localhost:8000/voices/voice_abc123def456"
```

**응답**:

```json
{
  "message": "보이스가 성공적으로 삭제되었습니다: voice_abc123def456"
}
```

---

## 🤝 외부 봇 연동 예제

### Python 봇 예제

```python
import requests

# API 서버 URL
API_URL = "http://localhost:8000"

# 1. 커스텀 보이스 등록
def register_voice(audio_path, voice_name, ref_text, language="Korean"):
    with open(audio_path, 'rb') as audio_file:
        files = {'audio_file': audio_file}
        data = {
            'voice_name': voice_name,
            'ref_text': ref_text,
            'language': language
        }

        response = requests.post(
            f"{API_URL}/voices/register",
            files=files,
            data=data
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 보이스 등록 성공: {result['voice_id']}")
            return result['voice_id']
        else:
            print(f"❌ 등록 실패: {response.text}")
            return None

# 2. TTS 생성
def generate_tts(text, voice_id, language="Korean", output_path="output.wav"):
    response = requests.post(
        f"{API_URL}/tts/generate",
        json={
            "text": text,
            "voice_id": voice_id,
            "language": language
        }
    )

    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ TTS 생성 완료: {output_path}")
        return output_path
    else:
        print(f"❌ TTS 생성 실패: {response.text}")
        return None

# 3. 사용 예제
if __name__ == "__main__":
    # 보이스 등록
    voice_id = register_voice(
        audio_path="my_voice.wav",
        voice_name="sohee_voice",
        ref_text="안녕하세요, 저는 소희입니다.",
        language="Korean"
    )

    if voice_id:
        # TTS 생성
        generate_tts(
            text="부모님의 병원비를 위해 오늘도 열심히 일하고 있습니다.",
            voice_id=voice_id,
            language="Korean",
            output_path="bot_output.wav"
        )
```

### Node.js 봇 예제

```javascript
const axios = require("axios");
const FormData = require("form-data");
const fs = require("fs");

const API_URL = "http://localhost:8000";

// 1. 커스텀 보이스 등록
async function registerVoice(
  audioPath,
  voiceName,
  refText,
  language = "Korean",
) {
  const formData = new FormData();
  formData.append("audio_file", fs.createReadStream(audioPath));
  formData.append("voice_name", voiceName);
  formData.append("ref_text", refText);
  formData.append("language", language);

  try {
    const response = await axios.post(`${API_URL}/voices/register`, formData, {
      headers: formData.getHeaders(),
    });

    console.log(`✅ 보이스 등록 성공: ${response.data.voice_id}`);
    return response.data.voice_id;
  } catch (error) {
    console.error(`❌ 등록 실패: ${error.message}`);
    return null;
  }
}

// 2. TTS 생성
async function generateTTS(
  text,
  voiceId,
  language = "Korean",
  outputPath = "output.wav",
) {
  try {
    const response = await axios.post(
      `${API_URL}/tts/generate`,
      {
        text: text,
        voice_id: voiceId,
        language: language,
      },
      {
        responseType: "arraybuffer",
      },
    );

    fs.writeFileSync(outputPath, response.data);
    console.log(`✅ TTS 생성 완료: ${outputPath}`);
    return outputPath;
  } catch (error) {
    console.error(`❌ TTS 생성 실패: ${error.message}`);
    return null;
  }
}

// 3. 사용 예제
(async () => {
  const voiceId = await registerVoice(
    "my_voice.wav",
    "sohee_voice",
    "안녕하세요, 저는 소희입니다.",
    "Korean",
  );

  if (voiceId) {
    await generateTTS(
      "부모님의 병원비를 위해 오늘도 열심히 일하고 있습니다.",
      voiceId,
      "Korean",
      "bot_output.wav",
    );
  }
})();
```

---

## 📁 프로젝트 구조

```
Qwen3-TTS/
├── api/
│   ├── __init__.py           # API 패키지 초기화
│   ├── main.py               # FastAPI 메인 애플리케이션
│   ├── models.py             # Pydantic 데이터 모델
│   ├── routes.py             # API 라우트 정의
│   ├── tts_service.py        # TTS 서비스 로직
│   ├── voice_manager.py      # 보이스 관리
│   └── tests/                # 테스트 파일
│       └── test_api.py
├── data/
│   ├── voices/               # 업로드된 보이스 파일
│   └── voices_db.json        # 보이스 메타데이터
├── outputs/                  # 생성된 TTS 파일 (임시)
├── requirements_api.txt      # API 서버 의존성
└── README_API.md            # 이 문서
```

---

## 🔧 고급 설정

### 환경 변수 설정 (선택사항)

`.env` 파일을 생성하여 설정을 커스터마이즈할 수 있습니다:

```env
# 서버 설정
API_HOST=0.0.0.0
API_PORT=8000

# 모델 설정
MODEL_NAME=Qwen/Qwen3-TTS-12Hz-1.7B-Base
DEVICE_MAP=auto
DTYPE=bfloat16

# 데이터 경로
VOICES_DIR=data/voices
VOICES_DB=data/voices_db.json
```

### GPU 메모리 부족 시

GPU 메모리가 부족한 경우 0.6B 모델을 사용할 수 있습니다:

`api/tts_service.py` 파일에서 모델 이름 변경:

```python
self._model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",  # 0.6B 모델 사용
    device_map="auto",
    dtype=torch.bfloat16,
    attn_implementation="flash_attention_2"
)
```

---

## 🐛 문제 해결

### 1. Flash Attention 2 오류

**증상**: `flash_attention_2`를 찾을 수 없다는 오류

**해결**:

```bash
pip install flash-attn --no-build-isolation
```

또는 `api/tts_service.py`에서 `attn_implementation="sdpa"`로 변경

### 2. GPU 메모리 부족

**증상**: CUDA out of memory 오류

**해결**:

- 0.6B 모델 사용
- `dtype=torch.float16` 사용
- 배치 크기 줄이기

### 3. 모델 다운로드 느림

**증상**: 모델 로딩이 오래 걸림

**해결**:

```bash
# ModelScope를 통해 미리 다운로드
pip install modelscope
modelscope download --model Qwen/Qwen3-TTS-12Hz-1.7B-Base --local_dir ./models/Qwen3-TTS-12Hz-1.7B-Base
```

---

## 📝 라이선스

이 프로젝트는 Apache 2.0 라이선스를 따릅니다.

---

## 🙏 감사의 말

- [Qwen Team](https://github.com/QwenLM) - Qwen3-TTS 모델 개발
- [FastAPI](https://fastapi.tiangolo.com/) - 웹 프레임워크

---

## 📞 지원

문제가 발생하거나 질문이 있으시면 GitHub Issues를 통해 문의해주세요.
