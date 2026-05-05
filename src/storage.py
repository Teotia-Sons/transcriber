import threading

from google.cloud import storage

from config import Config

client = storage.Client()
bucket = client.bucket(Config.GCP_VOICE_PROMPTS_BUCKET)


def _upload_to_gcs(blob_name: str, wav_bytes: bytes):
    blob = bucket.blob(blob_name)
    blob.upload_from_string(wav_bytes, content_type="audio/wav")


def upload_recording(transcription_id: str, wav_bytes: bytes):
    blob_name = f"{transcription_id}.wav"
    thread = threading.Thread(
        target=_upload_to_gcs, args=(blob_name, wav_bytes), daemon=True
    )
    thread.start()
