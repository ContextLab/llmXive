#!/bin/bash
#
# run_pipeline.sh
# Orchestrates the llmXive code complexity research pipeline with strict
# resource enforcement (Time and Memory limits) as per SC-005.
#
# This script:
# 1. Sets a global memory limit (7GB) using ulimit.
# 2. Executes the entire pipeline with a 6-hour timeout.
# 3. Ensures the process fails loudly if limits are exceeded.
#

set -e

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Memory limit: 7 GB in Kilobytes (7 * 1024 * 1024 = 7340032)
# This enforces the hard limit per SC-005.
MEMORY_LIMIT_KB=7340032

# Time limit: 6 hours in seconds (6 * 60 * 60 = 21600)
TIME_LIMIT_SECONDS=21600

# Project root relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ----------------------------------------------------------------------
# Environment Setup
# ----------------------------------------------------------------------
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "ERROR: Virtual environment not found at .venv"
    echo "Please run T001b to initialize the environment first."
    exit 1
fi

# ----------------------------------------------------------------------
# Global Memory Limit Enforcement (SC-005)
# ----------------------------------------------------------------------
# ulimit -v sets the maximum virtual memory address space (in KB)
# that a process can allocate. If exceeded, the OS sends SIGKILL.
echo "Enforcing memory limit: ${MEMORY_LIMIT_KB} KB (7GB)..."
ulimit -v ${MEMORY_LIMIT_KB}

# Verify the limit was set (optional, for debugging)
CURRENT_LIMIT=$(ulimit -v)
if [ "$CURRENT_LIMIT" != "unlimited" ] && [ "$CURRENT_LIMIT" -lt "$MEMORY_LIMIT_KB" ]; then
    echo "WARNING: Memory limit set to $CURRENT_LIMIT KB, expected $MEMORY_LIMIT_KB KB"
fi

# ----------------------------------------------------------------------
# Time-Limit Enforcement Wrapper
# ----------------------------------------------------------------------
echo "Enforcing time limit: ${TIME_LIMIT_SECONDS} seconds (6h)..."
echo "Starting pipeline execution..."

# The timeout command runs the pipeline script.
# If the pipeline exceeds 6 hours, timeout will kill it and return 124.
# We wrap the main pipeline logic here.
# Assuming the main logic is in code/src/main.py or similar entry point.
# Based on tasks.md, the pipeline logic is orchestrated here or via a main entry.
# We will invoke the Python entry point that drives the full flow.

# Define the main pipeline entry point
PIPELINE_ENTRY="code/src/main.py"

if [ ! -f "$PIPELINE_ENTRY" ]; then
    echo "ERROR: Pipeline entry point not found at $PIPELINE_ENTRY"
    echo "Ensure T008 (skeleton orchestration) or the main implementation is complete."
    exit 1
fi

# Execute with timeout
# We use 'timeout' to enforce the wall-clock limit.
# The ulimit above ensures the memory limit is enforced by the kernel.
timeout ${TIME_LIMIT_SECONDS} python "$PIPELINE_ENTRY"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "FATAL: Pipeline execution exceeded the time limit of ${TIME_LIMIT_SECONDS} seconds."
    echo "The process was terminated by the timeout wrapper."
    exit 124
elif [ $EXIT_CODE -ne 0 ]; then
    echo "FATAL: Pipeline execution failed with exit code $EXIT_CODE."
    echo "Check logs above for specific errors (e.g., memory limit exceeded, data fetch errors)."
    exit $EXIT_CODE
else
    echo "Pipeline execution completed successfully."
    exit 0
fi