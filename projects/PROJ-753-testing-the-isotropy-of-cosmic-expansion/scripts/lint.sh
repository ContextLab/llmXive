#!/usr/bin/env bash
set -e
# Run Black in check mode (does not modify files) and then Ruff linting.
# The script exits with a non-zero status if either tool reports problems.
black --check .
ruff .
