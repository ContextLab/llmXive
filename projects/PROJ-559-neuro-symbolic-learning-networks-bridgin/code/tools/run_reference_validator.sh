#!/usr/bin/env bash
set -e
python - <<'PY'
import subprocess, sys, pathlib
script = pathlib.Path("code/tools/reference_validator.py")
result = subprocess.run([sys.executable, str(script), "--threshold", "0.8"], check=False)
sys.exit(result.returncode)
PY