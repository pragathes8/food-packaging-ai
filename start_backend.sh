#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
python -m pip install -r requirements.txt
python -m uvicorn app:app --reload --port 8000
