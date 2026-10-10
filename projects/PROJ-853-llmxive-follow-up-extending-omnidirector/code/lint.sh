#!/usr/bin/env bash
set -e
# Run ruff linting
ruff check .
# Run black formatting check
black --check .