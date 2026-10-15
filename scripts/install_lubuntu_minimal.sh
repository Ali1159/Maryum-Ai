#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  python3 python3-venv python3-pip \
  libportaudio2 portaudio19-dev \
  python3-gi gir1.2-gtk-3.0 \
  libasound2-dev

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Install complete. Copy .env.example to .env and set GEMINI_API_KEY."
