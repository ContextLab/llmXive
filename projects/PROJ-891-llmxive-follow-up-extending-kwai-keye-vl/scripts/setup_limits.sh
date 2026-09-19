#!/bin/bash
# setup_limits.sh - Configure system-level cgroups and ulimit wrappers for memory enforcement
# This script sets up memory limits for the llmXive pipeline to prevent OOM issues and enforce FR-006.
#
# Usage:
#   ./scripts/setup_limits.sh [memory_limit_mb]
#   Example: ./scripts/setup_limits.sh 7000  # Set 7GB limit

set -euo pipefail

# Configuration
MEMORY_LIMIT_MB=${1:-7000}  # Default to 7GB if not specified
CGROUP_NAME="llmxive_limit"
CGROUP_PATH="/sys/fs/cgroup/memory/${CGROUP_NAME}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

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

# Check if running as root (required for cgroup setup)
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_warn "This script requires root privileges to configure cgroups. Attempting to use ulimit fallback..."
        return 1
    fi
    return 0
}

# Check if cgroups v2 are available
check_cgroups_v2() {
    if [[ -d /sys/fs/cgroup ]]; then
        if grep -q cgroup /proc/filesystems; then
            log_info "cgroups detected. Checking version..."
            if [[ -f /sys/fs/cgroup/cgroup.controllers ]]; then
                log_info "cgroups v2 detected."
                return 0
            else
                log_warn "cgroups v1 detected. Setup will attempt v1 compatibility."
                return 1
            fi
        fi
    fi
    log_warn "cgroups not detected or not mounted. Falling back to ulimit."
    return 1
}

# Setup cgroups v2
setup_cgroups_v2() {
    log_info "Setting up cgroups v2 for memory limit: ${MEMORY_LIMIT_MB}MB"
    
    # Create cgroup directory
    if [[ ! -d "${CGROUP_PATH}" ]]; then
        mkdir -p "${CGROUP_PATH}"
        log_info "Created cgroup directory: ${CGROUP_PATH}"
    fi

    # Set memory limit (in bytes)
    MEMORY_LIMIT_BYTES=$((MEMORY_LIMIT_MB * 1024 * 1024))
    echo "${MEMORY_LIMIT_BYTES}" > "${CGROUP_PATH}/memory.max"
    log_info "Set memory.max to ${MEMORY_LIMIT_BYTES} bytes (${MEMORY_LIMIT_MB}MB)"

    # Enable memory controller
    echo "+memory" > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || true
    
    # Verify the limit was set
    CURRENT_LIMIT=$(cat "${CGROUP_PATH}/memory.max")
    if [[ "${CURRENT_LIMIT}" == "${MEMORY_LIMIT_BYTES}" ]]; then
        log_info "Successfully verified cgroup memory limit: ${CURRENT_LIMIT} bytes"
    else
        log_error "Failed to set memory limit. Expected ${MEMORY_LIMIT_BYTES}, got ${CURRENT_LIMIT}"
        return 1
    fi

    # Create a wrapper script for running commands in this cgroup
    cat > "${PROJECT_ROOT}/scripts/run_with_cgroup.sh" << EOF
#!/bin/bash
# Wrapper script to run commands within the llmxive cgroup memory limit
CGROUP_NAME="${CGROUP_NAME}"
CGROUP_PATH="/sys/fs/cgroup/memory/\${CGROUP_NAME}"

if [[ ! -d "\${CGROUP_PATH}" ]]; then
    echo "ERROR: Cgroup \${CGROUP_NAME} not found. Run setup_limits.sh first."
    exit 1
fi

# Move current process to the cgroup
echo \$$ > "\${CGROUP_PATH}/cgroup.procs"

# Execute the command
exec "\$@"
EOF
    chmod +x "${PROJECT_ROOT}/scripts/run_with_cgroup.sh"
    log_info "Created wrapper script: ${PROJECT_ROOT}/scripts/run_with_cgroup.sh"
}

