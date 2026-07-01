#!/bin/bash
# setup_plan.sh
# Validates container runtime availability and disk quota (<14GB).

set -e

DISK_LIMIT_GB=14
DISK_LIMIT_KB=$((DISK_LIMIT_GB * 1024 * 1024))

echo "Checking Docker Daemon..."
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker daemon is not running or accessible."
    exit 1
fi
echo "Docker daemon is running."

echo "Checking Disk Quota..."
# Get available disk space in KB (Linux)
AVAILABLE_KB=$(df -k . | tail -1 | awk '{print $4}')

if [ "$AVAILABLE_KB" -lt "$DISK_LIMIT_KB" ]; then
    echo "Error: Disk space insufficient. Available: $((AVAILABLE_KB / 1024 / 1024))GB, Required: <${DISK_LIMIT_GB}GB free."
    exit 2
fi

echo "Disk space check passed. Available: $((AVAILABLE_KB / 1024 / 1024))GB"
exit 0