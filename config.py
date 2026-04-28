import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGO_URI = os.environ["MONGO_URI"]
    GCP_VOICE_PROMPTS_BUCKET = os.environ["GCP_VOICE_PROMPTS_BUCKET"]
    DEEPINFRA_API_KEY = os.environ["DEEPINFRA_API_KEY"]

    OTEL_EXPORTER_OTLP_ENDPOINT = os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    OTEL_EXPORTER_OTLP_API_KEY = os.environ["OTEL_EXPORTER_OTLP_API_KEY"]
