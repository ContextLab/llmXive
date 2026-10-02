#!/bin/bash
# Integration test for build script `build.sh` success
# Task: T013 [US1]
# Verification: Run `bash tests/integration/test_build.sh` and verify it calls `build.sh` and checks for binary existence.

set -e
set -u
set -o pipefail

# Project root relative to script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CODE_SCRIPTS_DIR="$PROJECT_ROOT/code/scripts"
BINARY_NAME="benchmark"
BINARY_PATH="$PROJECT_ROOT/code/benchmark/$BINARY_NAME"

echo "=== T013 Integration Test: Build Script Success ==="
echo "Project Root: $PROJECT_ROOT"
echo "Scripts Dir: $CODE_SCRIPTS_DIR"
echo "Expected Binary: $BINARY_PATH"

# Check if build.sh exists
BUILD_SCRIPT="$CODE_SCRIPTS_DIR/build.sh"
if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "ERROR: build.sh not found at $BUILD_SCRIPT"
    exit 1
fi
echo "OK: build.sh found at $BUILD_SCRIPT"

# Ensure build.sh is executable
chmod +x "$BUILD_SCRIPT"

# Execute build.sh
echo "Executing build.sh..."
if ! bash "$BUILD_SCRIPT"; then
    echo "ERROR: build.sh failed with exit code $?"
    echo "Check build.log for details."
    exit 1
fi
echo "OK: build.sh executed successfully"

# Verify binary existence
if [ ! -f "$BINARY_PATH" ]; then
    echo "ERROR: Binary '$BINARY_NAME' not found at $BINARY_PATH"
    exit 1
fi
echo "OK: Binary '$BINARY_NAME' exists at $BINARY_PATH"

# Verify binary is executable
if [ ! -x "$BINARY_PATH" ]; then
    echo "ERROR: Binary '$BINARY_NAME' is not executable"
    exit 1
fi
echo "OK: Binary '$BINARY_NAME' is executable"

# Verify binary is valid ELF (basic check)
if ! file "$BINARY_PATH" | grep -q "ELF"; then
    echo "WARNING: Binary '$BINARY_PATH' does not appear to be a valid ELF executable"
    # Not a hard failure, as it might be a script or other valid format, but likely an issue
else
    echo "OK: Binary '$BINARY_PATH' is a valid ELF executable"
fi

echo "=== T013 Integration Test: PASSED ==="
exit 0