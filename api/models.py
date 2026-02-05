from pydantic import BaseModel, Field
from typing import Optional, List


class VoiceRegisterRequest(BaseModel):
    """커스텀 보이스 등록 요청"""
    voice_name: str = Field(..., description="보이스 이름")
    ref_text: str = Field(..., description="참조 오디오의 텍스트 (음성 파일에서 말한 내용)")
    language: str = Field(default="Auto", description="언어 (Auto, Korean, English, Chinese, Japanese 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "voice_name": "my_custom_voice",
                "ref_text": "안녕하세요, 저는 커스텀 보이스입니다.",
                "language": "Korean"
            }
        }


class VoiceRegisterResponse(BaseModel):
    """보이스 등록 응답"""
    voice_id: str = Field(..., description="생성된 보이스 ID")
    voice_name: str = Field(..., description="보이스 이름")
    message: str = Field(..., description="응답 메시지")


class TTSGenerateRequest(BaseModel):
    """TTS 생성 요청"""
    text: str = Field(..., description="음성으로 변환할 텍스트")
    voice_id: str = Field(..., description="사용할 보이스 ID")
    language: str = Field(default="Auto", description="언어 (Auto, Korean, English, Chinese, Japanese 등)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "안녕하세요, 부모님의 병원비를 위해 열심히 일하고 있습니다.",
                "voice_id": "voice_abc123",
                "language": "Korean"
            }
        }


class VoiceInfo(BaseModel):
    """보이스 정보"""
    voice_id: str = Field(..., description="보이스 ID")
    voice_name: str = Field(..., description="보이스 이름")
    ref_text: str = Field(..., description="참조 텍스트")
    language: str = Field(..., description="언어")
    created_at: str = Field(..., description="생성 시간")


class VoiceListResponse(BaseModel):
    """보이스 목록 응답"""
    voices: List[VoiceInfo] = Field(..., description="등록된 보이스 목록")
    total: int = Field(..., description="전체 보이스 수")


class ErrorResponse(BaseModel):
    """에러 응답"""
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
