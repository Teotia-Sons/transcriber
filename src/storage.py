from google.cloud import storage

from config import Config

from .db import Transcription

client = storage.Client()
bucket = client.bucket(Config.GCP_VOICE_PROMPTS_BUCKET)


def upload_audio(wav_bytes: bytes, text: str, content_type: str = "audio/wav"):
    transcription = Transcription(text=text).save()
    blob = bucket.blob(f"{transcription.id}.wav")
    blob.upload_from_string(wav_bytes, content_type=content_type)
