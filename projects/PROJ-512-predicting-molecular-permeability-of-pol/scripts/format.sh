#!/bin/bash
set -e

echo "Running Black formatter..."
black projects/PROJ-512-predicting-molecular-permeability-of-pol/code
black projects/PROJ-512-predicting-molecular-permeability-of-pol/tests

echo "Running Ruff linter (fix mode)..."
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/code --fix
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/tests --fix

echo "Running Ruff linter (strict mode)..."
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/code
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/tests

echo "Formatting and linting complete."
