import torch
import soundfile as sf
import os
import subprocess
from qwen_tts import Qwen3TTSModel

# 1. 설정
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
REF_AUDIO_PATH = r"C:\음성파일\last_kids.m4a"
TEMP_WAV_PATH = "temp_reference.wav"
OUTPUT_FILE = "output_kids_clone_final.wav"

# --- [고품질 정밀 복제 설정] ---
# 1분 전체가 아니라 가장 깨끗한 '5~6초' 구간만 쓰는 것이 정석입니다.
START_SEC = "0"    # 시작 시간
DURATION = "7"     # 자르는 길이 (5~7초 추천)

# 중요: 위 구간(START_SEC부터 DURATION까지)에서 실제 한 말을 아주 똑같이(쉼표 포함) 적어주세요.
# 예: "망내는 아무래도 가슴보다 골반" 
REF_TEXT = "근데 골반이 진짜 넓어 망내는 역시 가슴보다는골반..여러분들은 제 방송의 묘미가 뭐라고생각하세여" 
# ------------------------------

def convert_and_crop(input_path, output_path, start, duration):
    try:
        subprocess.run([
            "static_ffmpeg", "-y", "-ss", start, "-t", duration, "-i", input_path, 
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", output_path
        ], check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"❌ 변환 실패: {e}")
        return False

print(f"🚀 [최종 안정화 모드] Voice Clone 시작!")

if not os.path.exists(REF_AUDIO_PATH):
    print(f"⚠️ 에러: '{REF_AUDIO_PATH}' 파일을 찾을 수 없습니다.")
    exit()

convert_and_crop(REF_AUDIO_PATH, TEMP_WAV_PATH, START_SEC, DURATION)

try:
    print(f"📥 모델 로딩 중...")
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="auto",
        dtype=torch.bfloat16, 
        attn_implementation="sdpa"
    )
    
    # 텍스트가 없으면(비어있으면) 자동으로 목소리 특징만 추출하는 모드로 작동
    USE_X_VECTOR = len(REF_TEXT.strip()) < 2
    
    print(f"🎯 목소리 분석 중... (모드: {'특징 추출' if USE_X_VECTOR else '정밀 복제'})")
    voice_clone_prompt = model.create_voice_clone_prompt(
        ref_audio=TEMP_WAV_PATH,
        ref_text=REF_TEXT,
        x_vector_only_mode=USE_X_VECTOR
    )

    # 3. 음성 생성 (주신 긴 대본 적용)
    GEN_TEXT = """
당연히 알지! 그 댕댕이가 "왜요?" 하는 눈빛으로 쳐다보는 그거잖아. 🐶

진비야, 혹시 지금 나한테 뭐 부탁받고 "왜요?" 시전하려는 거야? 아니면 내가 무슨 말만 하면 "왜요?" 하고 장난치려고? ㅋㅋㅋ

너 그 밈 쓰면서 나 놀리면 나도 "안돼요!" 밈으로 받아칠 거야! 흥! 😤❤️
"""
    print(f"⏳ 긴 대본 음성 생성 중... (텍스트 길이: {len(GEN_TEXT)}자)")
    
    wavs, sr = model.generate_voice_clone(
        text=GEN_TEXT,
        language="Korean",
        voice_clone_prompt=voice_clone_prompt,
        temperature=0.9,
        top_p=0.9,
        do_sample=True,
        repetition_penalty=1.1,
        max_new_tokens=4096  # 긴 텍스트를 위해 토큰 수를 넉넉히 늘렸습니다.
    )

    output_path = "output_long_script.wav"
    sf.write(output_path, wavs[0], sr)
    print(f"\n🎉 완료! '{output_path}' 파일이 생성되었습니다.")
    print("이 파일에서 한국어 목소리가 나오는지 확인해주세요!")

    if os.path.exists(TEMP_WAV_PATH):
        os.remove(TEMP_WAV_PATH)

except Exception as e:
    print(f"\n🚫 오류 발생: {e}")
