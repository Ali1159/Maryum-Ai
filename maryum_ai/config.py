from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(slots=True)
class MaryumConfig:
    gemini_api_key: str
    model: str = "gemini-live-2.5-flash-preview"
    system_prompt: str = (
        "You are Maryum, a warm and helpful desktop voice assistant. Be kind, concise, "
        "supportive, and respectful. Never manipulate the user, and refuse unsafe requests. "
        "For sensitive, destructive, privileged, or network-sensitive operations, request "
        "explicit confirmation through the app before proceeding."
    )
    mic_sample_rate_hz: int = 16000
    speaker_sample_rate_hz: int = 24000
    vad_aggressiveness: int = 2
    scripts_allowlist_dir: str = "~/maryum-scripts"


class ConfigError(RuntimeError):
    pass


def load_config() -> MaryumConfig:
    dotenv_path = os.environ.get("MARYUM_ENV_FILE", ".env")
    load_dotenv(dotenv_path=dotenv_path, override=False)

    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "Missing GEMINI_API_KEY. Set it in your environment or in a .env file."
        )

    return MaryumConfig(
        gemini_api_key=key,
        model=os.environ.get("MARYUM_GEMINI_MODEL", "gemini-live-2.5-flash-preview"),
        system_prompt=os.environ.get("MARYUM_SYSTEM_PROMPT", MaryumConfig.system_prompt),
        vad_aggressiveness=int(os.environ.get("MARYUM_VAD_AGGRESSIVENESS", "2")),
        scripts_allowlist_dir=os.path.expanduser(
            os.environ.get("MARYUM_SCRIPTS_DIR", "~/maryum-scripts")
        ),
    )


def ensure_scripts_dir(path: str) -> Path:
    scripts_dir = Path(path).expanduser()
    scripts_dir.mkdir(parents=True, exist_ok=True)
    return scripts_dir
