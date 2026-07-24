#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")/../.."
BUILD_SCRIPT="$PROJECT_ROOT/code/scripts/build.sh"
BUILD_DIR="$PROJECT_ROOT/build"

echo "=== Integration Test: Build Script ==="

# Clean previous build
rm -rf "$BUILD_DIR"

# Run build script
echo "Running build script..."
bash "$BUILD_SCRIPT"

# Verify executable exists
if [ ! -f "$BUILD_DIR/verify_layout" ]; then
    echo "FAILED: verify_layout executable not found"
    exit 1
fi

echo "PASSED: Build script completed successfully"
echo "Executable: $BUILD_DIR/verify_layout"

# Run the executable
echo "Running verify_layout..."
"$BUILD_DIR/verify_layout"

echo "PASSED: verify_layout executed successfully"
exit 0
