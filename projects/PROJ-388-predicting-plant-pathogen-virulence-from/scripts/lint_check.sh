#!/bin/bash
set -e

echo "Running linter check (ruff)..."
ruff check code/ src/ tests/

echo "Lint check passed."