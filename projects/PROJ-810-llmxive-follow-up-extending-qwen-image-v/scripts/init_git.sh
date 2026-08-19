#!/bin/bash
# T003b: Initialize Git Repository
# Logic: Run `git init` and verify `.git/HEAD` exists.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Initializing Git repository in: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Check if already initialized
if [ -d ".git" ]; then
    echo ".git directory already exists. Skipping init."
else
    echo "Running git init..."
    git init
fi

# Verify
if [ -f ".git/HEAD" ]; then
    echo "SUCCESS: .git/HEAD exists. Repository initialized."
else
    echo "ERROR: .git/HEAD not found. Initialization failed."
    exit 1
fi
