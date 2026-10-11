#!/usr/bin/env bash
# T002-B: Install pinned dependencies and record evidence of the installation.
# Runs pip install against code/requirements.txt in the active environment,
# then saves the full pip install log and a pip freeze snapshot as evidence.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

if [ ! -f "$REQ_FILE" ]; then
    echo "ERROR: requirements file not found at $REQ_FILE" >&2
    exit 1
fi

# Evidence directory (project-owned)
EVIDENCE_DIR="$PROJ_DIR/data/processed"
mkdir -p "$EVIDENCE_DIR"

echo "=== T002-B: installing pinned dependencies from $REQ_FILE ==="
python -m pip install --upgrade pip >> "$EVIDENCE_DIR/pip_install_log.txt" 2>&1 || \
    python -m pip install -r "$REQ_FILE" >> "$EVIDENCE_DIR/pip_install_log.txt" 2>&1
# Main install (recorded)
python -m pip install -r "$REQ_FILE" 2>&1 | tee "$EVIDENCE_DIR/pip_install_log.txt"

echo "=== T002-B: recording pip freeze snapshot ==="
python -m pip freeze > "$EVIDENCE_DIR/installed_versions.txt"

# Verify each pinned package is importable at the pinned version
python - "$REQ_FILE" <<'PYEOF'
import sys
from importlib.metadata import version, PackageNotFoundError

req_path = sys.argv[1]
failures = []
with open(req_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, pinned = line.partition("==")
        try:
            installed = version(name)
        except PackageNotFoundError:
            failures.append(f"{name}: NOT INSTALLED (pinned {pinned})")
            continue
        if installed != pinned:
            failures.append(f"{name}: installed {installed} != pinned {pinned}")

if failures:
    for msg in failures:
        print("VERSION MISMATCH:", msg, file=sys.stderr)
    sys.exit(1)
print("All pinned dependencies verified installed at their pinned versions.")
PYEOF

echo "=== T002-B: installation evidence written to $EVIDENCE_DIR ==="
echo "  - pip_install_log.txt (full pip install output)"
echo "  - installed_versions.txt (pip freeze snapshot)"
