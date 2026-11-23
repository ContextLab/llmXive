#!/bin/bash
# verify_resources.sh - Validate resource constraints for baseline training
#
# This script parses the output of `/usr/bin/time -v` and `taskset -c 0-3`
# to verify that:
# 1. CPU pinning is active (process is bound to cores 0-3)
# 2. RSS memory usage is strictly less than 7GB (7168 MB)
#
# Usage:
#   ./scripts/verify_resources.sh <time_output_file> <taskset_output_file>
#
# Exit codes:
#   0 - All constraints satisfied
#   1 - Constraint violation (memory or CPU pinning)
#   2 - Missing arguments or file read errors

set -e

# Configuration
MAX_MEMORY_MB=7168  # 7 GB in MB
REQUIRED_CORES="0-3"

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Error: Two arguments required."
    echo "Usage: $0 <time_output_file> <taskset_output_file>"
    exit 2
fi

TIME_OUTPUT_FILE="$1"
TASKSET_OUTPUT_FILE="$2"

# Verify input files exist
if [ ! -f "$TIME_OUTPUT_FILE" ]; then
    echo "Error: Time output file not found: $TIME_OUTPUT_FILE"
    exit 2
fi

if [ ! -f "$TASKSET_OUTPUT_FILE" ]; then
    echo "Error: Taskset output file not found: $TASKSET_OUTPUT_FILE"
    exit 2
fi

echo "=== Resource Verification ==="
echo "Max Memory Limit: ${MAX_MEMORY_MB} MB"
echo "Required CPU Pinning: Cores ${REQUIRED_CORES}"
echo ""

# 1. Verify CPU Pinning
echo "Checking CPU Pinning..."
# taskset -c output usually looks like: "current affinity list: 0-3" or "0-3"
# We grep for the pattern matching the required cores.
if grep -qE "^[0-9]+-[0-9]+$" "$TASKSET_OUTPUT_FILE" || grep -qE "affinity.*[0-9]+-[0-9]+" "$TASKSET_OUTPUT_FILE"; then
    # Extract the core range found
    FOUND_CORES=$(grep -oE "[0-9]+-[0-9]+" "$TASKSET_OUTPUT_FILE" | head -n 1)
    if [ "$FOUND_CORES" == "$REQUIRED_CORES" ]; then
        echo "✓ CPU Pinning Verified: Process bound to cores $FOUND_CORES"
    else
        echo "✗ CPU Pinning Violation: Expected cores $REQUIRED_CORES, found $FOUND_CORES"
        exit 1
    fi
else
    echo "✗ CPU Pinning Violation: Could not confirm binding to cores $REQUIRED_CORES"
    echo "Taskset output content:"
    cat "$TASKSET_OUTPUT_FILE"
    exit 1
fi

# 2. Verify Memory Usage (RSS)
echo "Checking Memory Usage..."
# /usr/bin/time -v output line: "Maximum resident set size (kbytes): 123456"
RSS_KB=$(grep -E "Maximum resident set size \(kbytes\):" "$TIME_OUTPUT_FILE" | awk '{print $NF}')

if [ -z "$RSS_KB" ]; then
    echo "✗ Memory Violation: Could not parse RSS from time output."
    echo "Time output content:"
    cat "$TIME_OUTPUT_FILE"
    exit 1
fi

# Convert KB to MB
RSS_MB=$((RSS_KB / 1024))

echo "  RSS Usage: ${RSS_MB} MB (Limit: ${MAX_MEMORY_MB} MB)"

if [ "$RSS_MB" -lt "$MAX_MEMORY_MB" ]; then
    echo "✓ Memory Constraint Satisfied: ${RSS_MB} MB < ${MAX_MEMORY_MB} MB"
else
    echo "✗ Memory Constraint Violated: ${RSS_MB} MB >= ${MAX_MEMORY_MB} MB"
    exit 1
fi

echo ""
echo "=== All Resource Constraints Verified ==="
exit 0