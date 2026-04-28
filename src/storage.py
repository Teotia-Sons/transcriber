import io
import wave

from google.cloud import storage

from config import Config

from .db import Transcription

client = storage.Client()
bucket = client.bucket(Config.GCP_VOICE_PROMPTS_BUCKET)


def _get_wav_duration_ms(wav_bytes: bytes) -> int:
    wav_buffer = io.BytesIO(wav_bytes)
    with wave.open(wav_buffer, 'rb') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return int((frames / rate) * 1000)


def save_recording(wav_bytes: bytes, text: str, content_type: str = "audio/wav") -> str:
    duration_ms = _get_wav_duration_ms(wav_bytes)
    transcription = Transcription(text=text, duration_ms=duration_ms).save()
    blob = bucket.blob(f"{transcription.id}.wav")
    blob.upload_from_string(wav_bytes, content_type=content_type)
    return str(transcription.id)
