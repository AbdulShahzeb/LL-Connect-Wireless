#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$ROOT_DIR/venv"

if [ -f "$VENV_PATH/bin/activate" ] && [ -z "$VIRTUAL_ENV" ]; then
    source "$VENV_PATH/bin/activate"
    PYTHON_EXEC="python"
else
    PYTHON_EXEC="python3"
fi

DEV=1 python "$ROOT_DIR/src/cli.py" "$@"