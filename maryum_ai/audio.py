from __future__ import annotations

import queue
from collections.abc import Callable

import sounddevice as sd


class AudioIO:
    def __init__(self, mic_rate: int = 16000, speaker_rate: int = 24000):
        self.mic_rate = mic_rate
        self.speaker_rate = speaker_rate
        self._mic_stream: sd.RawInputStream | None = None
        self._speaker_stream: sd.RawOutputStream | None = None
        self._muted = False
        self._speaker_queue: queue.Queue[bytes] = queue.Queue(maxsize=100)

    def start(
        self,
        mic_callback: Callable[[bytes], None],
    ) -> None:
        def _on_mic(indata, frames, _time, status):
            if status:
                return
            if not self._muted:
                mic_callback(bytes(indata))

        def _on_speaker(outdata, frames, _time, status):
            if status:
                outdata[:] = b"\x00" * len(outdata)
                return
            try:
                chunk = self._speaker_queue.get_nowait()
            except queue.Empty:
                chunk = b"\x00" * len(outdata)

            if len(chunk) < len(outdata):
                chunk += b"\x00" * (len(outdata) - len(chunk))
            outdata[:] = chunk[: len(outdata)]

        self._mic_stream = sd.RawInputStream(
            samplerate=self.mic_rate,
            blocksize=480,
            dtype="int16",
            channels=1,
            callback=_on_mic,
        )
        self._speaker_stream = sd.RawOutputStream(
            samplerate=self.speaker_rate,
            blocksize=960,
            dtype="int16",
            channels=1,
            callback=_on_speaker,
        )
        self._mic_stream.start()
        self._speaker_stream.start()

    def play(self, pcm16_chunk: bytes) -> None:
        try:
            self._speaker_queue.put_nowait(pcm16_chunk)
        except queue.Full:
            pass

    def set_muted(self, muted: bool) -> None:
        self._muted = muted

    def stop(self) -> None:
        if self._mic_stream:
            self._mic_stream.stop()
            self._mic_stream.close()
            self._mic_stream = None
        if self._speaker_stream:
            self._speaker_stream.stop()
            self._speaker_stream.close()
            self._speaker_stream = None
        while not self._speaker_queue.empty():
            self._speaker_queue.get_nowait()
