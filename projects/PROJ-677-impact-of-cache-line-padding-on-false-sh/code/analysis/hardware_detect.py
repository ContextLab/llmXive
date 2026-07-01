"""
Hardware specification detection and CPU governor configuration utility.

This script detects the number of CPU cores, cache line size, and attempts
to set the CPU governor to 'performance' mode for consistent benchmarking.
"""

import os
import subprocess
import sys
import yaml
from pathlib import Path


def get_core_count() -> int:
    """Detect the number of logical CPU cores."""
    try:
        # Try os.cpu_count() first (Python standard)
        count = os.cpu_count()
        if count is not None and count > 0:
            return count
    except Exception:
        pass

    # Fallback: parse /proc/cpuinfo if available
    try:
        with open("/proc/cpuinfo", "r") as f:
            content = f.read()
            return content.count("processor\t:")
    except FileNotFoundError:
        pass

    # Final fallback: use nproc command
    try:
        result = subprocess.run(["nproc"], capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 1  # Default to 1 if detection fails


def get_cache_line_size() -> int:
    """Detect the CPU cache line size in bytes."""
    # Common default for x86_64
    default_size = 64

    # Try to read from sysfs (Linux)
    try:
        # Check for L1 data cache line size
        sysfs_path = "/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size"
        if os.path.exists(sysfs_path):
            with open(sysfs_path, "r") as f:
                return int(f.read().strip())
    except (ValueError, FileNotFoundError, PermissionError):
        pass

    # Try dmidecode if available (requires root usually)
    try:
        result = subprocess.run(
            ["dmidecode", "-t", "cache"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.splitlines():
            if "Line Size" in line:
                parts = line.split(":")
                if len(parts) > 1:
                  # Extract number (e.g., "64 Bytes")
                  num_str = "".join(filter(str.isdigit, parts[1]))
                  if num_str:
                      return int(num_str)
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Fallback: check getconf (sometimes available)
    try:
        result = subprocess.run(["getconf", "LEVEL1_DCACHE_LINESIZE"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        pass

    return default_size


def set_cpu_governor(target_governor: str = "performance") -> tuple[bool, str]:
    """
    Attempt to set the CPU governor to the specified mode.

    Returns:
        tuple: (success: bool, message: str)
    """
    governor_path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"

    # Check if we have permission to write
    if not os.path.exists(governor_path):
        return False, f"Governor path not found: {governor_path}. System may not support dynamic governor changes."

    if not os.access(governor_path, os.W_OK):
        return False, f"Permission denied: Cannot write to {governor_path}. Try running with sudo."

    # Check if the target governor is available
    available_path = governor_path.replace("scaling_governor", "scaling_available_governors")
    available_governors = []
    try:
        with open(available_path, "r") as f:
            available_governors = f.read().strip().split()
    except FileNotFoundError:
        pass

    if target_governor not in available_governors:
        current_governor = "unknown"
        try:
            with open(governor_path, "r") as f:
                current_governor = f.read().strip()
        except FileNotFoundError:
            pass
        return False, f"Governor '{target_governor}' not available. Available: {available_governors}. Current: {current_governor}"

    # Attempt to set the governor
    try:
        with open(governor_path, "w") as f:
            f.write(target_governor)
        return True, f"Successfully set CPU governor to '{target_governor}'"
    except PermissionError:
        return False, f"Permission denied while writing to {governor_path}. Try running with sudo."
    except Exception as e:
        return False, f"Failed to set governor: {str(e)}"


def generate_hardware_spec(output_path: str | None = None) -> dict:
    """
    Detect hardware specs and optionally save to a YAML file.

    Args:
        output_path: Optional path to save the YAML file. If None, only returns the dict.

    Returns:
        dict: Hardware specification dictionary.
    """
    core_count = get_core_count()
    cache_line_size = get_cache_line_size()
    governor_success, governor_msg = set_cpu_governor("performance")

    spec = {
        "detected_at": None,  # Will be set by caller if needed, or left as null
        "hardware": {
            "logical_cores": core_count,
            "cache_line_size_bytes": cache_line_size,
        },
        "cpu_governor": {
            "requested": "performance",
            "success": governor_success,
            "message": governor_msg
        }
    }

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    return spec


def main():
    """Entry point for the script."""
    # Default output path relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    output_file = project_root / "data" / "hardware_spec.yaml"

    print(f"Detecting hardware specifications...")
    print(f"  Logical Cores: {get_core_count()}")
    print(f"  Cache Line Size: {get_cache_line_size()} bytes")

    success, msg = set_cpu_governor("performance")
    print(f"  CPU Governor: {'Success' if success else 'Failed'} - {msg}")

    spec = generate_hardware_spec(str(output_file))

    print(f"\nHardware specification saved to: {output_file}")
    print("Contents:")
    with open(output_file, "r") as f:
        print(f.read())


if __name__ == "__main__":
    main()