# Setup cgroups v1 (fallback)
setup_cgroups_v1() {
    log_info "Setting up cgroups v1 for memory limit: ${MEMORY_LIMIT_MB}MB"
    
    # Check if cgroup-tools is installed
    if ! command -v cgcreate &> /dev/null; then
        log_warn "cgcreate not found. Attempting manual setup..."
        # Manual setup might not work without proper permissions
        return 1
    fi

    # Create cgroup
    cgcreate -g memory:${CGROUP_NAME}
    
    # Set memory limit
    MEMORY_LIMIT_BYTES=$((MEMORY_LIMIT_MB * 1024 * 1024))
    cgset -r memory.limit_in_bytes=${MEMORY_LIMIT_BYTES} ${CGROUP_NAME}
    
    log_info "Created cgroup ${CGROUP_NAME} with limit ${MEMORY_LIMIT_BYTES} bytes"
}

# Setup ulimit fallback (no root required)
setup_ulimit() {
    log_info "Setting up ulimit for memory limit: ${MEMORY_LIMIT_MB}MB"
    
    # Convert MB to KB (ulimit -v uses KB)
    MEMORY_LIMIT_KB=$((MEMORY_LIMIT_MB * 1024))
    
    # Create a wrapper script that sets ulimit before running commands
    cat > "${PROJECT_ROOT}/scripts/run_with_ulimit.sh" << EOF
#!/bin/bash
# Wrapper script to run commands with ulimit memory constraint
# Usage: ./run_with_ulimit.sh [command] [args...]

MEMORY_LIMIT_KB=${MEMORY_LIMIT_KB}

# Set virtual memory limit (in KB)
ulimit -v \${MEMORY_LIMIT_KB}

# Check if the limit was set
if [[ \$(ulimit -v) == "unlimited" ]]; then
    echo "WARNING: ulimit -v could not be set. Running without memory constraint."
else
    echo "INFO: Memory limit set to \$(ulimit -v) KB (\$(( \$(ulimit -v) / 1024 )) MB)"
fi

# Execute the command with all arguments
exec "\$@"
EOF
    chmod +x "${PROJECT_ROOT}/scripts/run_with_ulimit.sh"
    log_info "Created wrapper script: ${PROJECT_ROOT}/scripts/run_with_ulimit.sh"
}

# Verify memory limit via /proc/self/status
verify_limit() {
    log_info "Verifying memory limit configuration..."
    
    # Run a test command to check the limit
    if [[ -f "${PROJECT_ROOT}/scripts/run_with_ulimit.sh" ]]; then
        TEST_OUTPUT=$("${PROJECT_ROOT}/scripts/run_with_ulimit.sh" cat /proc/self/status 2>&1 || true)
        VMSIZE=$(echo "${TEST_OUTPUT}" | grep "VmSize" | awk '{print $2}')
        VMRSS=$(echo "${TEST_OUTPUT}" | grep "VmRSS" | awk '{print $2}')
        
        if [[ -n "${VMRSS}" ]]; then
            log_info "Current VmRSS: ${VMRSS} kB"
            log_info "Current VmSize: ${VMSIZE} kB"
        fi
    fi

    # Check if OOM killer is configured (system-wide)
    if [[ -f /proc/sys/vm/overcommit_memory ]]; then
        OVERCOMMIT=$(cat /proc/sys/vm/overcommit_memory)
        log_info "Memory overcommit setting: ${OVERCOMMIT}"
        if [[ "${OVERCOMMIT}" == "2" ]]; then
            log_info "Strict overcommit accounting is enabled. OOM kills will occur at configured limits."
        else
            log_warn "Overcommit accounting is not strict. OOM kills might not occur at exact limits."
        fi
    fi

    log_info "Verification complete. To test OOM kill behavior, run a memory-intensive process within the limit."
}

# Main execution
main() {
    log_info "Starting memory limit setup for ${MEMORY_LIMIT_MB}MB..."
    
    # Try cgroups first (requires root)
    if check_root && check_cgroups_v2; then
        setup_cgroups_v2
        verify_limit
        log_info "Setup completed successfully with cgroups v2."
        return 0
    elif check_root && check_cgroups_v1; then
        setup_cgroups_v1
        verify_limit
        log_info "Setup completed successfully with cgroups v1."
        return 0
    else
        log_warn "cgroups setup failed or not available. Using ulimit fallback."
        setup_ulimit
        verify_limit
        log_info "Setup completed with ulimit fallback. Note: ulimit is less strict than cgroups."
        return 0
    fi
}

# Run main function
main "$@"