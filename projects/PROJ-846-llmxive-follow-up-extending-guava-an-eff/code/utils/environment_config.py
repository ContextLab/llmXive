"""
Environment configuration management for CPU-only runner constraints.

This module enforces the CPU-only constraint required by the project's
execution environment. It provides utilities to verify hardware availability,
configure device settings, and enforce constraints before heavy computation.
"""

import os
import sys
import platform
import subprocess
from typing import Dict, Any, Optional, List

import numpy as np
import torch

from utils.exceptions import DatasetUnavailableError


class EnvironmentConfigError(Exception):
    """Raised when environment configuration constraints are violated."""
    pass


def detect_cpu_count() -> int:
    """
    Detect the number of available CPU cores.

    Returns:
        int: Number of logical CPU cores available.

    Raises:
        EnvironmentConfigError: If CPU count cannot be determined.
    """
    try:
        # Try os.cpu_count first (standard library)
        count = os.cpu_count()
        if count is not None and count > 0:
            return count

        # Fallback to platform-specific methods
        if platform.system() == "Windows":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # GetSystemInfo
            class SYSTEM_INFO(ctypes.Structure):
                _fields_ = [
                    ("wProcessorArchitecture", ctypes.c_ushort),
                    ("wReserved", ctypes.c_ushort),
                    ("dwPageSize", ctypes.c_ulong),
                    ("lpMinimumApplicationAddress", ctypes.c_void_p),
                    ("lpMaximumApplicationAddress", ctypes.c_void_p),
                    ("dwActiveProcessorMask", ctypes.c_void_p),
                    ("dwNumberOfProcessors", ctypes.c_ulong),
                    ("dwProcessorType", ctypes.c_ulong),
                    ("dwAllocationGranularity", ctypes.c_ulong),
                    ("wProcessorLevel", ctypes.c_ushort),
                    ("wProcessorRevision", ctypes.c_ushort),
                ]
            sys_info = SYSTEM_INFO()
            kernel32.GetSystemInfo(ctypes.byref(sys_info))
            if sys_info.dwNumberOfProcessors > 0:
                return sys_info.dwNumberOfProcessors
        else:
            # Linux/Unix: try nproc command
            result = subprocess.run(
                ["nproc"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    pass

        raise EnvironmentConfigError("Unable to determine CPU count")
    except Exception as e:
        raise EnvironmentConfigError(f"Failed to detect CPU count: {e}")


def verify_cpu_only_constraint() -> Dict[str, Any]:
    """
    Verify that the environment is configured for CPU-only execution.

    This function:
    1. Checks if CUDA is available but disabled (expected for CPU-only)
    2. Verifies PyTorch is using CPU
    3. Checks for any GPU device visibility
    4. Sets environment variables to enforce CPU-only behavior

    Returns:
        Dict[str, Any]: Configuration status including:
            - cpu_only: bool (True if CPU-only is enforced)
            - cuda_available: bool
            - cuda_disabled: bool
            - device: str (expected 'cpu')
            - cpu_count: int
            - warnings: List[str]

    Raises:
        EnvironmentConfigError: If GPU is detected and not explicitly disabled,
          or if CPU count is 0.
    """
    warnings = []
    cpu_count = detect_cpu_count()

    if cpu_count == 0:
        raise EnvironmentConfigError("No CPU cores detected. Cannot run.")

    # Check CUDA availability
    cuda_available = torch.cuda.is_available()
    cuda_disabled = os.environ.get("CUDA_VISIBLE_DEVICES", "") == ""

    # Enforce CPU-only by setting environment variables if CUDA is available
    if cuda_available and not cuda_disabled:
        warnings.append("CUDA is available but not explicitly disabled. Enforcing CPU-only.")
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        # Re-check
        cuda_available = torch.cuda.is_available()

    # Verify device
    device = torch.device("cpu")

    # Check if any GPU is visible
    gpu_visible = False
    if "CUDA_VISIBLE_DEVICES" in os.environ:
        visible = os.environ["CUDA_VISIBLE_DEVICES"]
        if visible and visible != "-1":
            gpu_visible = True

    if gpu_visible:
        warnings.append("GPU devices are visible. Setting CUDA_VISIBLE_DEVICES='' to enforce CPU-only.")
        os.environ["CUDA_VISIBLE_DEVICES"] = ""

    # Final verification
    if torch.cuda.is_available():
        raise EnvironmentConfigError(
            "GPU is still available after enforcement. "
            "Please run with CUDA_VISIBLE_DEVICES='' or set --cpu-only flag."
        )

    return {
        "cpu_only": True,
        "cuda_available": False,
        "cuda_disabled": True,
        "device": str(device),
        "cpu_count": cpu_count,
        "warnings": warnings,
        "platform": platform.system(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    }


def configure_torch_for_cpu() -> None:
    """
    Configure PyTorch for optimal CPU performance.

    This function:
    1. Sets the number of threads for intra-op and inter-op parallelism
    2. Disables CUDA
    3. Sets appropriate environment variables

    Must be called before any heavy computation.
    """
    # Ensure CUDA is disabled
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

    # Configure thread count (use half of available cores for better memory locality)
    cpu_count = detect_cpu_count()
    optimal_threads = max(1, cpu_count // 2)

    torch.set_num_threads(optimal_threads)
    torch.set_num_interop_threads(1)

    # Disable MKL multithreading if it conflicts
    # (usually not needed, but good practice)
    os.environ["OMP_NUM_THREADS"] = str(optimal_threads)


def get_environment_summary() -> Dict[str, Any]:
    """
    Get a comprehensive summary of the current environment configuration.

    Returns:
        Dict[str, Any]: Summary including:
            - hardware: CPU count, platform
            - software: Python version, PyTorch version
            - constraints: CPU-only status, CUDA status
            - configuration: Thread counts, device
    """
    try:
        config = verify_cpu_only_constraint()
        configure_torch_for_cpu()

        return {
            "hardware": {
                "platform": config["platform"],
                "cpu_count": config["cpu_count"],
            },
            "software": {
                "python_version": config["python_version"],
                "torch_version": torch.__version__,
                "numpy_version": np.__version__,
            },
            "constraints": {
                "cpu_only": config["cpu_only"],
                "cuda_available": config["cuda_available"],
                "cuda_disabled": config["cuda_disabled"],
            },
            "configuration": {
                "device": config["device"],
                "torch_threads": torch.get_num_threads(),
                "torch_interop_threads": torch.get_num_interop_threads(),
            },
            "warnings": config["warnings"],
        }
    except EnvironmentConfigError as e:
        return {
            "error": str(e),
            "cpu_only": False,
        }


def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by raising an error if GPU is detected.

    This is a strict check that should be called at the entry point of
    any script that must run on CPU only.

    Raises:
        EnvironmentConfigError: If GPU is detected.
    """
    config = verify_cpu_only_constraint()
    if not config["cpu_only"]:
        raise EnvironmentConfigError("CPU-only constraint violated.")


def main() -> None:
    """
    Main entry point for testing environment configuration.

    Prints a summary of the environment and any warnings.
    """
    print("=== Environment Configuration Check ===")
    try:
        summary = get_environment_summary()
        if "error" in summary:
            print(f"ERROR: {summary['error']}")
            sys.exit(1)

        print(f"Platform: {summary['hardware']['platform']}")
        print(f"CPU Cores: {summary['hardware']['cpu_count']}")
        print(f"Python: {summary['software']['python_version']}")
        print(f"PyTorch: {summary['software']['torch_version']}")
        print(f"Device: {summary['configuration']['device']}")
        print(f"CPU-only enforced: {summary['constraints']['cpu_only']}")
        print(f"Threads: {summary['configuration']['torch_threads']} (intra), {summary['configuration']['torch_interop_threads']} (interop)")

        if summary["warnings"]:
            print("\nWarnings:")
            for warning in summary["warnings"]:
                print(f"  - {warning}")
        else:
            print("\nNo warnings. Environment is correctly configured for CPU-only execution.")

    except EnvironmentConfigError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()