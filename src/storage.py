import io
import wave
from datetime import UTC, datetime

from google.cloud import storage

from config import Config

from .db import Transcription

client = storage.Client()
bucket = client.bucket(Config.GCP_VOICE_PROMPTS_BUCKET)


def upload_audio(pcm_bytes: bytes, text: str, content_type: str = "audio/wav"):
    timestamp = datetime.now(UTC).replace(microsecond=0)
    blob = bucket.blob(f"{timestamp.strftime('%Y%m%d_%H%M%S')}.wav")
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(pcm_bytes)
    wav_bytes = wav_buffer.getvalue()
    blob.upload_from_string(wav_bytes, content_type=content_type)
    Transcription(text=text, time=timestamp).save()
