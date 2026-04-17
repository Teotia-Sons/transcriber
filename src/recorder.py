import sys
import threading
from queue import Queue
from typing import Optional, Union

from loguru import logger
from pyaudio import PyAudio, paInt16

FRAMES_PER_SECOND = 16000
AUDIO_FORMAT = paInt16
BYTES_PER_FRAME = 2

SENTINEL = object()


class Recorder:
    def __init__(self):
        self._record_thread: threading.Thread | None = None
        self._listening_event = threading.Event()
        self._stream = None
        self._audio_queue: Optional[Queue[Union[bytes, object]]] = None
        self._frames: list[bytes] = []

    def start(self) -> Queue[Union[bytes, object]]:
        assert not self._listening_event.is_set()

        self._stream = PyAudio().open(
            format=AUDIO_FORMAT,
            channels=1,
            rate=FRAMES_PER_SECOND,
            input=True,
            frames_per_buffer=FRAMES_PER_SECOND // 100,  # 10ms for macOS
        )

        queue: Queue[bytes] = Queue()
        self._audio_queue = queue
        self._frames = []

        self._listening_event.set()
        thread = threading.Thread(target=self._record)
        thread.start()
        self._record_thread = thread
        logger.debug("Recording started")

        return queue

    def _record(self):
        queue = self._audio_queue
        assert queue is not None

        while self._listening_event.is_set():
            data = self._stream.read(FRAMES_PER_SECOND)
            self._frames.append(data)
            queue.put(data)

    def stop(self) -> bytes:
        self._stop_recording()
        return b"".join(self._frames)

    def cancel(self) -> None:
        logger.debug("Recording cancelled")
        self._stop_recording()

    def _stop_recording(self):
        assert self._listening_event.is_set()
        self._listening_event.clear()

        record_thread = self._record_thread
        assert record_thread is not None
        record_thread.join()

        self._stream.stop_stream()
        self._stream.close()
        self._audio_queue.put(SENTINEL)
        logger.debug("Recording stopped")


if __name__ == "__main__":
    import time

    if len(sys.argv) < 2:
        logger.error("Usage: python -m src.recorder <filepath>")
        logger.error("Example: python -m src.recorder test.pcm")
        sys.exit(1)

    recorder = Recorder()
    recorder.start()
    logger.info(f"Recording for 3 seconds")
    time.sleep(3)
    pcm_bytes = recorder.stop()
    with open(sys.argv[1], "wb") as f:
        f.write(pcm_bytes)
    logger.info(f"Saved recording to {sys.argv[1]}")
