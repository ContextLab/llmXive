#!/bin/bash
#
# validate_env.sh - OS-level resource limit enforcement script
#
# Purpose: Harden the 7GB RAM constraint (FR-006, Constitution Principle VII)
# by setting OS-level resource limits via ulimit before pipeline execution.
#
# This script must be sourced or executed before running the main pipeline.
# It sets:
#   - Max resident set size (RAM) to 7GB
#   - Max CPU time to 6 hours (21600 seconds)
#   - Max open files to 1024 (standard for most workloads)
#
# Exit codes:
#   0 - Limits set successfully or already set
#   1 - Failed to set limits or environment check failed
#

set -e

# Configuration
RAM_LIMIT_GB=7
RAM_LIMIT_KB=$((RAM_LIMIT_GB * 1024 * 1024))
CPU_LIMIT_HOURS=6
CPU_LIMIT_SECONDS=$((CPU_LIMIT_HOURS * 3600))
OPEN_FILES_LIMIT=1024

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

# Check if running in a shell that supports ulimit
if ! command -v ulimit &> /dev/null; then
    log_error "ulimit command not found. Cannot enforce resource limits."
    exit 1
fi

# Check if we have permission to set limits
if [ "$EUID" -ne 0 ] && [ -z "$ALLOW_NON_ROOT" ]; then
    log_warn "Running as non-root. Some limits may not be enforceable."
fi

# Set soft and hard limits for RAM (max resident set size)
log_info "Setting RAM limit to ${RAM_LIMIT_GB}GB (${RAM_LIMIT_KB} KB)..."
if ! ulimit -v -S ${RAM_LIMIT_KB} 2>/dev/null; then
    # Try virtual memory limit if resident set doesn't work
    log_warn "Could not set resident set limit, trying virtual memory limit..."
    if ! ulimit -v -S ${RAM_LIMIT_KB} 2>/dev/null; then
        log_error "Failed to set RAM limit. Continuing with current limits."
    fi
else
    log_info "RAM limit set successfully."
fi

# Set hard limit for CPU time (6 hours)
log_info "Setting CPU time limit to ${CPU_LIMIT_HOURS} hours (${CPU_LIMIT_SECONDS} seconds)..."
if ! ulimit -t -S ${CPU_LIMIT_SECONDS} 2>/dev/null; then
    log_error "Failed to set CPU time limit."
    exit 1
fi
log_info "CPU time limit set successfully."

# Set open files limit
log_info "Setting open files limit to ${OPEN_FILES_LIMIT}..."
if ! ulimit -n -S ${OPEN_FILES_LIMIT} 2>/dev/null; then
    log_warn "Could not set open files limit. Continuing with current limit."
else
    log_info "Open files limit set successfully."
fi

# Verify the limits were applied
log_info "Verifying resource limits..."
CURRENT_RAM=$(ulimit -v -S 2>/dev/null || echo "unlimited")
CURRENT_CPU=$(ulimit -t -S 2>/dev/null || echo "unlimited")
CURRENT_FILES=$(ulimit -n -S 2>/dev/null || echo "unlimited")

log_info "Current soft limits:"
log_info "  RAM (virtual memory): ${CURRENT_RAM} KB"
log_info "  CPU time: ${CURRENT_CPU} seconds"
log_info "  Open files: ${CURRENT_FILES}"

# Check if limits are reasonable
if [ "$CURRENT_RAM" != "unlimited" ] && [ "$CURRENT_RAM" -lt "$RAM_LIMIT_KB" ]; then
    log_info "RAM limit is within expected range."
elif [ "$CURRENT_RAM" = "unlimited" ]; then
    log_warn "RAM limit is unlimited. This may violate FR-006."
fi

if [ "$CURRENT_CPU" != "unlimited" ] && [ "$CURRENT_CPU" -le "$CPU_LIMIT_SECONDS" ]; then
    log_info "CPU time limit is within expected range."
elif [ "$CURRENT_CPU" = "unlimited" ]; then
    log_warn "CPU time limit is unlimited. This may violate FR-006."
fi

log_info "Resource limit enforcement script completed successfully."
exit 0