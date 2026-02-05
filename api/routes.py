from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
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
    description="음성 파일과 텍스트를 업로드하여 새로운 커스텀 보이스를 등록합니다.",
    tags=["Voice Management"]
)
async def register_voice(
    audio_file: UploadFile = File(..., description="음성 파일 (WAV, MP3 등)"),
    voice_name: str = Form(..., description="보이스 이름"),
    ref_text: str = Form(..., description="음성 파일에서 말한 텍스트"),
    language: str = Form(default="Auto", description="언어 (Auto, Korean, English 등)")
):
    """
    커스텀 보이스 등록
    
    - **audio_file**: 3초 이상의 음성 샘플 파일
    - **voice_name**: 보이스를 식별할 이름
    - **ref_text**: 음성 파일에서 실제로 말한 내용
    - **language**: 언어 설정 (Auto로 설정하면 자동 감지)
    """
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio_file.filename).suffix) as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"📤 보이스 등록 요청: {voice_name} (파일: {audio_file.filename})")
        
        # 보이스 등록
        voice_id = voice_manager.register_voice(
            audio_file_path=tmp_file_path,
            voice_name=voice_name,
            ref_text=ref_text,
            language=language
        )
        
        # 임시 파일 삭제
        Path(tmp_file_path).unlink()
        
        return VoiceRegisterResponse(
            voice_id=voice_id,
            voice_name=voice_name,
            message=f"보이스가 성공적으로 등록되었습니다. Voice ID: {voice_id}"
        )
        
    except Exception as e:
        logger.error(f"❌ 보이스 등록 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보이스 등록 실패: {str(e)}")


@router.post(
    "/tts/generate",
    summary="TTS 생성",
    description="텍스트와 보이스 ID를 사용하여 음성을 생성합니다.",
    tags=["TTS Generation"],
    responses={
        200: {
            "content": {"audio/wav": {}},
            "description": "생성된 WAV 오디오 파일"
        }
    }
)
async def generate_tts(request: TTSGenerateRequest):
    """
    TTS 생성
    
    - **text**: 음성으로 변환할 텍스트
    - **voice_id**: 사용할 커스텀 보이스 ID
    - **language**: 언어 설정 (Auto, Korean, English 등)
    
    Returns:
        WAV 형식의 오디오 파일 스트림
    """
    try:
        logger.info(f"🎤 TTS 생성 요청: voice_id={request.voice_id}, text='{request.text[:50]}...'")
        
        # Voice Clone Prompt 가져오기 (캐시 사용)
        voice_prompt = voice_manager.get_or_create_prompt(request.voice_id, tts_service)
        
        # TTS 생성 (비동기 처리)
        wavs, sr = await asyncio.to_thread(
            tts_service.generate_voice_clone,
            text=request.text,
            language=request.language,
            voice_clone_prompt=voice_prompt
        )
        
        # WAV 파일로 변환
        wav_io = io.BytesIO()
        sf.write(wav_io, wavs[0], sr, format='WAV')
        wav_io.seek(0)
        
        logger.info(f"✅ TTS 생성 완료: {len(wavs[0])} samples, {sr}Hz")
        
        return StreamingResponse(
            wav_io,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_output.wav"
            }
        )
        
    except ValueError as e:
        logger.error(f"❌ 잘못된 요청: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ TTS 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS 생성 실패: {str(e)}")


@router.get(
    "/voices",
    response_model=VoiceListResponse,
    summary="보이스 목록 조회",
    description="등록된 모든 커스텀 보이스 목록을 조회합니다.",
    tags=["Voice Management"]
)
async def list_voices():
    """
    등록된 모든 보이스 목록 반환
    """
    try:
        voices_data = voice_manager.list_voices()
        
        voices = [
            VoiceInfo(
                voice_id=v["voice_id"],
                voice_name=v["voice_name"],
                ref_text=v["ref_text"],
                language=v["language"],
                created_at=v["created_at"]
            )
            for v in voices_data
        ]
        
        return VoiceListResponse(
            voices=voices,
            total=len(voices)
        )
        
    except Exception as e:
        logger.error(f"❌ 보이스 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보이스 목록 조회 실패: {str(e)}")


@router.delete(
    "/voices/{voice_id}",
    summary="보이스 삭제",
    description="등록된 커스텀 보이스를 삭제합니다.",
    tags=["Voice Management"]
)
async def delete_voice(voice_id: str):
    """
    보이스 삭제
    
    - **voice_id**: 삭제할 보이스 ID
    """
    try:
        success = voice_manager.delete_voice(voice_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"존재하지 않는 보이스 ID: {voice_id}")
        
        return {"message": f"보이스가 성공적으로 삭제되었습니다: {voice_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 보이스 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보이스 삭제 실패: {str(e)}")


@router.get(
    "/health",
    summary="헬스 체크",
    description="API 서버 상태를 확인합니다.",
    tags=["System"]
)
async def health_check():
    """
    서버 헬스 체크
    """
    return {
        "status": "healthy",
        "model": "Qwen3-TTS-12Hz-1.7B-Base",
        "message": "TTS API 서버가 정상 작동 중입니다."
    }
