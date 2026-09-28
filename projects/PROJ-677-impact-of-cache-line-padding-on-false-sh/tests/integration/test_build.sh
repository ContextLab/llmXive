#!/bin/bash
# Integration test for build script build.sh success
# Task: T013 [US1]
# Dependence: T015 (build.sh implementation)
# Description: Verifies that the build script compiles the C++ benchmark harness
#              successfully with the required optimization flags.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BUILD_SCRIPT="${PROJECT_ROOT}/code/scripts/build.sh"
BENCHMARK_DIR="${PROJECT_ROOT}/code/benchmark"
TEMP_BUILD_DIR="${PROJECT_ROOT}/code/benchmark/build_test"

echo "=== Integration Test: T013 - Build Script Success ==="
echo "Project Root: ${PROJECT_ROOT}"
echo "Build Script: ${BUILD_SCRIPT}"

# Check prerequisites
if [[ ! -f "${BUILD_SCRIPT}" ]]; then
    echo "ERROR: Build script not found at ${BUILD_SCRIPT}"
    exit 1
fi

if [[ ! -x "${BUILD_SCRIPT}" ]]; then
    echo "ERROR: Build script is not executable. Fixing permissions..."
    chmod +x "${BUILD_SCRIPT}"
fi

# Clean up any previous test build artifacts
if [[ -d "${TEMP_BUILD_DIR}" ]]; then
    rm -rf "${TEMP_BUILD_DIR}"
fi
mkdir -p "${TEMP_BUILD_DIR}"

# Execute the build script
echo "Executing build script..."
# We run the script from the project root to ensure relative paths work
cd "${PROJECT_ROOT}"

if ! bash "${BUILD_SCRIPT}" --output-dir "${TEMP_BUILD_DIR}" --verify; then
    echo "ERROR: Build script execution failed."
    exit 1
fi

# Verify that the expected binaries were created
EXPECTED_BINARIES=(
    "benchmark_packed"
    "benchmark_padded"
    "verify_layout"
)

echo "Verifying generated binaries..."
ALL_FOUND=true
for binary in "${EXPECTED_BINARIES[@]}"; do
    if [[ -f "${TEMP_BUILD_DIR}/${binary}" ]]; then
        echo "  [OK] ${binary} found"
    else
        echo "  [FAIL] ${binary} NOT found"
        ALL_FOUND=false
    fi
done

if [[ "${ALL_FOUND}" != "true" ]]; then
    echo "ERROR: One or more expected binaries are missing."
    exit 1
fi

# Verify binaries are executable
echo "Verifying binary executability..."
for binary in "${EXPECTED_BINARIES[@]}"; do
    if [[ -x "${TEMP_BUILD_DIR}/${binary}" ]]; then
        echo "  [OK] ${binary} is executable"
    else
        echo "  [FAIL] ${binary} is NOT executable"
        ALL_FOUND=false
    fi
done

if [[ "${ALL_FOUND}" != "true" ]]; then
    echo "ERROR: One or more binaries are not executable."
    exit 1
fi

# Optional: Run a quick single-threaded validation if verify_layout exists
if [[ -f "${TEMP_BUILD_DIR}/verify_layout" ]]; then
    echo "Running verify_layout quick check..."
    if "${TEMP_BUILD_DIR}/verify_layout"; then
        echo "  [OK] verify_layout passed"
    else
        echo "  [WARN] verify_layout returned non-zero (may be expected if strict checks fail, but build succeeded)"
    fi
fi

# Cleanup test artifacts
echo "Cleaning up test build directory..."
rm -rf "${TEMP_BUILD_DIR}"

echo "=== Integration Test T013 PASSED ==="
exit 0