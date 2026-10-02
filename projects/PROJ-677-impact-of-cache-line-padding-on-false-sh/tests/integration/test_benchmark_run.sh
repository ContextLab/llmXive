#!/bin/bash
set -euo pipefail

PROJECT_ROOT="projects/PROJ-677-impact-of-cache-line-padding-on-false-sh"
SCRIPT_DIR="code/scripts"
DATA_DIR="data/raw"
BENCHMARK_BINARY="${PROJECT_ROOT}/code/benchmark/benchmark"
BUILD_SCRIPT="${PROJECT_ROOT}/${SCRIPT_DIR}/build.sh"
RUN_SCRIPT="${PROJECT_ROOT}/${SCRIPT_DIR}/run_benchmarks.sh"

echo "=== Integration Test: T020 - run_benchmarks.sh Sample Generation ==="

# 1. Ensure the benchmark binary exists (run build if missing)
if [[ ! -x "${BENCHMARK_BINARY}" ]]; then
    echo "Benchmark binary not found. Running build script..."
    if [[ -f "${BUILD_SCRIPT}" ]]; then
        bash "${BUILD_SCRIPT}"
    else
        echo "ERROR: Build script not found at ${BUILD_SCRIPT}"
        exit 1
    fi
fi

# 2. Ensure the run_benchmarks.sh script exists
if [[ ! -f "${RUN_SCRIPT}" ]]; then
    echo "ERROR: run_benchmarks.sh not found at ${RUN_SCRIPT}"
    exit 1
fi

# 3. Clean previous raw data to ensure fresh generation
echo "Cleaning previous raw data..."
rm -rf "${PROJECT_ROOT}/${DATA_DIR}"
mkdir -p "${PROJECT_ROOT}/${DATA_DIR}"

# 4. Execute the benchmark runner
# We expect this to take some time, but the task requires generating samples.
# If the script is not fully implemented to run all configs, we run a minimal subset
# to satisfy the "5 rows per config" verification for the test environment.
# However, per task T026, the script should handle the loop.
# We invoke the script directly.
echo "Executing run_benchmarks.sh..."
bash "${RUN_SCRIPT}"

# 5. Verification: Check data/raw/ contains CSV files
echo "Verifying output in ${DATA_DIR}..."
CSV_COUNT=$(find "${PROJECT_ROOT}/${DATA_DIR}" -name "*.csv" -type f | wc -l)

if [[ ${CSV_COUNT} -eq 0 ]]; then
    echo "FAIL: No CSV files found in ${DATA_DIR}"
    exit 1
fi

echo "Found ${CSV_COUNT} CSV file(s)."

# 6. Verification: Check that each CSV has at least 5 rows per configuration
# The task requires: "verify data/raw/ contains CSV files with 5 rows per config"
# We check the total row count for 'packed' and 'padded' across all files.
TOTAL_PACKED=0
TOTAL_PADDED=0

for csv_file in "${PROJECT_ROOT}/${DATA_DIR}"/*.csv; do
    if [[ -f "$csv_file" ]]; then
        echo "Checking file: $csv_file"
        # Count lines where configuration is 'packed' or 'padded'
        # Assuming header is present, we subtract 1 from total lines if needed, 
        # but grep -c is safer for specific values.
        PACKED_LINES=$(grep -c ",packed," "$csv_file" 2>/dev/null || echo 0)
        PADDED_LINES=$(grep -c ",padded," "$csv_file" 2>/dev/null || echo 0)
        
        TOTAL_PACKED=$((TOTAL_PACKED + PACKED_LINES))
        TOTAL_PADDED=$((TOTAL_PADDED + PADDED_LINES))
        
        echo "  - packed rows: ${PACKED_LINES}"
        echo "  - padded rows: ${PADDED_LINES}"
    fi
done

echo "Total packed rows: ${TOTAL_PACKED}"
echo "Total padded rows: ${TOTAL_PADDED}"

# 7. Final Assertion
if [[ ${TOTAL_PACKED} -lt 5 ]] || [[ ${TOTAL_PADDED} -lt 5 ]]; then
    echo "FAIL: Did not generate sufficient samples. Required >= 5 rows per config."
    echo "      Found: packed=${TOTAL_PACKED}, padded=${TOTAL_PADDED}"
    exit 1
fi

echo "SUCCESS: Integration test passed. Generated CSV files with >= 5 samples per configuration."
exit 0