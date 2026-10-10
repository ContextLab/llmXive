#!/usr/bin/env bash
# Install pinned project dependencies (Constitution Principle I).
# Run-book prerequisite: quickstart.md step 2 ("pip install -r requirements.txt").
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REQ="$SCRIPT_DIR/requirements.txt"
if [ ! -f "$REQ" ]; then
  REQ="$SCRIPT_DIR/../requirements.txt"
fi
if [ ! -f "$REQ" ]; then
  echo "FATAL: no requirements.txt found under $SCRIPT_DIR" >&2
  exit 1
fi
echo "Installing dependencies from $REQ"
python -m pip install -r "$REQ"
python -c "import numpy, transformers, datasets, torch; print('deps ok:', numpy.__version__, transformers.__version__, datasets.__version__, torch.__version__)"
