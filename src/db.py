from datetime import UTC, datetime

from mongoengine import DateTimeField, Document, IntField, StringField


class Transcription(Document):
    transcribed_text = StringField(required=True)
    text = StringField(required=True)
    duration_ms = IntField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
