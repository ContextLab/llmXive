#!/usr/bin/env bash
# T002b: Set up the Python virtual environment and install requirements.
# Creates ./venv at the project root, installs the pinned dependencies from
# requirements.txt, runs `pip check`, and writes an installation log to
# data/logs/venv_setup.json as verifiable evidence.
set -euo pipefail

cd "$(dirname "$0")/.."

# Locate the requirements manifest (prefer code/requirements.txt per quickstart).
REQ=""
for f in code/requirements.txt requirements.txt; do
  if [ -f "$f" ]; then
    REQ="$f"
    break
  fi
done
if [ -z "$REQ" ]; then
  echo "ERROR: no requirements.txt found (looked for code/requirements.txt, requirements.txt)" >&2
  exit 1
fi
echo "Using requirements manifest: $REQ"

# Create the virtual environment.
if [ ! -d venv ]; then
  python3 -m venv venv
fi
PY="./venv/bin/python"

# Upgrade pip first so pinned-version resolution works reliably.
"$PY" -m pip install --upgrade pip

# Install the pinned dependencies (fail loudly on any error).
"$PY" -m pip install -r "$REQ"

# Verify dependency consistency.
"$PY" -m pip check

# Write verifiable installation evidence.
mkdir -p data/logs
"$PY" - "$REQ" <<'EOF'
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

req_path = sys.argv[1]
freeze = subprocess.run(
    ["./venv/bin/pip", "freeze"], capture_output=True, text=True, check=True
).stdout.strip().splitlines()

log = {
    "task_id": "T002b",
    "status": "success",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "python_executable": str(Path("./venv/bin/python").resolve()),
    "python_version": sys.version.split()[0],
    "requirements_manifest": req_path,
    "installed_packages": freeze,
    "package_count": len(freeze),
}
out = Path("data/logs/venv_setup.json")
out.write_text(json.dumps(log, indent=2) + "\n")
print(f"Wrote installation log to {out} ({len(freeze)} packages installed)")
EOF

echo "Virtual environment setup complete."
echo "Activate with: source venv/bin/activate"