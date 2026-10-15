from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from google import genai
from google.genai import types

from .config import MaryumConfig


class GeminiLiveClient:
    def __init__(self, config: MaryumConfig):
        self.config = config
        self._client = genai.Client(api_key=config.gemini_api_key)
        self._session: Any | None = None
        self._session_cm: Any | None = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        async with self._lock:
            if self._session is not None:
                return

            self._session_cm = self._client.aio.live.connect(
                model=self.config.model,
                config=types.LiveConnectConfig(
                    response_modalities=["AUDIO"],
                    system_instruction=self.config.system_prompt,
                ),
            )
            self._session = await self._session_cm.__aenter__()

    async def disconnect(self) -> None:
        async with self._lock:
            if self._session_cm is None:
                self._session = None
                return

            await self._session_cm.__aexit__(None, None, None)
            self._session = None
            self._session_cm = None

    async def send_audio(self, pcm16_chunk: bytes) -> None:
        if not self._session:
            return

        blob = types.Blob(data=pcm16_chunk, mime_type="audio/pcm;rate=16000")
        await self._session.send_realtime_input(audio=blob)

    async def receive_audio(self) -> AsyncIterator[bytes]:
        if not self._session:
            return

        async for message in self._session.receive():
            server_content = getattr(message, "server_content", None)
            if not server_content or not getattr(server_content, "model_turn", None):
                continue
            parts = getattr(server_content.model_turn, "parts", [])
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    yield inline_data.data
