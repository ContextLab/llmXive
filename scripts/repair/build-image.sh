#!/usr/bin/env bash
set -euo pipefail
# Send only platform packaging files to Docker, never the research corpus or credentials.
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
tar -C "$root" --exclude='__pycache__' -cf - pyproject.toml README.md LICENSE src scripts/repair/Dockerfile | docker build -t llmxive-repair-tests:latest -f scripts/repair/Dockerfile -
