import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VoiceManager:
    """
    커스텀 보이스 관리 클래스
    보이스 파일 저장, 메타데이터 관리, Voice Clone Prompt 캐싱
    """
    
    def __init__(self, voices_dir: str = "data/voices", db_path: str = "data/voices_db.json"):
        self.voices_dir = Path(voices_dir)
        self.db_path = Path(db_path)
        self.voice_prompts: Dict[str, any] = {}  # voice_id -> prompt_items 캐시
        
        # 디렉토리 생성
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # DB 파일이 없으면 생성
        if not self.db_path.exists():
            self._save_db({})
    
    def _load_db(self) -> Dict:
        """메타데이터 DB 로드"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"DB 로드 실패: {e}")
            return {}
    
    def _save_db(self, db: Dict):
        """메타데이터 DB 저장"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"DB 저장 실패: {e}")
            raise
    
    def register_voice(
        self,
        audio_file_path: str,
        voice_name: str,
        ref_text: str,
        language: str = "Auto"
    ) -> str:
        """
        새로운 보이스 등록
        
        Args:
            audio_file_path: 업로드된 오디오 파일 경로
            voice_name: 보이스 이름
            ref_text: 참조 오디오의 텍스트
            language: 언어
        
        Returns:
            voice_id: 생성된 보이스 ID
        """
        # 고유 ID 생성
        voice_id = f"voice_{uuid.uuid4().hex[:12]}"
        
        # 파일 확장자 추출
        file_ext = Path(audio_file_path).suffix
        
        # 보이스 파일 저장 경로
        voice_file_path = self.voices_dir / f"{voice_id}{file_ext}"
        
        # 파일 복사
        shutil.copy2(audio_file_path, voice_file_path)
        logger.info(f"📁 보이스 파일 저장: {voice_file_path}")
        
        # 메타데이터 저장
        db = self._load_db()
        db[voice_id] = {
            "voice_id": voice_id,
            "voice_name": voice_name,
            "audio_path": str(voice_file_path),
            "ref_text": ref_text,
            "language": language,
            "created_at": datetime.now().isoformat()
        }
        self._save_db(db)
        
        logger.info(f"✅ 보이스 등록 완료: {voice_id} ({voice_name})")
        return voice_id
    
    def get_voice(self, voice_id: str) -> Optional[Dict]:
        """보이스 정보 조회"""
        db = self._load_db()
        return db.get(voice_id)
    
    def list_voices(self) -> List[Dict]:
        """모든 보이스 목록 반환"""
        db = self._load_db()
        return list(db.values())
    
    def delete_voice(self, voice_id: str) -> bool:
        """
        보이스 삭제
        
        Args:
            voice_id: 삭제할 보이스 ID
        
        Returns:
            성공 여부
        """
        db = self._load_db()
        
        if voice_id not in db:
            logger.warning(f"⚠️ 존재하지 않는 보이스: {voice_id}")
            return False
        
        # 파일 삭제
        voice_data = db[voice_id]
        audio_path = Path(voice_data["audio_path"])
        
        if audio_path.exists():
            audio_path.unlink()
            logger.info(f"🗑️ 파일 삭제: {audio_path}")
        
        # DB에서 제거
        del db[voice_id]
        self._save_db(db)
        
        # 캐시에서 제거
        if voice_id in self.voice_prompts:
            del self.voice_prompts[voice_id]
        
        logger.info(f"✅ 보이스 삭제 완료: {voice_id}")
        return True
    
    def get_or_create_prompt(self, voice_id: str, tts_service):
        """
        Voice Clone Prompt 가져오기 (캐시 사용)
        
        Args:
            voice_id: 보이스 ID
            tts_service: TTSService 인스턴스
        
        Returns:
            voice_clone_prompt: 재사용 가능한 프롬프트
        """
        # 캐시에 있으면 반환
        if voice_id in self.voice_prompts:
            logger.info(f"💾 캐시된 Prompt 사용: {voice_id}")
            return self.voice_prompts[voice_id]
        
        # 보이스 정보 로드
        voice_data = self.get_voice(voice_id)
        if not voice_data:
            raise ValueError(f"존재하지 않는 보이스 ID: {voice_id}")
        
        # Prompt 생성
        logger.info(f"🔨 새로운 Prompt 생성: {voice_id}")
        prompt_items = tts_service.create_voice_clone_prompt(
            ref_audio=voice_data["audio_path"],
            ref_text=voice_data["ref_text"],
            x_vector_only_mode=False
        )
        
        # 캐시에 저장
        self.voice_prompts[voice_id] = prompt_items
        
        return prompt_items
    
    def clear_prompt_cache(self, voice_id: Optional[str] = None):
        """
        Prompt 캐시 삭제
        
        Args:
            voice_id: 특정 보이스 ID (None이면 전체 삭제)
        """
        if voice_id:
            if voice_id in self.voice_prompts:
                del self.voice_prompts[voice_id]
                logger.info(f"🧹 캐시 삭제: {voice_id}")
        else:
            self.voice_prompts.clear()
            logger.info("🧹 전체 캐시 삭제")


# 싱글톤 인스턴스 생성
voice_manager = VoiceManager()
