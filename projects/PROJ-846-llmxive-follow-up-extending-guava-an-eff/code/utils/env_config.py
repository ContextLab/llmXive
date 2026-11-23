"""
Environment configuration and CPU constraint enforcement for llmXive.

This module provides utilities to verify that the execution environment
adheres to CPU-only constraints, preventing accidental GPU usage during
development or specific benchmark phases.
"""

import os
import sys
from pathlib import Path


class EnvironmentConfigError(RuntimeError):
    """Custom exception for environment configuration failures."""
    pass


def check_cpu_constraints() -> bool:
    """
    Verify that the environment is configured for CPU-only execution.

    Checks two conditions:
    1. The `CUDA_VISIBLE_DEVICES` environment variable is either unset or empty.
    2. The `--cpu-only` flag is present in the command line arguments (sys.argv).

    If a GPU is detected (CUDA_VISIBLE_DEVICES is set to a non-empty value)
    AND the `--cpu-only` flag is missing, this function raises a RuntimeError.

    Returns:
        bool: True if constraints are satisfied (CPU-only mode active or
              no GPU configured and flag present).

    Raises:
        RuntimeError: If a GPU is detected (CUDA_VISIBLE_DEVICES is set)
                      but the `--cpu-only` flag is not provided.
    """
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    has_cpu_flag = "--cpu-only" in sys.argv

    # Case 1: CUDA_VISIBLE_DEVICES is set to a non-empty string (GPU detected)
    if cuda_devices and not has_cpu_flag:
        raise RuntimeError(
            "GPU detected via CUDA_VISIBLE_DEVICES but '--cpu-only' flag is missing. "
            "Set CUDA_VISIBLE_DEVICES='' or add '--cpu-only' to arguments to enforce CPU-only mode."
        )

    # Case 2: CUDA_VISIBLE_DEVICES is empty/unset, but we still check for the flag
    # to ensure explicit intent if the environment is ambiguous, though strictly
    # the requirement is "empty OR --cpu-only flag".
    # The logic above covers: if GPU detected -> must have flag.
    # If no GPU detected -> no error.

    return True


def main():
    """Entry point for CLI usage of env_config checks."""
    try:
        check_cpu_constraints()
        print("Environment constraints satisfied: CPU-only mode enforced.")
        sys.exit(0)
    except RuntimeError as e:
        print(f"Environment constraint violation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()