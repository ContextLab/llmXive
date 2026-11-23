#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BENCHMARK_DIR="$PROJECT_ROOT/benchmark"

echo "=== Applying clang-format to C++ files ==="

# Check for clang-format
if ! command -v clang-format &> /dev/null; then
    echo "ERROR: clang-format is not installed."
    echo "Install it via: sudo apt-get install clang-format"
    echo "or: brew install clang-format"
    exit 1
fi

echo "clang-format version: $(clang-format --version)"

# Find all C++ files
CPP_FILES=$(find "$BENCHMARK_DIR" -name "*.cpp" -o -name "*.hpp" -o -name "*.h")

if [ -z "$CPP_FILES" ]; then
    echo "No C++ files found in $BENCHMARK_DIR"
    exit 0
fi

echo "Formatting files:"
echo "$CPP_FILES" | tr '\n' ' '
echo ""

# Apply clang-format in-place
for file in $CPP_FILES; do
    echo "Formatting: $file"
    clang-format -i "$file"
done

echo ""
echo "=== Formatting Complete ==="
echo "All C++ source files have been formatted with clang-format."
