#!/usr/bin/env bash
set -euo pipefail

# Task: T009 - Verify Spec Alignment Report Existence
# Description: Asserts that docs/spec_alignment_report.md exists.
# Fails the build if the file is missing or empty.

REPORT_PATH="docs/spec_alignment_report.md"

if [ ! -f "$REPORT_PATH" ]; then
    echo "ERROR: Spec alignment report not found at $REPORT_PATH"
    echo "Please ensure task T000/T000a has been completed and the report generated."
    exit 1
fi

if [ ! -s "$REPORT_PATH" ]; then
    echo "ERROR: Spec alignment report at $REPORT_PATH is empty."
    exit 1
fi

echo "SUCCESS: Spec alignment report exists and is non-empty."
exit 0
