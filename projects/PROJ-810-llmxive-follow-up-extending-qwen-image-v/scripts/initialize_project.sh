#!/bin/bash
set -e

# Project root relative to script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Initializing project structure..."

# Create directory structure
mkdir -p "$PROJECT_ROOT/code"
mkdir -p "$PROJECT_ROOT/tests"
mkdir -p "$PROJECT_ROOT/data/raw"
mkdir -p "$PROJECT_ROOT/data/interim"
mkdir -p "$PROJECT_ROOT/data/results"
mkdir -p "$PROJECT_ROOT/data/manual"
mkdir -p "$PROJECT_ROOT/data/figures"
mkdir -p "$PROJECT_ROOT/specs"
mkdir -p "$PROJECT_ROOT/code/data/cache"

echo "Directories created."

# Initialize Git if not already done
if [ ! -d "$PROJECT_ROOT/.git" ]; then
    echo "Initializing Git repository..."
    git -C "$PROJECT_ROOT" init
    echo "Git repository initialized."
else
    echo "Git repository already exists."
fi

echo "Project setup complete."