#!/usr/bin/env bash
# T044b: Generate the initial detect-secrets baseline file.
#
# This script ensures that the `detect-secrets` tool is installed,
# runs a scan of the repository root, and writes a valid
# `.secrets.baseline` JSON file. It fails loudly if any step does not
# succeed, satisfying the requirement that the baseline must exist for
# the CI security‑scan workflow.

set -euo pipefail

# Resolve the project root (two levels up from this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${PROJECT_ROOT}"

# Ensure detect-secrets is available; install it if missing.
if ! command -v detect-secrets >/dev/null 2>&1; then
    echo "detect-secrets not found; installing via pip..."
    python -m pip install --quiet detect-secrets
fi

# Verify the CLI is now accessible.
if ! command -v detect-secrets >/dev/null 2>&1; then
    echo "ERROR: detect-secrets still unavailable after install attempt." >&2
    exit 1
fi

echo "Running detect-secrets scan to generate .secrets.baseline ..."
# The scan may exit with a non‑zero code if potential secrets are found.
# We capture the exit code but continue as the baseline file is still
# written in that case.
set +e
detect-secrets scan --baseline .secrets.baseline . 
SCAN_RC=$?
set -e
echo "detect-secrets scan exit code: ${SCAN_RC}"

# Ensure the baseline file was created.
if [ ! -f .secrets.baseline ]; then
    echo "ERROR: .secrets.baseline was not created (scan exit code ${SCAN_RC})." >&2
    exit 1
fi

# Validate that the baseline is a well‑formed JSON file with expected keys.
python - <<'PY'
import json
import sys

with open(".secrets.baseline") as f:
    baseline = json.load(f)

if "results" not in baseline or "plugins_used" not in baseline:
    print("ERROR: .secrets.baseline is not a valid detect-secrets baseline.", file=sys.stderr)
    sys.exit(1)

n_files = len(baseline["results"])
n_secrets = sum(len(v) for v in baseline["results"].values())
print(f"Baseline OK: {n_files} file(s) scanned, {n_secrets} potential secret(s) recorded.")
PY

echo ".secrets.baseline generated successfully at the project root."