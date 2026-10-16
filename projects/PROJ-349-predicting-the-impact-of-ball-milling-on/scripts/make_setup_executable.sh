#!/usr/bin/env bash
# Ensure the main setup script is executable before tests run.
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
chmod +x "${SCRIPT_DIR}/setup.sh"
echo "Made ${SCRIPT_DIR}/setup.sh executable."