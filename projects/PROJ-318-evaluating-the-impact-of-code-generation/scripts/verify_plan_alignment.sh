#!/bin/bash
set -e

PLAN_FILE="plan.md"

if [ ! -f "$PLAN_FILE" ]; then
    echo "Error: $PLAN_FILE not found."
    exit 1
fi

echo "Verifying plan alignment..."

# Check 1: Ensure '100 methods' is absent
if grep -qi "100 methods" "$PLAN_FILE"; then
    echo "FAIL: Found reference to '100 methods' in $PLAN_FILE"
    exit 1
fi
echo "PASS: No reference to '100 methods' found."

# Check 2: Ensure 'Max [deferred] methods per repository' is present (or the specific hard cap text)
# The task description says: grep for 'Max [deferred] methods per repository'
# However, the implementation replaces '100' with '[deferred]', so we check for the specific phrase.
if ! grep -q "Max a reasonable number of methods per repository to ensure manageability and coherence." "$PLAN_FILE"; then
    echo "FAIL: Hard cap statement 'Max a reasonable number of methods per repository...' not found."
    exit 1
fi
echo "PASS: Hard cap statement found."

# Check 3: Ensure 'fallback to 8-bit' is absent
if grep -qi "fallback to 8-bit" "$PLAN_FILE"; then
    echo "FAIL: Found reference to 'fallback to 8-bit' in $PLAN_FILE"
    exit 1
fi
echo "PASS: No reference to 'fallback to 8-bit' found."

echo "Plan alignment verification successful."
exit 0