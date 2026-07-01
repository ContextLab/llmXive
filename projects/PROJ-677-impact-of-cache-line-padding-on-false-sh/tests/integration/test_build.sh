#!/bin/bash
# Integration test for build.sh
# Verifies that the build script compiles successfully and produces binaries
#
# Exit codes:
# 0 - Success (both binaries exist and are executable)
# 1 - Failure (build script failed or binaries missing)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "${SCRIPT_DIR}")")"
BUILD_SCRIPT="${PROJECT_ROOT}/code/scripts/build.sh"
BENCHMARK_DIR="${PROJECT_ROOT}/code/benchmark"

echo "=== Integration Test: Build Script ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Build Script: ${BUILD_SCRIPT}"
echo ""

# Check if build script exists
if [[ ! -f "${BUILD_SCRIPT}" ]]; then
    echo "ERROR: Build script not found at ${BUILD_SCRIPT}"
    exit 1
fi

# Make build script executable
chmod +x "${BUILD_SCRIPT}"

# Clean previous builds if they exist
if [[ -f "${BENCHMARK_DIR}/benchmark" ]]; then
    rm -f "${BENCHMARK_DIR}/benchmark"
    echo "Removed existing benchmark binary"
fi
if [[ -f "${BENCHMARK_DIR}/verify_layout" ]]; then
    rm -f "${BENCHMARK_DIR}/verify_layout"
    echo "Removed existing verify_layout binary"
fi

# Run build script
echo "Running build script..."
if ! bash "${BUILD_SCRIPT}"; then
    echo "ERROR: Build script failed"
    exit 1
fi
echo ""

# Verify binaries exist
echo "Checking for compiled binaries..."
if [[ ! -f "${BENCHMARK_DIR}/benchmark" ]]; then
    echo "ERROR: benchmark binary not found"
    exit 1
fi
if [[ ! -f "${BENCHMARK_DIR}/verify_layout" ]]; then
    echo "ERROR: verify_layout binary not found"
    exit 1
fi
echo "Both binaries found."

# Verify binaries are executable
if [[ ! -x "${BENCHMARK_DIR}/benchmark" ]]; then
    echo "ERROR: benchmark binary is not executable"
    exit 1
fi
if [[ ! -x "${BENCHMARK_DIR}/verify_layout" ]]; then
    echo "ERROR: verify_layout binary is not executable"
    exit 1
fi
echo "Both binaries are executable."

# Run verify_layout to ensure it works (single-threaded validation)
echo ""
echo "Running verify_layout binary..."
if ! "${BENCHMARK_DIR}/verify_layout"; then
    echo "ERROR: verify_layout binary failed to run"
    exit 1
fi
echo "verify_layout ran successfully."

echo ""
echo "=== Integration Test: PASSED ==="
echo "Build script compiles successfully and produces working binaries."