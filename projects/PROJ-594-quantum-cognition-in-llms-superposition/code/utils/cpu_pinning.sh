#!/bin/bash
#
# CPU Pinning Wrapper Script
# Satisfies SC-004: Ensures deterministic execution by pinning processes to CPU core 0.
#
# Usage:
#   ./cpu_pinning.sh <python_script.py> [args...]
#
# Example:
#   ./cpu_pinning.sh python code/experiments/run_baseline.py --seed 42
#

set -e

if [ $# -eq 0 ]; then
    echo "Error: No command provided." >&2
    echo "Usage: $0 <command> [args...]" >&2
    exit 1
fi

# Pin the entire process group to CPU list 0 to ensure deterministic behavior
# and satisfy SC-004 constraints for reproducible research on CI.
# We use 'taskset' which is standard on most Linux-based CI environments.

echo "Pinning process to CPU core 0..."

exec taskset --cpu-list 0 "$@"