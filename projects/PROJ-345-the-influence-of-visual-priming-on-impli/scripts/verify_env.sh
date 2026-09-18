#!/bin/bash
# Script to verify Python 3.11 virtualenv and installed dependencies
# Task: T003b - Create Python 3.11 virtualenv and install dependencies from requirements.txt
# Implementation: Assert specific package versions via pip show/list parsing

set -e

# Configuration
REQUIRED_PYTHON_VERSION="3.11"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11 is available
check_python_version() {
    log_info "Checking for Python ${REQUIRED_PYTHON_VERSION}..."
    if ! command -v python3.11 &> /dev/null; then
        log_error "Python ${REQUIRED_PYTHON_VERSION} is not installed or not in PATH."
        log_error "Please install Python 3.11 and ensure it is accessible."
        exit 1
    fi

    local installed_version
    installed_version=$(python3.11 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$installed_version" != "$REQUIRED_PYTHON_VERSION" ]]; then
        log_error "Python ${REQUIRED_PYTHON_VERSION} required, but found ${installed_version}."
        exit 1
    fi
    log_info "Python ${REQUIRED_PYTHON_VERSION} found."
}

# Create virtualenv if it doesn't exist
create_venv() {
    log_info "Checking virtualenv at ${VENV_DIR}..."
    if [[ ! -d "${VENV_DIR}" ]]; then
        log_info "Creating Python 3.11 virtualenv at ${VENV_DIR}..."
        python3.11 -m venv "${VENV_DIR}"
        log_info "Virtualenv created successfully."
    else
        log_info "Virtualenv already exists at ${VENV_DIR}."
    fi
}

# Activate virtualenv
activate_venv() {
    log_info "Activating virtualenv..."
    source "${VENV_DIR}/bin/activate"
    log_info "Virtualenv activated."
}

# Install dependencies from requirements.txt
install_dependencies() {
    if [[ ! -f "${REQUIREMENTS_FILE}" ]]; then
        log_error "requirements.txt not found at ${REQUIREMENTS_FILE}"
        exit 1
    fi

    log_info "Installing dependencies from ${REQUIREMENTS_FILE}..."
    # Upgrade pip first
    pip install --upgrade pip --quiet
    # Install requirements
    pip install -r "${REQUIREMENTS_FILE}" --quiet
    log_info "Dependencies installed successfully."
}

# Verify specific package versions
verify_package_version() {
    local package_name="$1"
    local expected_version="$2"
    local actual_version

    actual_version=$(pip show "${package_name}" 2>/dev/null | grep -E "^Version:" | awk '{print $2}')

    if [[ -z "${actual_version}" ]]; then
        log_error "Package '${package_name}' is not installed."
        return 1
    fi

    # Handle version comparison (simple prefix match for pinned versions)
    # e.g., pandas==2.0.3 -> check if actual starts with 2.0.3
    if [[ "${actual_version}" == "${expected_version}"* ]]; then
        log_info "✓ ${package_name}==${actual_version} (expected: ${expected_version}...)"
        return 0
    else
        log_error "✗ ${package_name} version mismatch: ${actual_version} != ${expected_version}"
        return 1
    fi
}

# Main verification logic
main() {
    log_info "Starting environment verification for T003b..."

    check_python_version
    create_venv
    activate_venv
    install_dependencies

    log_info "Verifying package versions..."

    # Define required packages and versions based on T003a requirements
    # These must match the versions in requirements.txt
    local packages=(
        "pandas:2.0.3"
        "numpy:1.24.3"
        "statsmodels:0.14.0"
        "scikit-learn:1.3.0"
        "requests:2.31.0"
        "pyyaml:6.0.1"
        "pillow:10.0.0"
    )

    local failed=0
    for entry in "${packages[@]}"; do
        package_name="${entry%%:*}"
        expected_version="${entry##*:}"
        if ! verify_package_version "${package_name}" "${expected_version}"; then
            ((failed++))
        fi
    done

    # Special handling for torch (CPU-only, version may vary)
    if pip show torch &> /dev/null; then
        log_info "✓ torch is installed (CPU-only check skipped, assuming correct via requirements.txt)"
    else
        log_warn "⚠ torch is not installed. Check requirements.txt for CPU-only specification."
    fi

    if [[ ${failed} -gt 0 ]]; then
        log_error "Verification failed: ${failed} package(s) did not match expected versions."
        exit 1
    fi

    log_info "All verifications passed successfully!"
    log_info "Virtualenv: ${VENV_DIR}"
    log_info "Python version: $(python --version)"
    exit 0
}

main "$@"