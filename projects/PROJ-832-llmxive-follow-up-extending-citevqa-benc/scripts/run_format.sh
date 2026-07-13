#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CODE_DIR="$ROOT_DIR/code"

echo "🎨 Formatting code with Black..."
black "$CODE_DIR"

echo "🔧 Formatting with Ruff..."
ruff format "$CODE_DIR"

echo "✅ Formatting complete."