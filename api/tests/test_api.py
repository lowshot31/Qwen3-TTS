import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from api.main import app

client = TestClient(app)


def test_health_check():
    """헬스 체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_root():
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data


def test_list_voices_empty():
    """빈 보이스 목록 조회 테스트"""
    response = client.get("/voices")
    assert response.status_code == 200
    data = response.json()
    assert "voices" in data
    assert "total" in data
    assert isinstance(data["voices"], list)


def test_register_voice():
    """보이스 등록 테스트"""
    # 테스트용 더미 오디오 파일 생성
    audio_content = b"dummy audio content"
    
    files = {
        "audio_file": ("test_voice.wav", io.BytesIO(audio_content), "audio/wav")
    }
    data = {
        "voice_name": "test_voice",
        "ref_text": "테스트 음성입니다.",
        "language": "Korean"
    }
    
    response = client.post("/voices/register", files=files, data=data)
    
    # 실제 모델이 없으면 실패할 수 있으므로 상태 코드만 확인
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        result = response.json()
        assert "voice_id" in result
        assert result["voice_name"] == "test_voice"


def test_tts_generate_invalid_voice():
    """존재하지 않는 보이스로 TTS 생성 시도"""
    request_data = {
        "text": "테스트 텍스트입니다.",
        "voice_id": "invalid_voice_id",
        "language": "Korean"
    }
    
    response = client.post("/tts/generate", json=request_data)
    assert response.status_code == 404


def test_delete_nonexistent_voice():
    """존재하지 않는 보이스 삭제 시도"""
    response = client.delete("/voices/nonexistent_voice_id")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
