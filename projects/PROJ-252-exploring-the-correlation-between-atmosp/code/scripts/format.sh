#!/usr/bin/env bash
# Script to run Black formatter on the codebase

set -e

echo "Running Black formatter..."
black code/ tests/
echo "Formatting complete."
