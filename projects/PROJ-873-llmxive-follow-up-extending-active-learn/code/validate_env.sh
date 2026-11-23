#!/bin/bash
# T004b: OS-level resource limit enforcement script
# Purpose: Harden the GB RAM constraint (7GB) using ulimit to serve Constitution Principle VII.
# This script sets a soft/hard memory limit for the current shell session and its children.
# It also verifies CPU-only constraints (CUDA) as part of the environment validation.

set -e

# Configuration
MAX_MEMORY_MB=7168  # 7GB in MB
MAX_MEMORY_KB=$((MAX_MEMORY_MB * 1024))
SCRIPT_NAME="validate_env.sh"

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_success() {
    echo "[SUCCESS] $1"
}

# 1. Check if running in an environment that supports ulimit (Linux/Unix)
if ! command -v ulimit &> /dev/null; then
    log_error "ulimit command not found. This script requires a POSIX-compliant shell."
    exit 1
fi

log_info "Checking system memory limits..."

# 2. Set the memory limit (virtual memory)
# Note: ulimit -v sets the virtual memory limit in KB.
# We set both soft and hard limits to enforce the constraint strictly.
log_info "Setting memory limit to ${MAX_MEMORY_MB}MB (${MAX_MEMORY_KB}KB)..."

if ! ulimit -v -S ${MAX_MEMORY_KB} 2>/dev/null; then
    log_error "Failed to set soft memory limit. You may need root privileges or the limit may be restricted by the OS."
    # In some CI environments, ulimit might be restricted. We log a warning but proceed if the check is informational.
    # However, for Constitution Principle VII, we must enforce it if possible.
    # If we can't set it, we fail loudly as per the task requirement to "harden" the constraint.
    log_error "Cannot enforce memory limit via ulimit. Aborting to ensure safety."
    exit 1
fi

if ! ulimit -v -H ${MAX_MEMORY_KB} 2>/dev/null; then
    log_error "Failed to set hard memory limit. Aborting."
    exit 1
fi

log_success "Memory limits set successfully: ${MAX_MEMORY_MB}MB."

# 3. Verify CUDA availability (Must be absent or ignored for CPU-only)
log_info "Checking CUDA availability..."
if command -v nvidia-smi &> /dev/null; then
    log_info "nvidia-smi found. Checking for GPU usage..."
    if nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader 2>/dev/null | grep -q "."; then
        log_error "GPU detected. This pipeline is CPU-only. Please disable GPU or run in a CPU-only environment."
        exit 1
    fi
fi

# Check if CUDA environment variables are set (common indicators)
if [ -n "${CUDA_VISIBLE_DEVICES}" ]; then
    if [ "${CUDA_VISIBLE_DEVICES}" != "-1" ]; then
        log_error "CUDA_VISIBLE_DEVICES is set to '${CUDA_VISIBLE_DEVICES}'. Set to '-1' for CPU-only."
        exit 1
    fi
fi

log_success "CUDA check passed: No GPU detected or GPU is disabled."

# 4. Verify memory limit is actually enforced (Self-test)
log_info "Verifying memory limit enforcement..."
# We attempt to allocate a large block of memory using a simple Python one-liner.
# If the limit is working, this should fail with a MemoryError or OOM kill.
# However, we just want to confirm the limit is set correctly.
CURRENT_LIMIT=$(ulimit -v)
if [ "$CURRENT_LIMIT" != "unlimited" ]; then
    log_success "Memory limit is active: ${CURRENT_LIMIT} KB."
else
    log_error "Memory limit appears to be 'unlimited'. This violates the safety constraint."
    exit 1
fi

log_success "Environment validation passed: Memory limit enforced, GPU constraints met."
exit 0
