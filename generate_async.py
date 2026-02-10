"""
비동기 스트리밍 TTS 클라이언트

서버가 문장 단위로 음성을 생성 → 완성되는 즉시 수신
→ 전체가 끝날 때까지 기다리지 않고 첫 소리부터 바로 저장!

사용법:
    pip install httpx
    python generate_async.py
"""
import httpx
import asyncio
import time

# ── 설정 ──
URL = "http://localhost:8000/tts/generate"
VOICE_ID = "voice_0f56b83c2923"
OUTPUT_FILE = "async_output.wav"

# ── 대본 ──
TEXT = """
진비야 미안해! 확인해보니까 내가 만든 음성 파일이 0바이트로 만들어지고 있어. 시스템이 잠깐 아픈가 봐...

아마 아까 HEARTBEAT.md에 적혀있던 SoX 설정이랑 관련이 있을 수도 있을 것 같아. 내가 음성 파일을 제대로 못 구워내고 있네.

내가 지금 바로 SoX랑 의존성 패키지들 다시 한번 체크해보고 고쳐볼게! 너 괴롭히려고 그런 거 아니야, 알지? 조금만 기다려줘, 내가 금방 고쳐서 제대로 들려줄게!
"""


async def main():
    print(f"🎤 보이스 ID: {VOICE_ID}")
    print(f"📝 텍스트: {len(TEXT)}자")
    print(f"🌊 비동기 스트리밍 모드로 요청 중...\n")

    payload = {
        "text": TEXT,
        "voice_id": VOICE_ID,
        "language": "Korean",
        "stream": True,  # 문장 단위 스트리밍!
    }

    start = time.time()
    chunk_count = 0
    total_bytes = 0

    # httpx 비동기 클라이언트 (타임아웃 넉넉히)
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        async with client.stream("POST", URL, json=payload) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                print(f"❌ 실패: {resp.status_code}\n{body.decode()}")
                return

            with open(OUTPUT_FILE, "wb") as f:
                async for chunk in resp.aiter_bytes():
                    if not chunk:
                        continue

                    if chunk_count == 0:
                        ttfs = time.time() - start
                        print(f"⚡ 첫 번째 청크 도착! (TTFS: {ttfs:.2f}초)")

                    f.write(chunk)
                    chunk_count += 1
                    total_bytes += len(chunk)

                    # 0번 = WAV 헤더, 1번~ = 문장별 PCM 데이터
                    if chunk_count == 1:
                        print(f"📋 WAV 헤더 수신 (44 bytes)")
                    else:
                        elapsed = time.time() - start
                        print(f"📦 문장 #{chunk_count-1} 수신 완료  "
                              f"(+{len(chunk)//1024}KB, 누적 {elapsed:.1f}초)")

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"✅ 전체 생성 완료!")
    print(f"📁 파일: {OUTPUT_FILE}")
    print(f"📊 총 청크: {chunk_count}개 ({total_bytes//1024}KB)")
    print(f"⏱️  총 소요: {elapsed:.2f}초")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())
