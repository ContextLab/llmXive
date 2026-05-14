#!/usr/bin/env bash
# Spec 009 T061: thin wrapper around the PDF auditor.

set -euo pipefail

if [ -z "${VIRTUAL_ENV:-}" ] && [ -z "${CI:-}" ]; then
  echo "WARN: no active venv. Run \`source .venv/bin/activate\` first if needed." >&2
fi

cd "$(git rev-parse --show-toplevel)"

# Fail-fast precondition checks (Constitution V) — the CLI does them too,
# but mirror them here so this wrapper exits early if tools are missing.
command -v pdftotext >/dev/null 2>&1 || { echo "FATAL: pdftotext not on PATH (install poppler)"; exit 1; }

python -m llmxive.audit.cli pdf \
  --papers-dir "${1:-docs/papers}" \
  "$@"
