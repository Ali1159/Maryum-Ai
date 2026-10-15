# Maryum-Ai

Maryum is a lightweight Linux desktop voice assistant for Ubuntu/Lubuntu Minimal using Python, GTK, and Gemini Live audio.

## Features (MVP)
- Lightweight GTK status window for Lubuntu Minimal
- Always-listening local microphone mode with voice activity detection (VAD)
- Bidirectional Gemini Live audio client using `GEMINI_API_KEY`
- Visible status indicator: disconnected / listening / transmitting / muted / error
- Controls: start listening, mute mic, disconnect, emergency stop
- Safe Linux automation layer with allowlisted tools and blocked risky actions
- Optional `systemd --user` autostart unit

## Safety model (important)
Maryum **does not** provide unrestricted machine control.

Allowed automation tools:
- open applications
- set volume
- list/search files
- run user-approved scripts from an allowlisted directory

Risky actions are blocked unless explicit confirmation is added in user flow:
- deletion/removal
- package install
- `sudo` operations
- shutdown/reboot
- system settings changes
- network-sensitive actions

See: [`docs/SAFETY.md`](docs/SAFETY.md)

## Requirements
- Ubuntu/Lubuntu Minimal
- Python 3.10+
- Audio stack (PortAudio / ALSA / PulseAudio/PipeWire)

## Install (Lubuntu Minimal)
From repository root:

```bash
./scripts/install_lubuntu_minimal.sh
cp .env.example .env
nano .env  # set GEMINI_API_KEY
```

## Configuration
Environment variables (in shell or `.env`):

- `GEMINI_API_KEY` (**required**)
- `MARYUM_GEMINI_MODEL` (default: `gemini-live-2.5-flash-preview`)
- `MARYUM_SYSTEM_PROMPT` (warm, helpful Maryum personality)
- `MARYUM_VAD_AGGRESSIVENESS` (0-3, default 2)
- `MARYUM_SCRIPTS_DIR` (default `~/maryum-scripts`)

## Run
```bash
source .venv/bin/activate
python -m maryum_ai.main
```

## Tests
Tests avoid hardware and live Gemini key usage.

```bash
pytest
```

## systemd user autostart (optional)
```bash
mkdir -p ~/.config/systemd/user
cp systemd/maryum.service ~/.config/systemd/user/maryum.service
systemctl --user daemon-reload
systemctl --user enable --now maryum.service
```

Disable:
```bash
systemctl --user disable --now maryum.service
```

## Project structure
- `maryum_ai/config.py` - env/config loading
- `maryum_ai/gemini_live.py` - Gemini Live audio client
- `maryum_ai/audio.py` - microphone capture + speaker playback
- `maryum_ai/vad.py` - local speech detection
- `maryum_ai/controller.py` - app lifecycle/reconnect/state machine
- `maryum_ai/safety.py` - allowlist + confirmation policy
- `maryum_ai/tools.py` - safe automation execution layer
- `maryum_ai/gui.py` - GTK UI
- `docs/SAFETY.md` - permission/privacy/safety details
