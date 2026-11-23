#!/bin/bash
#
# Test execution script for llm-code-review-impact
#
# Usage: ./scripts/run_tests.sh [unit|integration|all]
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

run_unit_tests() {
    echo "Running unit tests..."
    pytest tests/unit/ -v --tb=short
}

run_integration_tests() {
    echo "Running integration tests..."
    pytest tests/integration/ -v --tb=short
}

run_all_tests() {
    echo "Running all tests..."
    pytest tests/ -v --tb=short
}

main() {
    case "${1:-all}" in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        all)
            run_all_tests
            ;;
        *)
            echo "Usage: $0 [unit|integration|all]"
            exit 1
            ;;
    esac

    if [ $? -eq 0 ]; then
        log_success "All tests passed!"
    else
        log_error "Some tests failed!"
        exit 1
    fi
}

main "$@"