#!/usr/bin/env bash
# T044b: Generate the initial detect-secrets baseline file.
#
# Runs `detect-secrets scan --baseline .secrets.baseline` from the project
# root so that the CI security-scan job (T044a) has a baseline to audit
# against. The script fails loudly (set -e) if detect-secrets is missing,
# the scan fails, or the resulting baseline file is invalid JSON.
set -euo pipefail

# Resolve the project root (three levels above this script) so the
# baseline lands at the repository root regardless of the caller's cwd.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../" && pwd)"
cd "${PROJECT_ROOT}"

# Ensure detect-secrets is available (it is also in requirements.txt).
if ! command -v detect-secrets >/dev/null 2>&1; then
    echo "detect-secrets not found on PATH; installing..."
    python -m pip install --quiet detect-secrets
fi

echo "Running detect-secrets scan to generate .secrets.baseline ..."
detect-secrets scan --baseline .secrets.baseline

# Validate the baseline is a real, well-formed detect-secrets baseline.
if [ ! -f .secrets.baseline ]; then
    echo "ERROR: .secrets.baseline was not created." >&2
    exit 1
fi

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
print(f"Baseline OK: {n_files} file(s) scanned, {n_secrets} potential secret(s) recorded for audit.")
PY

echo ".secrets.baseline generated successfully at the project root."
