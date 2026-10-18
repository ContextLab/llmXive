#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Linting helper for the project.
#
# This script runs ``ruff`` and ``black`` on the repository, writes the
# combined output to ``logs/lint.txt`` and exits with a non‑zero status
# if any tool reports a problem.
# ----------------------------------------------------------------------

set -e

# Ensure the logs directory exists.
mkdir -p logs

# Run ruff.
if ! ruff_output=$(ruff check . 2>&1); then
    echo "$ruff_output" > logs/lint.txt
    echo "Ruff reported errors – exiting with status 1."
    exit 1
fi

# Run black in check mode.
if ! black_output=$(black --check . 2>&1); then
    {
        echo "$ruff_output"
        echo "$black_output"
    } > logs/lint.txt
    echo "Black reported formatting issues – exiting with status 1."
    exit 1
fi

# If both tools succeeded, combine their (empty) output.
{
    echo "$ruff_output"
    echo "$black_output"
} > logs/lint.txt

echo "Linting passed – logs written to logs/lint.txt."
