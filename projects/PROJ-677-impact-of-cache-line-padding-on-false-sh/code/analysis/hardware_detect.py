import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import re
import platform

def get_cpu_model() -> str:
    """Detect CPU model from /proc/cpuinfo (Linux) or fallback."""
    if sys.platform == "linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if line.startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except FileNotFoundError:
            pass
    # Fallback to platform module
    return platform.processor() or platform.machine() or "Unknown CPU"

def get_core_count() -> int:
    """Detect logical core count."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1

def get_cache_line_size() -> int:
    """Detect cache line size (default 64 bytes if undetectable)."""
    if sys.platform == "linux":
        try:
            # Try reading from sysfs (modern Linux)
            cache_path = "/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size"
            if os.path.exists(cache_path):
                with open(cache_path, "r") as f:
                    return int(f.read().strip())
        except (FileNotFoundError, ValueError, PermissionError):
            pass
        
        try:
            # Fallback: lscpu
            result = subprocess.run(
                ["lscpu"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith("Cache line size:"):
                    return int(line.split(":", 1)[1].strip())
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass

    # Default assumption for x86_64
    return 64

def get_compiler_flags() -> str:
    """Detect default compiler flags or common optimization flags."""
    # Check environment variables first
    cxx_flags = os.environ.get("CXXFLAGS", "")
    if cxx_flags:
        return cxx_flags
    
    # Common default for build systems in this project
    return "-O3 -march=native"

def generate_hardware_spec(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Detect hardware specifications and write them to a YAML file.
    
    Args:
        output_path: Path to write the YAML file. Defaults to data/hardware_spec.yaml 
                     relative to the project root.
                     
    Returns:
        The generated specification dictionary.
    """
    if output_path is None:
        # Determine project root relative to this file's location
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent.parent
        output_path = project_root / "data" / "hardware_spec.yaml"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    spec = {
        "cpu_model": get_cpu_model(),
        "core_count": get_core_count(),
        "cache_line_size": get_cache_line_size(),
        "compiler_flags": get_compiler_flags(),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(output_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
    
    return spec

def main():
    """Entry point for running the hardware detection script."""
    try:
        spec = generate_hardware_spec()
        print(f"Hardware specification written to: {spec.get('output_path', 'data/hardware_spec.yaml')}")
        print(f"CPU Model: {spec['cpu_model']}")
        print(f"Core Count: {spec['core_count']}")
        print(f"Cache Line Size: {spec['cache_line_size']} bytes")
        print(f"Compiler Flags: {spec['compiler_flags']}")
        sys.exit(0)
    except Exception as e:
        print(f"Error generating hardware spec: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
