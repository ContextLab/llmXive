#!/bin/bash
# Wrapper script to run a command with memory and time limits.
# This script attempts to use cgroups if available, otherwise falls back to ulimit.
# Usage: ./run_with_limits.sh <memory_gb> <time_limit_hours> <command> [args...]

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <memory_gb> <time_limit_hours> <command> [args...]"
    exit 1
fi

MEMORY_GB=$1
TIME_LIMIT_HOURS=$2
shift 2

COMMAND="$@"

# Calculate limits
MEMORY_KB=$((MEMORY_GB * 1024 * 1024))
TIME_LIMIT_SEC=$(echo "$TIME_LIMIT_HOURS * 3600" | bc)

echo "Running: $COMMAND"
echo "Memory Limit: ${MEMORY_GB} GB (${MEMORY_KB} KB)"
echo "Time Limit: ${TIME_LIMIT_HOURS} hours (${TIME_LIMIT_SEC} seconds)"

# Check for cgroups v2 and cgexec
if command -v cgexec &> /dev/null && [ -d /sys/fs/cgroup/memory ]; then
    echo "Using cgroups for memory limit..."
    # Create a temporary cgroup
    CGROUP_NAME="llmxive_tmp_$$"
    # Note: This assumes a cgroups v1 setup where /sys/fs/cgroup/memory exists
    # or v2 with legacy support. For pure v2, the path might differ.
    # We rely on cgexec to handle the specifics.
    
    # Run with cgexec
    timeout ${TIME_LIMIT_SEC} cgexec -g memory:llmxive_runner $COMMAND || {
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo "ERROR: Process timed out"
            exit 1
        elif [ $EXIT_CODE -eq 137 ]; then
            echo "ERROR: Process killed (likely OOM)"
            exit 1
        fi
        exit $EXIT_CODE
    }
else
    echo "cgroups not available or cgexec missing. Using ulimit and timeout."
    # Fallback to ulimit and timeout
    # ulimit -v sets virtual memory limit in KB
    ulimit -v $MEMORY_KB
    
    timeout ${TIME_LIMIT_SEC} $COMMAND || {
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 124 ]; then
            echo "ERROR: Process timed out"
            exit 1
        elif [ $EXIT_CODE -eq 137 ]; then
            echo "ERROR: Process killed (likely OOM)"
            exit 1
        fi
        exit $EXIT_CODE
    }
fi
