import json
import sys
import threading
import time
from datetime import datetime
from typing import Optional

import websocket
from loguru import logger

from config import Config


class Transcriber:
    def __init__(
        self,
    ):
        self._ws: Optional[websocket.WebSocketApp] = None
        self._state: dict[str, str] = {}
        self._text: str = ""
        self._is_connected_event: threading.Event = threading.Event()
        self._is_complete_event: threading.Event = threading.Event()

    def start(self):
        self._connect()

    def send_chunk(self, chunk: bytes):
        assert self._ws
        self._ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)

    def stop(self):
        checkpoint = json.dumps({"checkpoint_id": "final"})
        assert self._ws
        self._ws.send(checkpoint)
        self._is_complete_event.wait(timeout=5)

        self._disconnect()
        logger.debug("Transcription stopped")

        return self._text

    def cancel(self):
        self._disconnect()
        logger.debug("Transcription cancelled")

    def _connect(self):
        ws = websocket.WebSocketApp(
            "wss://audio-streaming.api.fireworks.ai/v1/audio/transcriptions/streaming",
            header={"Authorization": Config.FIREWORKS_API_KEY},
            on_message=self._on_message,
            on_error=self._on_error,
            on_open=self._on_open,
        )
        thread = threading.Thread(target=ws.run_forever)
        thread.start()
        self._ws = ws
        self._is_connected_event.wait(timeout=5)
        logger.debug("Transcription started")

    def _on_message(self, ws, message):
        data = json.loads(message)

        if "text" in data:
            self._text = data["text"]
            return

        assert data.get("checkpoint_id") == "final"
        self._is_complete_event.set()

    def _disconnect(self):
        assert self._ws
        self._ws.close()
        self._ws = None

    def _on_open(self, ws):
        self._is_connected_event.set()

    @staticmethod
    def _on_error(ws, error):
        logger.error(f"WebSocket error: {error}")


if __name__ == "__main__":
    from .recorder import BYTES_PER_FRAME, FRAMES_PER_SECOND

    if len(sys.argv) < 2:
        logger.error("Usage: python -m src.transcriber <filepath>")
        logger.error("Example: python -m src.transcriber test.pcm")
        sys.exit(1)

    transcriber = Transcriber()
    transcriber.start()

    with open(sys.argv[1], "rb") as pcm_file:
        while True:
            chunk = pcm_file.read(FRAMES_PER_SECOND * BYTES_PER_FRAME)
            if not chunk:
                break
            logger.debug(f"Sending chunk at {datetime.now().isoformat()}")
            transcriber.send_chunk(chunk)
            logger.debug(f"Sent at {datetime.now().isoformat()}")
            time.sleep(0.1)
    text = transcriber.stop()
    logger.info(f"Transcription: {text}")
