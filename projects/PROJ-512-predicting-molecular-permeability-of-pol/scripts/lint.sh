#!/bin/bash
set -e

echo "Running Ruff linter (check only, no fixes)..."
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/code
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/tests

echo "Linting complete."
