import io
import threading
import wave

from google.cloud import storage

from config import Config

from .db import Transcription

client = storage.Client()
bucket = client.bucket(Config.GCP_VOICE_PROMPTS_BUCKET)


def _get_wav_duration_ms(wav_bytes: bytes) -> int:
    wav_buffer = io.BytesIO(wav_bytes)
    with wave.open(wav_buffer, "rb") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return int((frames / rate) * 1000)


def _upload_to_gcs(blob_name: str, wav_bytes: bytes, content_type: str):
    blob = bucket.blob(blob_name)
    blob.upload_from_string(wav_bytes, content_type=content_type)


def save_recording(wav_bytes: bytes, text: str, content_type: str = "audio/wav") -> str:
    duration_ms = _get_wav_duration_ms(wav_bytes)
    transcription = Transcription(text=text, duration_ms=duration_ms).save()
    blob_name = f"{transcription.id}.wav"
    thread = threading.Thread(
        target=_upload_to_gcs, args=(blob_name, wav_bytes, content_type), daemon=True
    )
    thread.start()
    return str(transcription.id)
