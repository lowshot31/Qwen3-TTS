import torch
from qwen_tts import Qwen3TTSModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TTSService:
    """
    TTS 서비스 싱글톤 클래스
    Qwen3-TTS 모델을 로드하고 관리합니다.
    """
    _instance: Optional['TTSService'] = None
    _model: Optional[Qwen3TTSModel] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """모델이 아직 로드되지 않았다면 초기화"""
        if self._model is None:
            self._initialize_model()
    
    def _initialize_model(self):
        """Qwen3-TTS 모델 초기화"""
        logger.info("🚀 Qwen3-TTS 모델을 로드 중입니다...")
        
        try:
            # Qwen3-TTS-12Hz-1.7B-Base 모델 로드
            # Voice Clone 기능을 위한 Base 모델 사용
            self._model = Qwen3TTSModel.from_pretrained(
                "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                device_map="auto",  # 자동으로 GPU 할당
                dtype=torch.bfloat16,  # 메모리 효율성을 위해 bfloat16 사용
                attn_implementation="flash_attention_2"  # Flash Attention 2 사용
            )
            logger.info("✅ 모델 로드 완료!")
            logger.info(f"📊 모델 정보: Qwen3-TTS-12Hz-1.7B-Base")
            logger.info(f"💾 Device: {next(self._model.parameters()).device}")
            
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {str(e)}")
            # Flash Attention 2가 없는 경우 대체 방법 시도
            if "flash_attention_2" in str(e):
                logger.warning("⚠️ Flash Attention 2를 사용할 수 없습니다. SDPA로 대체합니다.")
                self._model = Qwen3TTSModel.from_pretrained(
                    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
                    device_map="auto",
                    dtype=torch.bfloat16,
                    attn_implementation="sdpa"
                )
                logger.info("✅ 모델 로드 완료 (SDPA 사용)")
            else:
                raise
    
    @property
    def model(self) -> Qwen3TTSModel:
        """모델 인스턴스 반환"""
        if self._model is None:
            self._initialize_model()
        return self._model
    
    def generate_voice_clone(
        self,
        text: str,
        language: str,
        voice_clone_prompt,
        **kwargs
    ):
        """
        Voice Clone을 사용하여 TTS 생성
        
        Args:
            text: 음성으로 변환할 텍스트
            language: 언어 (Auto, Korean, English 등)
            voice_clone_prompt: create_voice_clone_prompt로 생성된 프롬프트
            **kwargs: 추가 생성 파라미터
        
        Returns:
            (wavs, sample_rate): 생성된 오디오와 샘플레이트
        """
        logger.info(f"🎤 TTS 생성 시작: '{text[:50]}...' (언어: {language})")
        
        # 기본 생성 파라미터
        default_kwargs = {
            "max_new_tokens": 2048,
            "do_sample": True,
            "top_k": 50,
            "top_p": 1.0,
            "temperature": 0.9,
            "repetition_penalty": 1.05,
        }
        default_kwargs.update(kwargs)
        
        try:
            wavs, sr = self.model.generate_voice_clone(
                text=text,
                language=language,
                voice_clone_prompt=voice_clone_prompt,
                **default_kwargs
            )
            logger.info(f"✅ TTS 생성 완료 (샘플레이트: {sr}Hz)")
            return wavs, sr
            
        except Exception as e:
            logger.error(f"❌ TTS 생성 실패: {str(e)}")
            raise
    
    def create_voice_clone_prompt(
        self,
        ref_audio,
        ref_text: str,
        x_vector_only_mode: bool = False
    ):
        """
        Voice Clone Prompt 생성
        
        Args:
            ref_audio: 참조 오디오 (파일 경로, URL, numpy array 등)
            ref_text: 참조 오디오의 텍스트
            x_vector_only_mode: True면 speaker embedding만 사용 (ref_text 불필요)
        
        Returns:
            voice_clone_prompt: 재사용 가능한 프롬프트
        """
        logger.info(f"🎯 Voice Clone Prompt 생성 중... (x_vector_only: {x_vector_only_mode})")
        
        try:
            prompt_items = self.model.create_voice_clone_prompt(
                ref_audio=ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only_mode
            )
            logger.info("✅ Voice Clone Prompt 생성 완료")
            return prompt_items
            
        except Exception as e:
            logger.error(f"❌ Prompt 생성 실패: {str(e)}")
            raise


# 싱글톤 인스턴스 생성
tts_service = TTSService()
