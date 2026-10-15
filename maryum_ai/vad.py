from __future__ import annotations

import audioop

import webrtcvad


class VoiceActivityDetector:
    def __init__(self, sample_rate_hz: int = 16000, aggressiveness: int = 2):
        self.sample_rate_hz = sample_rate_hz
        self.vad = webrtcvad.Vad(max(0, min(3, aggressiveness)))

    def is_speech(self, pcm16_chunk: bytes) -> bool:
        if not pcm16_chunk:
            return False

        try:
            return self.vad.is_speech(pcm16_chunk, self.sample_rate_hz)
        except Exception:
            rms = audioop.rms(pcm16_chunk, 2)
            return rms > 400
