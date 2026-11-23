#!/usr/bin/env bash
#
# Pre‑commit hook / CI step to run the Reference‑Validator Agent.
# The script executes the Python citation‑validation entry point and
# exits with the same status code, causing the pipeline to fail on any
# mismatches.
#
set -euo pipefail

python - <<'PY'
import sys
from src.ci.run_citation_validation import main

# The main function returns an exit code (0 = success, non‑zero = failure).
sys.exit(main())
PY
