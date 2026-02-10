import torch
import asyncio
from qwen_tts import Qwen3TTSModel
from typing import Optional, AsyncGenerator, List
import logging
import traceback
import re
import io
import struct
import soundfile as sf
import numpy as np

logger = logging.getLogger(__name__)


class TTSService:
    """
    Qwen3-TTS 서비스 클래스
    - 단판 생성 (generate_voice_clone)
    - 문장 단위 스트리밍 생성 (stream_voice_clone)
    """

    def __init__(self, model_path: str = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"):
        self.model_path = model_path
        self._model = None

    def _initialize_model(self):
        if self._model is not None:
            return
        try:
            logger.info(f"🚀 모델 로드 시작: {self.model_path}")
            self._model = Qwen3TTSModel.from_pretrained(
                self.model_path,
                device_map="auto",
                dtype=torch.bfloat16,
                attn_implementation="sdpa"
            )
            logger.info("✅ 모델 로드 완료!")
        except Exception as e:
            logger.error(f"❌ 모델 로드 실패: {str(e)}")
            raise

    @property
    def model(self) -> Qwen3TTSModel:
        if self._model is None:
            self._initialize_model()
        return self._model

    # ──────────────────────────────────────────
    # 텍스트 전처리
    # ──────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """이모지 및 소리 없는 특수문자 제거"""
        # 이모지 제거
        text = re.sub(
            r'[\U0001F600-\U0001F64F'
            r'\U0001F300-\U0001F5FF'
            r'\U0001F680-\U0001F6FF'
            r'\U0001F1E0-\U0001F1FF'
            r'\U00002702-\U000027B0'
            r'\U0000FE00-\U0000FE0F'
            r'\U0001F900-\U0001F9FF'
            r'\U0001FA00-\U0001FA6F'
            r'\U0001FA70-\U0001FAFF'
            r'\U00002600-\U000026FF]+',
            '', text
        )
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _split_sentences(self, text: str, min_chars: int = 80) -> List[str]:
        """
        문장 단위 분할 (의미 있는 묶음 유지)
        - ., !, ?, \\n 기준으로 분리
        - min_chars 이하인 짧은 문장은 다음 문장과 합침
        """
        # 문장 경계로 분리 (구분자 보존)
        parts = re.split(r'(?<=[.!?\n])\s*', text)
        parts = [p.strip() for p in parts if p.strip()]

        chunks: List[str] = []
        current = ""

        for part in parts:
            if len(current) + len(part) < min_chars:
                current = (current + " " + part).strip()
            else:
                if current:
                    chunks.append(current)
                current = part

        if current:
            chunks.append(current)

        return chunks

    # ──────────────────────────────────────────
    # 생성 파라미터
    # ──────────────────────────────────────────

    def _default_params(self, max_tokens: int = 4096) -> dict:
        return {
            "max_new_tokens": max_tokens,
            "do_sample": True,
            "top_p": 0.7,
            "temperature": 0.9,
            "repetition_penalty": 1.1,
        }

    # ──────────────────────────────────────────
    # 단판 생성 (전체 텍스트 한 번에)
    # ──────────────────────────────────────────

    def generate_voice_clone(self, text: str, language: str, voice_clone_prompt, **kwargs):
        """전체 텍스트를 한 번에 생성 (Blocking)"""
        cleaned = self._clean_text(text)
        params = self._default_params(4096)
        params.update(kwargs)

        logger.info(f"🎤 전체 생성 시작: {len(cleaned)}자")
        return self.model.generate_voice_clone(
            text=cleaned,
            language=language,
            voice_clone_prompt=voice_clone_prompt,
            **params
        )

    # ──────────────────────────────────────────
    # 문장 단위 스트리밍 생성 (비동기)
    # ──────────────────────────────────────────

    async def stream_voice_clone(
        self,
        text: str,
        language: str,
        voice_clone_prompt,
        **kwargs
    ) -> AsyncGenerator[bytes, None]:
        """
        문장 단위로 쪼개서 생성 → 완료되는 즉시 yield
        각 청크는 **raw PCM int16** 바이트로 전송하고,
        맨 앞에 WAV 헤더(44바이트)를 먼저 보냄.
        → 클라이언트는 수신 데이터를 그대로 .wav 파일로 저장 가능!
        """
        cleaned = self._clean_text(text)
        sentences = self._split_sentences(cleaned, min_chars=80)

        logger.info(f"🌊 스트리밍 시작: {len(sentences)}개 문장")
        for i, s in enumerate(sentences):
            logger.info(f"   [{i+1}] {s[:40]}...")

        params = self._default_params(2048)
        params.update(kwargs)

        # ── 1) 더미 WAV 헤더 전송 (나중에 크기 확정 불가 → 최대값 기입) ──
        yield self._make_wav_header(sample_rate=24000)

        # ── 2) 문장별 생성 & PCM 전송 ──
        for i, sentence in enumerate(sentences):
            try:
                logger.info(f"👉 [{i+1}/{len(sentences)}] 생성 중...")

                # 블로킹 모델 호출 → 스레드풀로 이동
                wavs, sr = await asyncio.to_thread(
                    self.model.generate_voice_clone,
                    text=sentence,
                    language=language,
                    voice_clone_prompt=voice_clone_prompt,
                    **params
                )

                # numpy float → int16 PCM 변환
                audio = wavs[0]
                if audio.dtype != np.int16:
                    audio = (audio * 32767).clip(-32768, 32767).astype(np.int16)

                yield audio.tobytes()
                logger.info(f"✅ [{i+1}/{len(sentences)}] 전송 완료 ({len(audio)} samples)")

            except Exception:
                logger.error(f"❌ [{i+1}] 생성 실패:\n{traceback.format_exc()}")
                continue

    @staticmethod
    def _make_wav_header(sample_rate: int = 24000, bits: int = 16, channels: int = 1) -> bytes:
        """
        스트리밍용 WAV 헤더 (data 크기 = 0xFFFFFFFF → 크기 미확정)
        대부분의 플레이어가 이를 '파일 끝까지 읽기'로 해석함.
        """
        data_size = 0xFFFFFFFF
        byte_rate = sample_rate * channels * (bits // 8)
        block_align = channels * (bits // 8)

        header = struct.pack(
            '<4sI4s'    # RIFF, filesize, WAVE
            '4sIHHIIHH' # fmt chunk
            '4sI',      # data chunk header
            b'RIFF', data_size + 36, b'WAVE',
            b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits,
            b'data', data_size
        )
        return header

    # ──────────────────────────────────────────
    # Voice Clone Prompt 생성
    # ──────────────────────────────────────────

    def create_voice_clone_prompt(self, ref_audio, ref_text: str, x_vector_only_mode: bool = False):
        try:
            logger.info("🎯 Voice Clone Prompt 생성 중...")
            return self.model.create_voice_clone_prompt(
                ref_audio=ref_audio,
                ref_text=ref_text,
                x_vector_only_mode=x_vector_only_mode
            )
        except Exception:
            logger.error(f"❌ Prompt 생성 실패:\n{traceback.format_exc()}")
            raise


# 싱글톤
tts_service = TTSService()
