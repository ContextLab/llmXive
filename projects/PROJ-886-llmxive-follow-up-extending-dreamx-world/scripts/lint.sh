#!/bin/bash
# Script to run ruff linter only (no formatting changes)

set -e

echo "Running Ruff linter (strict mode)..."
ruff check --exit-non-zero-on-fix projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
ruff check --exit-non-zero-on-fix projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

echo "Linting completed successfully."
