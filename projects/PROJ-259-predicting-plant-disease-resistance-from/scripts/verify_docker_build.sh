#!/bin/bash
# T058: Docker build verification task
# This script verifies that the Docker container builds successfully,
# starts correctly, mounts the data directory, and executes `code/main.py --dry-run`
# without errors.

set -e  # Exit immediately if a command exits with a non-zero status

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_IMAGE_NAME="plant-disease-pipeline:latest"
DOCKER_CONTAINER_NAME="pipeline-verify-$(date +%s)"

echo "=== T058: Docker Build Verification ==="
echo "Project Root: $PROJECT_ROOT"
echo "Image Name: $DOCKER_IMAGE_NAME"
echo "Container Name: $DOCKER_CONTAINER_NAME"
echo ""

# Step 1: Build the Docker image
echo "Step 1: Building Docker image..."
docker build -t "$DOCKER_IMAGE_NAME" -f "$PROJECT_ROOT/Dockerfile" "$PROJECT_ROOT"
if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed."
    exit 1
fi
echo "Docker image built successfully."
echo ""

# Step 2: Run the container with --dry-run
echo "Step 2: Running container with --dry-run..."
# Mount the data directory to ensure the container can access data
# The container expects data at /app/data
docker run --rm --name "$DOCKER_CONTAINER_NAME" \
    -v "$PROJECT_ROOT/data:/app/data" \
    -v "$PROJECT_ROOT/artifacts:/app/artifacts" \
    -v "$PROJECT_ROOT/code:/app/code" \
    -v "$PROJECT_ROOT/tests:/app/tests" \
    -v "$PROJECT_ROOT/specs:/app/specs" \
    "$DOCKER_IMAGE_NAME" \
    python code/main.py --dry-run

if [ $? -ne 0 ]; then
    echo "ERROR: Container execution failed."
    exit 1
fi

echo ""
echo "=== T058: Verification Complete ==="
echo "Docker build and --dry-run execution succeeded."
echo "The container starts, mounts data, and executes main.py --dry-run without errors."