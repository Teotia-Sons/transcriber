from datetime import UTC, datetime

from mongoengine import DateTimeField, Document, StringField, connect

from config import Config

connect(host=Config.MONGO_URI)


class Transcription(Document):
    text = StringField(required=True)
    created_at = DateTimeField(default=lambda: datetime.now(UTC))
