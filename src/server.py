import io
import threading
import time
import wave

from opentelemetry import context, trace
from pynput import keyboard
from pynput.keyboard import Controller

from .recorder import FRAMES_PER_SECOND, Recorder
from .storage import save_recording
from .transcribe import transcribe


def _pcm_to_wav(pcm_bytes: bytes) -> bytes:
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(FRAMES_PER_SECOND)
        wav_file.writeframes(pcm_bytes)
    return wav_buffer.getvalue()


class Server:
    def __init__(self):
        self.keyboard = Controller()
        self._key_monitor = keyboard.Listener(
            on_press=self._on_key_press, on_release=self._on_key_release
        )
        self.recorder = Recorder()

        self._listening_event = threading.Event()
        self._ctrl_l_presses: list[float] = []
        self._double_press_window = 0.5
        self.last_transcription: str = ""
        self._pressed_keys: set = set()
        self._recording_token = None

    def start(self):
        self._key_monitor.start()

    def stop(self):
        self._key_monitor.stop()
        if self._listening_event.is_set():
            self._cancel_recording()

    def _type_text(self, text: str):
        for char in text:
            self.keyboard.type(char)
            time.sleep(0.002)

    def _start_recording(self):
        self.last_transcription = ""

        span = trace.get_tracer(__name__).start_span("recording")
        self._recording_token = context.attach(trace.set_span_in_context(span))

        self._listening_event.set()
        self.recorder.start()

    def _stop_recording(self):
        pcm_bytes = self.recorder.stop()
        self._listening_event.clear()

        wav_bytes = _pcm_to_wav(pcm_bytes)
        final_text = transcribe(wav_bytes)
        self._type_text(final_text)
        self.last_transcription = final_text

        transcription_id = save_recording(wav_bytes, final_text)

        span = trace.get_current_span()
        span.set_attribute("transcription.id", transcription_id)
        context.detach(self._recording_token)
        span.end()

        self._recording_token = None

    def _cancel_recording(self):
        self.recorder.cancel()
        self._listening_event.clear()
        context.detach(self._recording_token)
        self._recording_token = None

    def _on_key_press(self, key):
        self._pressed_keys.add(key)

        if key == keyboard.Key.ctrl_l:
            current_time = time.time()
            self._ctrl_l_presses.append(current_time)
            self._ctrl_l_presses = [
                t
                for t in self._ctrl_l_presses
                if current_time - t <= self._double_press_window
            ]

            if len(self._ctrl_l_presses) >= 2 and not self._listening_event.is_set():
                self._start_recording()
                self._ctrl_l_presses = []
            elif len(self._ctrl_l_presses) == 1 and self._listening_event.is_set():
                self._stop_recording()
                self._ctrl_l_presses = []

        elif key == keyboard.Key.esc and self._listening_event.is_set():
            self._cancel_recording()
        elif (
                key == keyboard.KeyCode.from_char("v")
                and keyboard.Key.ctrl_l in self._pressed_keys
                and keyboard.Key.cmd in self._pressed_keys
        ):
            self._type_text(self.last_transcription)

    def _on_key_release(self, key):
        self._pressed_keys.discard(key)

    def run(self):
        self.start()
        try:
            keyboard.Listener.join(self._key_monitor)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
