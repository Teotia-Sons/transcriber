import threading
import time
from queue import Empty

from pynput import keyboard
from pynput.keyboard import Controller

from .recorder import Recorder
from .storage import upload_audio
from .transcriber import Transcriber


class Server:
    def __init__(self):
        self.keyboard = Controller()
        self._key_monitor = keyboard.Listener(
            on_press=self._on_key_press, on_release=self._on_key_release
        )
        self.transcriber = Transcriber()
        self.recorder = Recorder()

        self._listening_event = threading.Event()
        self._ctrl_l_presses: list[float] = []
        self._double_press_window = 0.5
        self.last_transcription: str = ""
        self._pressed_keys: set = set()

    def start(self):
        self._key_monitor.start()

    def stop(self):
        self._key_monitor.stop()
        if self._listening_event.is_set():
            self._cancel_recording()

    def _type_text(self, text: str):
        for char in text:
            self.keyboard.type(char)
            time.sleep(0.005)

    def _start_recording(self):
        self.audio_queue = self.recorder.start()
        self.transcriber.start()
        self._start_sender_thread()

    def _stop_recording(self):
        audio_bytes = self.recorder.stop()
        self._stop_sender_thread()
        final_text = self.transcriber.stop()
        self._type_text(final_text)
        self.last_transcription = final_text
        upload_audio(audio_bytes, final_text)

    def _cancel_recording(self):
        self.recorder.cancel()
        self._stop_sender_thread()
        self.transcriber.cancel()

    def _start_sender_thread(self):
        self._listening_event.set()
        self._sender_thread = threading.Thread(target=self._send_audio_to_transcriber)
        self._sender_thread.start()

    def _send_audio_to_transcriber(self):
        while self._listening_event.is_set():
            try:
                chunk = self.audio_queue.get(timeout=0.2)
                self.transcriber.send_chunk(chunk)
            except Empty:
                pass

    def _stop_sender_thread(self):
        self._listening_event.clear()
        self._sender_thread.join()

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
