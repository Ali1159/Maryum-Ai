# Maryum Safety and Privacy

## Permissions model
Maryum runs as your normal user account and does **not** request or store root credentials.

Allowed automation features are limited to:
- opening installed GUI applications by executable name
- changing volume via `pactl`
- listing/searching files
- launching executable scripts from the allowlisted `MARYUM_SCRIPTS_DIR`

## Confirmation policy
The assistant blocks high-risk operations unless explicitly confirmed in the user flow:
- delete/remove actions
- package installation
- sudo/privileged operations
- shutdown/reboot
- system settings changes
- network-sensitive actions

## Audio + privacy
- microphone is always available locally when listening is active
- local voice activity detection (VAD) decides when speech is present
- only speech segments are transmitted to Gemini Live
- logs are metadata-focused and do not print API keys or full transcripts by default

## Emergency stop and revocation
- use **EMERGENCY STOP** in the GUI to immediately mute/stop and disconnect
- stop the app at any time by closing the window
- revoke access by removing/rotating `GEMINI_API_KEY`
- disable autostart: `systemctl --user disable --now maryum.service`
