from groq import Groq
from opentelemetry import trace

from config import Config

client = Groq(api_key=Config.GROQ_API_KEY)
tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("transcribe")
def transcribe(wav_bytes: bytes) -> str:
    response = client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=("audio.wav", wav_bytes),
        response_format="text",
    )
    return response
