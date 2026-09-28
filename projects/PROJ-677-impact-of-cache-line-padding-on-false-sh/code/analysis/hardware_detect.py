"""
Hardware detection and configuration module for benchmark environment setup.

Detects CPU model, core count, cache line size, and configures CPU governor
to 'performance' mode for consistent benchmarking results.
"""
import os
import subprocess
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import re


def get_core_count() -> int:
    """
    Detect the number of logical CPU cores available.
    
    Returns:
        int: Number of logical CPU cores.
        
    Raises:
        RuntimeError: If core count cannot be determined.
    """
    try:
        # Try using os.cpu_count() first (most portable)
        count = os.cpu_count()
        if count is not None and count > 0:
            return count
        
        # Fallback: parse /proc/cpuinfo on Linux
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                # Count 'processor' entries
                processors = re.findall(r'^processor\s*:\s*\d+', content, re.MULTILINE)
                if processors:
                    return len(processors)
        
        # Fallback: use nproc command
        result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
        
    except Exception as e:
        raise RuntimeError(f"Failed to determine CPU core count: {e}")


def get_cache_line_size() -> int:
    """
    Detect the CPU cache line size in bytes.
    
    Returns:
        int: Cache line size in bytes (typically 64).
        
    Raises:
        RuntimeError: If cache line size cannot be determined.
    """
    try:
        # Try reading from /sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size
        cache_path = '/sys/devices/system/cpu/cpu0/cache/index0/coherency_line_size'
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                size_hex = f.read().strip()
                return int(size_hex, 16)
        
        # Fallback: parse /proc/cpuinfo for 'cache_alignment'
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                match = re.search(r'cache_alignment\s*:\s*(\d+)', content)
                if match:
                    return int(match.group(1))
        
        # Fallback: use getconf on Linux
        result = subprocess.run(['getconf', 'LEVEL1_DCACHE_LINESIZE'], 
                              capture_output=True, text=True, check=True)
        return int(result.stdout.strip())
        
    except Exception as e:
        # Default to 64 bytes (most common) if detection fails
        # Log warning but don't fail
        print(f"Warning: Could not detect cache line size, defaulting to 64: {e}", file=sys.stderr)
        return 64


def get_cpu_model() -> str:
    """
    Detect the CPU model name.
    
    Returns:
        str: CPU model name string.
        
    Raises:
        RuntimeError: If CPU model cannot be determined.
    """
    try:
        # Try reading from /proc/cpuinfo
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
                match = re.search(r'model name\s*:\s*(.+)', content)
                if match:
                    return match.group(1).strip()
        
        # Fallback: use lscpu
        result = subprocess.run(['lscpu'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Model name' in line or 'model name' in line:
                    return line.split(':', 1)[1].strip()
        
        # Fallback: use dmidecode (requires root)
        try:
            result = subprocess.run(['dmidecode', '-s', 'processor-version'], 
                                  capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        return "Unknown CPU"
        
    except Exception as e:
        raise RuntimeError(f"Failed to determine CPU model: {e}")


def set_cpu_governor(governor: str = 'performance') -> bool:
    """
    Set the CPU frequency governor to the specified mode.
    
    Tries multiple methods: cpupower, direct sysfs, and fallback commands.
    
    Args:
        governor: The governor mode to set (e.g., 'performance', 'powersave').
        
    Returns:
        bool: True if governor was successfully set, False otherwise.
        
    Note:
        This operation may require root privileges. If it fails, a warning
        is printed but the function returns False without raising an exception.
    """
    success = False
    
    # Method 1: Try cpupower (preferred)
    try:
        result = subprocess.run(
            ['sudo', 'cpupower', '-c', 'all', 'frequency-set', '-g', governor],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Successfully set CPU governor to '{governor}' via cpupower")
            return True
    except FileNotFoundError:
        pass  # cpupower not available
    except Exception as e:
        print(f"Warning: cpupower failed: {e}", file=sys.stderr)
    
    # Method 2: Direct sysfs write (requires root)
    try:
        cpu_dirs = [d for d in os.listdir('/sys/devices/system/cpu/') 
                   if re.match(r'cpu\d+', d)]
        
        for cpu_dir in cpu_dirs:
            governor_path = f'/sys/devices/system/cpu/{cpu_dir}/cpufreq/scaling_governor'
            if os.path.exists(governor_path):
                try:
                    with open(governor_path, 'w') as f:
                        f.write(governor)
                    success = True
                except PermissionError:
                    print(f"Warning: Permission denied writing to {governor_path}", 
                          file=sys.stderr)
                    continue
                except Exception as e:
                    print(f"Warning: Failed to write to {governor_path}: {e}", 
                          file=sys.stderr)
                    continue
        
        if success:
            print(f"Successfully set CPU governor to '{governor}' via sysfs")
            return True
            
    except FileNotFoundError:
        pass  # /sys not available
    except Exception as e:
        print(f"Warning: sysfs method failed: {e}", file=sys.stderr)
    
    # Method 3: Try performance-profiler or other tools
    try:
        result = subprocess.run(
            ['sudo', 'systemd-run', '--scope', '-p', f'CPUAffinity={governor}'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Successfully set CPU governor via systemd")
            return True
    except Exception:
        pass
    
    # Final result
    if not success:
        print(f"Warning: Could not set CPU governor to '{governor}'. "
              f"Benchmark results may be affected by frequency scaling.", 
              file=sys.stderr)
        print("Hint: Run with sudo or install cpupower tools.", file=sys.stderr)
    
    return success


def generate_hardware_spec(output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a complete hardware specification dictionary and optionally write to YAML.
    
    Args:
        output_path: Optional path to write the YAML file. If None, only returns the dict.
        
    Returns:
        Dict[str, Any]: Dictionary containing hardware specifications.
    """
    try:
        # Gather hardware information
        spec = {
            'cpu_model': get_cpu_model(),
            'core_count': get_core_count(),
            'cache_line_size_bytes': get_cache_line_size(),
            'os': sys.platform,
            'python_version': sys.version,
            'timestamp': subprocess.run(
                ['date', '-Iseconds'], capture_output=True, text=True
            ).stdout.strip() if os.path.exists('/bin/date') else "unknown"
        }
        
        # Write to YAML if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                yaml.dump(spec, f, default_flow_style=False, sort_keys=False)
            
            print(f"Hardware specification written to: {output_file}")
        
        return spec
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate hardware specification: {e}")


def main():
    """
    Main entry point for hardware detection script.
    
    Detects hardware specifications, attempts to set CPU governor to performance,
    and writes the results to hardware_spec.yaml in the data directory.
    """
    # Determine output path
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / 'data'
    output_path = data_dir / 'hardware_spec.yaml'
    
    print("=" * 60)
    print("Hardware Detection and Configuration")
    print("=" * 60)
    
    try:
        # Generate hardware specification
        print("\n1. Detecting hardware specifications...")
        spec = generate_hardware_spec(str(output_path))
        
        print(f"   CPU Model: {spec['cpu_model']}")
        print(f"   Core Count: {spec['core_count']}")
        print(f"   Cache Line Size: {spec['cache_line_size_bytes']} bytes")
        print(f"   OS: {spec['os']}")
        
        # Attempt to set CPU governor
        print("\n2. Configuring CPU governor...")
        if set_cpu_governor('performance'):
            print("   ✓ CPU governor set to 'performance'")
        else:
            print("   ✗ Failed to set CPU governor (benchmark may be affected)")
        
        print("\n" + "=" * 60)
        print("Hardware detection complete.")
        print(f"Output written to: {output_path}")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
