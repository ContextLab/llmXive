#!/usr/bin/env bash
# T002: install pinned dependencies and capture the CI install log.
# Writes outputs/install_log.txt (evidence that
# `pip install -r code/requirements.txt` ran without error).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p outputs

echo "=== pip install -r code/requirements.txt ===" > outputs/install_log.txt
pip install -r code/requirements.txt >> outputs/install_log.txt 2>&1
echo "=== install completed with exit code 0 ===" >> outputs/install_log.txt

# Verify every pinned package is now importable / present.
python - <<'PY' >> outputs/install_log.txt 2>&1
import importlib.metadata as md

pinned = [
    "torch", "transformers", "datasets", "pandas", "scikit-learn",
    "scipy", "statsmodels", "tqdm", "pytest", "ruff", "black",
]
for name in pinned:
    version = md.version(name)
    print(f"OK {name}=={version}")
print("All pinned dependencies verified.")
PY

echo "Install log written to outputs/install_log.txt"