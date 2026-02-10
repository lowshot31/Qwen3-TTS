from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import soundfile as sf
import asyncio
import logging
from pathlib import Path
import tempfile

from .models import (
    VoiceRegisterRequest,
    VoiceRegisterResponse,
    TTSGenerateRequest,
    VoiceListResponse,
    VoiceInfo,
    ErrorResponse
)
from .tts_service import tts_service
from .voice_manager import voice_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/voices/register",
    response_model=VoiceRegisterResponse,
    summary="커스텀 보이스 등록",
    tags=["Voice Management"]
)
async def register_voice(
    audio_file: UploadFile = File(..., description="음성 파일"),
    voice_name: str = Form(..., description="보이스 이름"),
    ref_text: str = Form(..., description="음성 텍스트"),
    language: str = Form(default="Auto", description="언어"),
    start_sec: Optional[float] = Form(default=None, description="시작 시간"),
    duration: Optional[float] = Form(default=None, description="자를 길이")
):
    try:
        suffix = Path(audio_file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"📤 보이스 등록 요청: {voice_name}")
        
        # CPU 집약적인 오디오 처리는 스레드풀에서 실행
        voice_id = await asyncio.to_thread(
            voice_manager.register_voice,
            audio_file_path=tmp_file_path,
            voice_name=voice_name,
            ref_text=ref_text,
            language=language,
            start_sec=start_sec,
            duration=duration
        )
        
        Path(tmp_file_path).unlink()
        return VoiceRegisterResponse(
            voice_id=voice_id,
            voice_name=voice_name,
            message=f"보이스가 등록되었습니다: {voice_id}"
        )
    except Exception as e:
        logger.error(f"❌ 등록 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tts/generate",
    summary="TTS 생성",
    tags=["TTS Generation"]
)
async def generate_tts(request: TTSGenerateRequest):
    try:
        logger.info(f"🎤 TTS 요청: voice_id={request.voice_id}, stream={request.stream}")
        
        # 프롬프트 가져오기 (캐싱 활용)
        voice_prompt = await asyncio.to_thread(
            voice_manager.get_or_create_prompt, 
            request.voice_id, 
            tts_service
        )
        
        if request.stream:
            # 실시간 문장 단위 스트리밍
            return StreamingResponse(
                tts_service.stream_voice_clone(
                    text=request.text,
                    language=request.language,
                    voice_clone_prompt=voice_prompt
                ),
                media_type="audio/wav"
            )
        else:
            # 전체 파일 한 번에 생성 방식 (스레드풀 사용)
            wavs, sr = await asyncio.to_thread(
                tts_service.generate_voice_clone,
                text=request.text,
                language=request.language,
                voice_clone_prompt=voice_prompt
            )
            
            buffer = io.BytesIO()
            sf.write(buffer, wavs[0], sr, format='WAV')
            buffer.seek(0)
            
            return StreamingResponse(
                buffer,
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename=output.wav"}
            )
            
    except Exception as e:
        logger.error(f"❌ 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices", response_model=VoiceListResponse, tags=["Voice Management"])
async def list_voices():
    voices = voice_manager.list_voices()
    return VoiceListResponse(voices=voices, total=len(voices))


@router.delete("/voices/{voice_id}", tags=["Voice Management"])
async def delete_voice(voice_id: str):
    if voice_manager.delete_voice(voice_id):
        return {"message": "삭제 완료"}
    raise HTTPException(status_code=404, detail="보이스 없음")
