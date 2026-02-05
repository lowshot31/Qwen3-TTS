import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

# 1. 모델 ID 설정 (CustomVoice: 텍스트 -> 음성 변환용)
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

print(f"🚀 모델을 로드 중입니다... ({MODEL_ID})")
print("📥 모델 다운로드 및 로딩에 시간이 걸릴 수 있습니다.")

try:
    # 2. 모델 불러오기
    # Flash Attention 2가 설치되어 있다면 사용 (빠름), 아니면 'sdpa'나 'eager' 사용
    # 여기서는 일단 flash_attention_2 시도. 에러나면 sdpa로 변경하세요.
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map="auto",
        dtype=torch.float16, 
        attn_implementation="flash_attention_2" 
    )
    
    print("✅ 모델 로드 성공! 음성 생성을 시작합니다.")

    # 3. 테스트할 텍스트 (한국어)
    text = "안녕하세요! Qwen3-TTS 모델 테스트 중입니다. 목소리가 잘 들리시나요? 부모님의 병원비를 위해 오늘도 열심히 일하고 있습니다."
    
    # 4. 음성 생성 (한국어 화자 Sohee)
    print("⏳ 오디오 생성 중... (화자: Sohee)")
    wavs, sr = model.generate_custom_voice(
        text=text,
        language="Korean",
        speaker="Sohee", 
        instruct="Warm and determined" # 따뜻하고 결의에 찬 목소리
    )

    # 5. 저장
    output_file = "output_sohee.wav"
    sf.write(output_file, wavs[0], sr)
    
    print(f"🎉 성공! '{output_file}' 파일이 저장되었습니다.")
    print("탐색기에서 해당 파일을 재생해보세요.")

except Exception as e:
    print("\n🚫 오류 발생!")
    print(str(e))
    if "flash_attention_2" in str(e):
        print("\n💡 팁: Flash Attention 2 에러가 났다면, 코드에서 attn_implementation='sdpa' 로 변경해서 다시 시도해보세요.")
