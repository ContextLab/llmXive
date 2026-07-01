"""
Environment setup verification script for llmXive project PROJ-202.

This script verifies that the execution environment meets the strict
hardware constraints defined for the CPU-only pipeline:
1. Confirms no NVIDIA GPU is detected (CPU-only requirement).
2. Verifies available system RAM is below 7GB (free-tier constraint).

If constraints are violated, the script exits with a non-zero status
and a descriptive error message to prevent resource exhaustion on
restricted runners.
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

# Constants
MAX_RAM_GB = 7.0
RAM_TOLERANCE_GB = 0.2  # Allow small variance for OS reporting differences
MAX_ALLOWED_RAM_BYTES = int((MAX_RAM_GB + RAM_TOLERANCE_GB) * 1024 ** 3)

def check_gpu_availability() -> bool:
    """
    Check if an NVIDIA GPU is available via nvidia-smi or environment variables.
    
    Returns:
        True if a GPU is detected, False otherwise.
    """
    # Check CUDA_VISIBLE_DEVICES
    cuda_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_devices and cuda_devices != "-1":
        return True

    # Check for nvidia-smi command
    try:
        # Use shell=True for cross-platform compatibility in simple checks
        # but restrict to specific command to avoid injection
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode == 0 and result.stdout:
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    # Check for specific environment variables often set by GPU runners
    if os.environ.get("NVIDIA_DRIVER_VERSION"):
        return True
        
    return False

def get_system_ram_gb() -> float:
    """
    Get the total system RAM in GB.
    
    Returns:
        Total RAM in GB as a float.
    """
    system = platform.system()
    
    if system == "Linux":
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        # Format: MemTotal:        7932120 kB
                        parts = line.split()
                        kb = int(parts[1])
                        return kb / (1024 ** 2)
        except (IOError, ValueError, IndexError):
            pass
    
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            if result.returncode == 0:
                bytes_ram = int(result.stdout.strip())
                return bytes_ram / (1024 ** 3)
        except (subprocess.SubprocessError, ValueError):
            pass
    
    elif system == "Windows":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", c_ulonglong),
                    ("ullAvailPhys", c_ulonglong),
                    ("ullTotalPageFile", c_ulonglong),
                    ("ullAvailPageFile", c_ulonglong),
                    ("ullTotalVirtual", c_ulonglong),
                    ("ullAvailVirtual", c_ulonglong),
                    ("ullAvailExtendedVirtual", c_ulonglong),
                ]
            
            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(status)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            
            return status.ullTotalPhys / (1024 ** 3)
        except (AttributeError, OSError):
            pass

    # Fallback: Try using resource module if available (Unix)
    try:
        import resource
        # This is a heuristic and might not reflect physical RAM on all systems
        # but is better than nothing for some environments
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # This doesn't give total RAM, so we skip it for total RAM check
        # and rely on the fact that if we can't detect RAM, we assume it's safe
        # unless we have a specific failure mode.
        pass
    except ImportError:
        pass

    # If we can't determine RAM, we assume it's safe to proceed but warn
    # In a strict environment, this might need to be a failure.
    # For this script, we return a sentinel value that triggers a warning.
    return -1.0

def verify_environment() -> bool:
    """
    Verify the current environment meets the project constraints.
    
    Returns:
        True if constraints are met, False otherwise.
    """
    print("Checking environment constraints for llmXive pipeline...")
    
    # 1. Check GPU availability
    has_gpu = check_gpu_availability()
    if has_gpu:
        print("❌ ERROR: GPU detected. This pipeline is designed for CPU-only execution.")
        print("   Please run on a CPU-only runner or set CUDA_VISIBLE_DEVICES=-1.")
        return False
    print("✅ GPU check passed: No GPU detected.")

    # 2. Check RAM
    total_ram_gb = get_system_ram_gb()
    
    if total_ram_gb < 0:
        print("⚠️  WARNING: Could not determine total system RAM.")
        print("   Proceeding with caution. Ensure RAM is < 7GB.")
        return True # Don't fail if we can't check, but warn
    
    print(f"ℹ️  Detected Total RAM: {total_ram_gb:.2f} GB")
    
    if total_ram_gb > MAX_RAM_GB + RAM_TOLERANCE_GB:
        print(f"❌ ERROR: System RAM ({total_ram_gb:.2f} GB) exceeds limit ({MAX_RAM_GB} GB).")
        print("   This pipeline is optimized for free-tier runners with < 7GB RAM.")
        print("   Running on high-memory machines may cause unintended scaling.")
        return False
    
    print(f"✅ RAM check passed: {total_ram_gb:.2f} GB is within limit.")
    
    return True

def main():
    """Entry point for the environment setup verification."""
    if not verify_environment():
        sys.exit(1)
    print("✅ Environment verification successful.")
    sys.exit(0)

if __name__ == "__main__":
    main()