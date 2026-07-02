#!/bin/bash
# Script to run the Docker verification and prepare the environment for T009B
# This script ensures images are pulled before the pipeline attempts to use them.

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Running Docker verification for PROJ-515..."

# Verify images are present
python3 "$SCRIPT_DIR/verify_docker_images.py"

if [ $? -ne 0 ]; then
    echo "ERROR: Docker verification failed. Aborting."
    exit 1
fi

echo "Docker environment verified successfully."
echo "You can now run the pipeline which will invoke these containers."
