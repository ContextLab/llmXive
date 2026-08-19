#!/bin/bash
# watchdog.sh - Monitor Docker container resource usage and kill if limits exceeded
#
# This script monitors a running Docker container and kills it if CPU or memory
# usage exceeds specified limits.
#
# Usage: ./watchdog.sh <container_id> <cpu_limit> <memory_limit_gb>
# Example: ./watchdog.sh abc123 2 7
#
# Exit codes:
#   0 - Container completed successfully or was killed due to limits
#   1 - Invalid arguments or container not found
#   2 - Monitoring error

set -e

# Configuration
CPU_LIMIT=${2:-2}
MEMORY_LIMIT_GB=${3:-7}
MEMORY_LIMIT_BYTES=$((MEMORY_LIMIT_GB * 1024 * 1024 * 1024))
CHECK_INTERVAL=5  # seconds
WARNING_THRESHOLD=0.8

# Validate arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <container_id> [cpu_limit] [memory_limit_gb]"
    exit 1
fi

CONTAINER_ID=$1

# Check if container exists
if ! docker inspect "$CONTAINER_ID" > /dev/null 2>&1; then
    echo "Error: Container '$CONTAINER_ID' not found"
    exit 1
fi

echo "Starting resource monitoring for container: $CONTAINER_ID"
echo "Limits: CPU=${CPU_LIMIT} cores, Memory=${MEMORY_LIMIT_GB}GB"
echo "Check interval: ${CHECK_INTERVAL}s"

while true; do
    # Check if container is still running
    if ! docker inspect --format='{{.State.Running}}' "$CONTAINER_ID" 2>/dev/null | grep -q "true"; then
        echo "Container has stopped. Exiting monitor."
        exit 0
    fi

    # Get container stats (non-streaming, one snapshot)
    STATS=$(docker stats --no-stream --format "{{.CPUPerc}}|{{.MemUsage}}" "$CONTAINER_ID" 2>/dev/null)
    
    if [ -z "$STATS" ]; then
        echo "Warning: Could not retrieve stats for container"
        sleep $CHECK_INTERVAL
        continue
    fi

    # Parse stats
    CPU_PERCENT=$(echo "$STATS" | cut -d'|' -f1 | sed 's/%//')
    MEM_USAGE=$(echo "$STATS" | cut -d'|' -f2 | cut -d'/' -f1)

    # Convert memory to bytes (simplified conversion)
    # Handle different units (MiB, GiB, etc.)
    MEM_VALUE=$(echo "$MEM_USAGE" | sed 's/[^0-9.]//g')
    MEM_UNIT=$(echo "$MEM_USAGE" | sed 's/[0-9.]//g')

    case "$MEM_UNIT" in
        *GiB*) MEM_BYTES=$(echo "$MEM_VALUE * 1024 * 1024 * 1024" | bc) ;;
        *MiB*) MEM_BYTES=$(echo "$MEM_VALUE * 1024 * 1024" | bc) ;;
        *KiB*) MEM_BYTES=$(echo "$MEM_VALUE * 1024" | bc) ;;
        *) MEM_BYTES=$(echo "$MEM_VALUE" | bc) ;;
    esac

    # Calculate CPU limit in percentage (assuming 100% = 1 core)
    CPU_LIMIT_PERCENT=$((CPU_LIMIT * 100))
    WARNING_CPU_LIMIT=$(echo "$CPU_LIMIT_PERCENT * $WARNING_THRESHOLD" | bc)
    WARNING_MEM_LIMIT=$(echo "$MEMORY_LIMIT_BYTES * $WARNING_THRESHOLD" | bc)

    # Log current usage
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] CPU: ${CPU_PERCENT}%, Memory: ${MEM_USAGE}"

    # Check CPU limit
    if [ $(echo "$CPU_PERCENT > $CPU_LIMIT_PERCENT" | bc) -eq 1 ]; then
        echo "CRITICAL: CPU limit exceeded (${CPU_PERCENT}% > ${CPU_LIMIT_PERCENT}%)"
        echo "Killing container due to resource limit violation."
        docker stop "$CONTAINER_ID"
        exit 0
    fi

    # Check Memory limit
    if [ "$MEM_BYTES" -gt "$MEMORY_LIMIT_BYTES" ]; then
        echo "CRITICAL: Memory limit exceeded (${MEM_USAGE} > ${MEMORY_LIMIT_GB}GB)"
        echo "Killing container due to resource limit violation."
        docker stop "$CONTAINER_ID"
        exit 0
    fi

    # Check warning thresholds
    if [ $(echo "$CPU_PERCENT > $WARNING_CPU_LIMIT" | bc) -eq 1 ]; then
        echo "WARNING: CPU usage approaching limit: ${CPU_PERCENT}% / ${CPU_LIMIT_PERCENT}%"
    fi

    if [ "$MEM_BYTES" -gt "$WARNING_MEM_LIMIT" ]; then
        echo "WARNING: Memory usage approaching limit: ${MEM_USAGE} / ${MEMORY_LIMIT_GB}GB"
    fi

    sleep $CHECK_INTERVAL
done
