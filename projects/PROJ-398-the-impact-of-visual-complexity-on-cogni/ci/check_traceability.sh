#!/bin/bash
#
# ci/check_traceability.sh
#
# Verifies that docs/traceability.md lists all infrastructure tasks defined in tasks.md.
# Infrastructure tasks are those in Phase 1 (Setup) and Phase 2 (Foundational).
#
# Exit codes:
#   0 - All infrastructure tasks are listed in the traceability report
#   1 - Missing infrastructure tasks or file not found
#

set -e

TRACEABILITY_FILE="docs/traceability.md"
TASKS_FILE="tasks.md"

# Check if traceability file exists
if [ ! -f "$TRACEABILITY_FILE" ]; then
    echo "ERROR: $TRACEABILITY_FILE not found."
    echo "Please run T001c to generate the traceability document first."
    exit 1
fi

# Check if tasks.md exists
if [ ! -f "$TASKS_FILE" ]; then
    echo "ERROR: $TASKS_FILE not found."
    exit 1
fi

# Define the set of infrastructure tasks based on Phase 1 and Phase 2
# From tasks.md:
# Phase 1: T001a, T001b, T002, T001c, T003, T004, T005, T006, T006a, T007, T060
# Phase 2: T008, T009 (Note: T008 is the current task, T009 is the next)
# We check for the tasks that should be documented as "completed" or "in progress"
# The list of infrastructure tasks to verify presence:
INFRA_TASKS=(
    "T001a"
    "T001b"
    "T002"
    "T001c"
    "T003"
    "T004"
    "T005"
    "T006"
    "T006a"
    "T007"
    "T060"
    "T008"
    "T009"
)

MISSING_TASKS=()
FOUND_COUNT=0

echo "Checking traceability for infrastructure tasks..."

for task in "${INFRA_TASKS[@]}"; do
    # Check if the task ID appears in the traceability file
    # We look for the task ID as a distinct token (e.g., "T001a" not "T001a0")
    if grep -q "\b${task}\b" "$TRACEABILITY_FILE"; then
        echo "  [OK] $task found in $TRACEABILITY_FILE"
        ((FOUND_COUNT++))
    else
        echo "  [MISSING] $task NOT found in $TRACEABILITY_FILE"
        MISSING_TASKS+=("$task")
    fi
done

TOTAL_INFRA=${#INFRA_TASKS[@]}

echo ""
echo "Summary: $FOUND_COUNT / $TOTAL_INFRA infrastructure tasks found."

if [ ${#MISSING_TASKS[@]} -gt 0 ]; then
    echo ""
    echo "ERROR: The following infrastructure tasks are missing from $TRACEABILITY_FILE:"
    for missing in "${MISSING_TASKS[@]}"; do
        echo "  - $missing"
    done
    echo ""
    echo "Please update docs/traceability.md to include all infrastructure tasks."
    exit 1
fi

echo "SUCCESS: All infrastructure tasks are listed in $TRACEABILITY_FILE."
exit 0
