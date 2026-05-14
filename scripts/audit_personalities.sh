#!/usr/bin/env bash
# Spec 009 T025: thin wrapper around the personality auditor.
# Constitution V (Fail Fast): the underlying python CLI does the precondition
# checks; this wrapper only sets `set -euo pipefail` and dispatches.

set -euo pipefail

if [ -z "${VIRTUAL_ENV:-}" ] && [ -z "${CI:-}" ]; then
  echo "WARN: no active venv detected. Run \`source .venv/bin/activate\` first if needed." >&2
fi

cd "$(git rev-parse --show-toplevel)"

python -m llmxive.audit.cli personality \
  --personalities-dir agents/prompts/personalities \
  --feed-glob 'projects/PROJ-*/activity.jsonl' \
  "$@"
