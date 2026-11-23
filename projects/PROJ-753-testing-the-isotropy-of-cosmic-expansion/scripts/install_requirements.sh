#!/usr/bin/env bash
set -e
# Install the project's pinned requirements.
# This script provides an explicit execution artifact for verification.
python -m pip install -r "$(dirname "$(realpath "$0")")/../requirements.txt"