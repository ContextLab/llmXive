#!/bin/bash
# Setup script for linting and formatting tools
# This script installs pre-commit hooks and verifies tool availability

set -e

echo "🔧 Setting up linting and formatting tools for llmXive..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install -r requirements.txt

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip install pre-commit
fi

# Initialize pre-commit hooks
echo "🔗 Installing git hooks..."
pre-commit install

# Verify tools are available
echo "✅ Verifying tool installation..."
ruff --version
black --version
pre-commit --version

echo "🎉 Setup complete! Run 'pre-commit run --all-files' to check all files."
echo "💡 Tip: Add 'pre-commit run' to your CI/CD pipeline for automated checks."
