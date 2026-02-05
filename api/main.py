from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from .routes import router

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Qwen3-TTS API",
    description="""
    ## Qwen3-TTS 음성 복제 API 서비스
    
    커스텀 보이스 파일을 사용하여 음성을 복제하고, 텍스트를 음성으로 변환하는 TTS API입니다.
    
    ### 주요 기능
    - **Voice Clone**: 3초 이상의 음성 샘플로 목소리 복제
    - **TTS 생성**: 등록된 커스텀 보이스로 텍스트를 음성으로 변환
    - **다국어 지원**: 한국어, 영어, 중국어, 일본어 등 10개 언어 지원
    
    ### 사용 모델
    - **Qwen3-TTS-12Hz-1.7B-Base**: Voice Clone 기능을 위한 Base 모델
    - 3초 이상의 음성 샘플로 빠른 음성 복제 가능
    - 10개 주요 언어 지원 (한국어, 영어, 중국어, 일본어, 독일어, 프랑스어, 러시아어, 포르투갈어, 스페인어, 이탈리아어)
    
    ### 시작하기
    1. `POST /voices/register` - 커스텀 보이스 등록
    2. `POST /tts/generate` - TTS 생성
    3. `GET /voices` - 등록된 보이스 목록 확인
    
    ### 외부 봇 연동 예제
    ```python
    import requests
    
    # TTS 생성 요청
    response = requests.post(
        "http://localhost:8000/tts/generate",
        json={
            "text": "안녕하세요, 테스트 음성입니다.",
            "voice_id": "voice_abc123",
            "language": "Korean"
        }
    )
    
    # 음성 파일 저장
    with open("output.wav", "wb") as f:
        f.write(response.content)
    ```
    """,
    version="1.0.0",
    contact={
        "name": "Qwen3-TTS API Support",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# CORS 설정 (외부 봇에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    logger.info("=" * 60)
    logger.info("🚀 Qwen3-TTS API 서버 시작 중...")
    logger.info("=" * 60)
    logger.info("📚 모델: Qwen3-TTS-12Hz-1.7B-Base")
    logger.info("🌍 다국어 지원: 한국어, 영어, 중국어, 일본어 등 10개 언어")
    logger.info("🎤 Voice Clone: 3초 이상 음성 샘플로 빠른 복제")
    logger.info("=" * 60)
    
    # TTS 서비스 초기화 (모델 로드)
    from .tts_service import tts_service
    logger.info("🔧 TTS 서비스 초기화 중...")
    _ = tts_service.model  # 모델 로드 트리거
    logger.info("✅ TTS 서비스 준비 완료!")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    logger.info("=" * 60)
    logger.info("👋 Qwen3-TTS API 서버 종료 중...")
    logger.info("=" * 60)


@app.get("/", tags=["System"])
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Qwen3-TTS API 서버에 오신 것을 환영합니다!",
        "docs": "/docs",
        "model": "Qwen3-TTS-12Hz-1.7B-Base",
        "features": [
            "Voice Clone (음성 복제)",
            "TTS Generation (텍스트 음성 변환)",
            "Multi-language Support (다국어 지원)"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
