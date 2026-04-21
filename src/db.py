from mongoengine import DateTimeField, Document, StringField, connect

from config import Config

connect(host=Config.MONGO_URI)


class Transcription(Document):
    time = DateTimeField(required=True, unique=True)
    text = StringField(required=True)
