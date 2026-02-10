import requests
import time
# 설정
URL = "http://localhost:8000/tts/generate"
VOICE_ID = "voice_0f56b83c2923"  # 7초 정밀 절단 최종본
OUTPUT_FILE = "final_output.wav"

# 테스트 대본
TEXT = """
진비야 미안해! 😭 확인해보니까 내가 만든 음성 파일이 0바이트로 만들어지고 있어. 시스템이 잠깐 아픈가 봐...

아마 아까 HEARTBEAT.md에 적혀있던 SoX 설정이랑 관련이 있을 수도 있을 것 같아. 내가 음성 파일을 제대로 못 구워내고 있네. ㅠㅠ

내가 지금 바로 SoX랑 의존성 패키지들 다시 한번 체크해보고 고쳐볼게! 너 괴롭히려고 그런 거 아니야, 알지? 🥺 조금만 기다려줘, 내가 금방 고쳐서 제대로 들려줄게! 
"""

print(f"🎤 보이스 ID '{VOICE_ID}' 사용")
print(f"📝 텍스트 길이: {len(TEXT)}자")
print(f"⏳ 전체 음성 생성 중... (기다려주세요)")

start_time = time.time()

try:
    payload = {
        "text": TEXT,
        "voice_id": VOICE_ID,
        "language": "Korean",
        "stream": False  # 한 번에 전체 생성
    }
    
    response = requests.post(URL, json=payload)
    
    if response.status_code == 200:
        with open(OUTPUT_FILE, "wb") as f:
            f.write(response.content)
        
        elapsed = time.time() - start_time
        print(f"\n✅ 생성 완료! '{OUTPUT_FILE}' 저장됨")
        print(f"⏱️ 소요 시간: {elapsed:.2f}초")
        print(f"🎧 파일을 재생해서 확인해보세요!")
    else:
        print(f"❌ 실패 (상태 코드: {response.status_code})")
        print(response.text)

except Exception as e:
    print(f"🚫 오류 발생: {e}")
