import os
import subprocess
import sys
import yaml
from pathlib import Path

def get_core_count() -> int:
    """Detect the number of physical or logical CPU cores available."""
    try:
        # Try using nproc first (standard on Linux)
        result = subprocess.run(
            ["nproc"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        # Fallback: read /proc/cpuinfo
        try:
            with open("/proc/cpuinfo", "r") as f:
                lines = f.readlines()
            count = sum(1 for line in lines if line.startswith("processor"))
            if count > 0:
                return count
        except FileNotFoundError:
            pass
        
        # Final fallback: use os.cpu_count()
        count = os.cpu_count()
        if count is not None:
            return count
        
        raise RuntimeError("Could not determine CPU core count.")

def get_cache_line_size() -> int:
    """Detect the CPU cache line size (typically 64 bytes)."""
    try:
        # Try using getconf (standard on Linux/Unix)
        result = subprocess.run(
            ["getconf", "LEVEL1_DCACHE_LINESIZE"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return int(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass

    try:
        # Fallback: read from sysfs on Linux
        with open("/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size", "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        pass

    try:
        # Fallback: read /proc/cpuinfo for 'cache_alignment' (some architectures)
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("cache alignment"):
                    return int(line.split(":")[1].strip())
    except FileNotFoundError:
        pass

    # Default assumption for modern x86_64 systems
    return 64

def set_cpu_governor(governor: str = "performance") -> bool:
    """
    Attempt to set the CPU frequency governor to the specified mode.
    Returns True if successful, False otherwise.
    
    Tries two methods:
    1. cpupower command (preferred)
    2. Direct write to /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
    """
    # Method 1: Try cpupower
    try:
        subprocess.run(
            ["sudo", "cpupower", "frequency-set", "-g", governor],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Method 2: Direct sysfs write (requires root)
    cpu_dirs = list(Path("/sys/devices/system/cpu").glob("cpu[0-9]*"))
    if not cpu_dirs:
        return False

    success_count = 0
    for cpu_dir in cpu_dirs:
        governor_path = cpu_dir / "cpufreq" / "scaling_governor"
        if governor_path.exists():
            try:
                # Check if we have write permission
                if os.access(governor_path, os.W_OK):
                    governor_path.write_text(f"{governor}\n")
                    success_count += 1
                else:
                    # Try with sudo
                    subprocess.run(
                        ["sudo", "sh", "-c", f"echo {governor} > {governor_path}"],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    success_count += 1
            except (subprocess.CalledProcessError, PermissionError, OSError):
                continue

    return success_count > 0

def generate_hardware_spec(output_path: str = "hardware_spec.yaml") -> dict:
    """
    Detect hardware specifications and generate a YAML file.
    
    Returns the specification dictionary.
    """
    core_count = get_core_count()
    cache_line_size = get_cache_line_size()
    governor_set = set_cpu_governor("performance")
    
    spec = {
        "detected_at": None,  # Can be filled with datetime if needed
        "cpu": {
            "core_count": core_count,
            "cache_line_size_bytes": cache_line_size,
            "governor_requested": "performance",
            "governor_set_successfully": governor_set
        }
    }
    
    # Write to YAML file
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    
    return spec

def main():
    """Main entry point for the hardware detection script."""
    output_file = "hardware_spec.yaml"
    print(f"Detecting hardware specifications...")
    
    try:
        spec = generate_hardware_spec(output_file)
        print(f"Hardware detection complete.")
        print(f"  Cores: {spec['cpu']['core_count']}")
        print(f"  Cache Line Size: {spec['cpu']['cache_line_size_bytes']} bytes")
        print(f"  Governor Set: {'Success' if spec['cpu']['governor_set_successfully'] else 'Failed (check permissions)'}")
        print(f"  Output written to: {output_file}")
    except Exception as e:
        print(f"Error during hardware detection: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
