#!/usr/bin/env bash
# T003: Run ruff linting and black formatting checks with the shared config.
set -e
cd "$(dirname "$0")/.."
ruff check --config code/pyproject.toml code/src tests
black --config code/pyproject.toml --check code/src tests