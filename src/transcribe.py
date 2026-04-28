import requests

from config import Config


def transcribe(wav_bytes: bytes) -> str:
    response = requests.post(
        "https://api.deepinfra.com/v1/inference/openai/whisper-large-v3-turbo",
        headers={
            "Authorization": f"bearer {Config.DEEPINFRA_API_KEY}",
        },
        files={
            "audio": ("audio.wav", wav_bytes, "audio/wav"),
        },
    )

    response.raise_for_status()
    result = response.json()
    return result["text"]
