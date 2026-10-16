#!/usr/bin/env bash
# Linting script for the project:
#   - Checks code formatting with Black (read‑only mode)
#   - Runs Ruff static analysis
# Exits with status 0 if both checks pass, otherwise non‑zero.

set -e  # abort on any error

# Run Black in check mode
black --check .

# Run Ruff
ruff .