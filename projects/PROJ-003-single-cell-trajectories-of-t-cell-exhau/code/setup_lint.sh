#!/bin/bash
# Ensure directory layout
mkdir -p logs data/results data/results/fork_points data/results/validation data/results/report
touch data/results/.gitkeep

# Install linting tools
pip install ruff black

# Run linting and capture output to logs/lint.txt
# We run these and capture exit codes to avoid 'forced' success
ruff check . > logs/lint.txt 2>&1
RUFF_STATUS=$?
black --check . >> logs/lint.txt 2>&1
BLACK_STATUS=$?

if [ $RUFF_STATUS -eq 0 ] && [ $BLACK_STATUS -eq 0 ]; then
    echo "Linting passed successfully."
    exit 0
else
    echo "Linting failed. Check logs/lint.txt for details."
    exit 1
fi
