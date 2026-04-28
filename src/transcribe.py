import requests

from config import Config


def transcribe(wav_bytes: bytes) -> str:
    response = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={"Authorization": f"Bearer {Config.GROQ_API_KEY}"},
        files={"file": ("audio.wav", wav_bytes, "audio/wav")},
        data={"model": "whisper-large-v3-turbo", "response_format": "json"},
    )
    
    response.raise_for_status()
    result = response.json()

    return result["text"].strip()
