#!/usr/bin/env bash
set -euo pipefail

# This script configures the linting and formatting tools (Ruff and Black)
# for the llmXive project. It installs the tools if missing and verifies
# configuration files exist.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CODE_DIR="$ROOT_DIR/code"

echo "🔧 Setting up linting and formatting tools..."

# Check if tools are installed
if ! command -v ruff &> /dev/null; then
    echo "⚠️  Ruff not found. Installing..."
    pip install ruff
else
    echo "✅ Ruff is installed."
fi

if ! command -v black &> /dev/null; then
    echo "⚠️  Black not found. Installing..."
    pip install black
else
    echo "✅ Black is installed."
fi

# Verify config files exist
if [ ! -f "$CODE_DIR/.ruff.toml" ]; then
    echo "❌ Error: $CODE_DIR/.ruff.toml not found."
    exit 1
fi

if [ ! -f "$CODE_DIR/.black.toml" ]; then
    echo "❌ Error: $CODE_DIR/.black.toml not found."
    exit 1
fi

echo "✅ Configuration files verified."
echo "🚀 You can now run:"
echo "   ruff check code/"
echo "   ruff format code/"
echo "   black code/"
