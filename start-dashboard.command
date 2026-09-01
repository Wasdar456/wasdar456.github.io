#!/bin/zsh

set -e
SCRIPT_DIR="${0:A:h}"
cd "$SCRIPT_DIR"

if [[ -x ".venv/bin/python" ]]; then
  exec .venv/bin/python scripts/control_panel.py
fi

exec python3 scripts/control_panel.py
