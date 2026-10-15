from __future__ import annotations

import asyncio
import logging
import threading
from collections.abc import Callable
from enum import Enum

from .audio import AudioIO
from .config import MaryumConfig
from .gemini_live import GeminiLiveClient
from .vad import VoiceActivityDetector

logger = logging.getLogger(__name__)


class AssistantState(str, Enum):
    DISCONNECTED = "disconnected"
    LISTENING = "listening"
    TRANSMITTING = "transmitting"
    MUTED = "muted"
    ERROR = "error"


class MaryumController:
    def __init__(self, config: MaryumConfig, on_state: Callable[[AssistantState], None]):
        self.config = config
        self.on_state = on_state
        self.audio = AudioIO(config.mic_sample_rate_hz, config.speaker_sample_rate_hz)
        self.vad = VoiceActivityDetector(config.mic_sample_rate_hz, config.vad_aggressiveness)
        self.gemini = GeminiLiveClient(config)

        self.state = AssistantState.DISCONNECTED
        self._muted = False
        self._running = False
        self._loop = asyncio.new_event_loop()
        self._thread: threading.Thread | None = None
        self._queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=200)

    def _set_state(self, state: AssistantState) -> None:
        self.state = state
        self.on_state(state)

    def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._start_async())
        self._loop.run_forever()

    async def _start_async(self) -> None:
        try:
            await self.gemini.connect()
            self.audio.start(self._on_mic_chunk)
            self._set_state(AssistantState.LISTENING)
            self._loop.create_task(self._send_audio_loop())
            self._loop.create_task(self._receive_audio_loop())
        except Exception as exc:
            logger.exception("Failed to start: %s", exc)
            self._set_state(AssistantState.ERROR)

    def _on_mic_chunk(self, chunk: bytes) -> None:
        if not self._running or self._muted:
            return
        if self.vad.is_speech(chunk):
            self._set_state(AssistantState.TRANSMITTING)
            self._loop.call_soon_threadsafe(self._enqueue_chunk, chunk)
        elif self.state != AssistantState.MUTED:
            self._set_state(AssistantState.LISTENING)

    def _enqueue_chunk(self, chunk: bytes) -> None:
        if self._queue.full():
            return
        self._queue.put_nowait(chunk)

    async def _send_audio_loop(self) -> None:
        while self._running:
            chunk = await self._queue.get()
            try:
                await self.gemini.send_audio(chunk)
            except Exception as exc:
                logger.warning("send_audio failed, reconnecting: %s", exc)
                await self._try_reconnect()

    async def _receive_audio_loop(self) -> None:
        while self._running:
            try:
                async for chunk in self.gemini.receive_audio():
                    self.audio.play(chunk)
                    if self.state != AssistantState.MUTED:
                        self._set_state(AssistantState.LISTENING)
            except Exception as exc:
                logger.warning("receive_audio failed, reconnecting: %s", exc)
                await self._try_reconnect()

    async def _try_reconnect(self) -> None:
        if not self._running:
            return
        self._set_state(AssistantState.ERROR)
        await self.gemini.disconnect()
        await asyncio.sleep(1.0)
        await self.gemini.connect()
        if self._muted:
            self._set_state(AssistantState.MUTED)
        else:
            self._set_state(AssistantState.LISTENING)

    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        self.audio.set_muted(muted)
        self._set_state(AssistantState.MUTED if muted else AssistantState.LISTENING)

    def stop(self) -> None:
        if not self._running:
            return

        self._running = False

        def _stop_async() -> None:
            self.audio.stop()
            self._loop.create_task(self.gemini.disconnect())
            self._set_state(AssistantState.DISCONNECTED)
            self._loop.call_later(0.1, self._loop.stop)

        self._loop.call_soon_threadsafe(_stop_async)
        if self._thread:
            self._thread.join(timeout=2)

    def emergency_stop(self) -> None:
        self.set_muted(True)
        self.stop()
