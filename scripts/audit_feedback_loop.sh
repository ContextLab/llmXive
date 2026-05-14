#!/usr/bin/env bash
# Spec 009 T077: thin wrapper around the feedback-loop auditor.

set -euo pipefail

if [ -z "${VIRTUAL_ENV:-}" ] && [ -z "${CI:-}" ]; then
  echo "WARN: no active venv. Run \`source .venv/bin/activate\` first if needed." >&2
fi

cd "$(git rev-parse --show-toplevel)"

python -m llmxive.audit.cli feedback_loop \
  --projects-dir projects \
  --since "${1:-7d}"
