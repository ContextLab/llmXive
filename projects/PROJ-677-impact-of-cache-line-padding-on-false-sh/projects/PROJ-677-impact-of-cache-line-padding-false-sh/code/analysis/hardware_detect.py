import os
import subprocess
import sys
import yaml
from pathlib import Path

def get_core_count():
    """Get the number of CPU cores available."""
    try:
        # Try using os.cpu_count() first
        count = os.cpu_count()
        if count:
            return count
    except Exception:
        pass
    
    # Fallback to lscpu if available
    try:
        result = subprocess.run(['lscpu'], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if line.startswith('CPU(s):'):
                return int(line.split(':')[1].strip())
    except Exception:
        pass
    
    return 1  # Default fallback

def get_cache_line_size():
    """Get the CPU cache line size."""
    try:
        # Common default
        return 64
    except Exception:
        return 64

def set_cpu_governor(governor='performance'):
    """Set the CPU frequency governor to the specified mode."""
    # Path to sysfs
    path = Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')
    
    if not path.exists():
        # Fallback for systems without this path or requiring root
        # Try using cpupower if available
        try:
            subprocess.run(['sudo', 'cpupower', 'frequency-set', '-g', governor], check=True)
            return True
        except subprocess.CalledProcessError:
            print(f"Warning: Could not set CPU governor to {governor} via cpupower", file=sys.stderr)
            return False
        except FileNotFoundError:
            print(f"Warning: cpupower not found and sysfs path missing", file=sys.stderr)
            return False

    try:
        # Check if we have write permissions
        if os.access(path, os.W_OK):
            with open(path, 'w') as f:
                f.write(governor)
            return True
        else:
            # Try with sudo
            try:
                subprocess.run(['sudo', 'sh', '-c', f'echo {governor} > {path}'], check=True)
                return True
            except subprocess.CalledProcessError:
                print(f"Warning: Could not set CPU governor (permission denied)", file=sys.stderr)
                return False
    except Exception as e:
        print(f"Warning: Error setting CPU governor: {e}", file=sys.stderr)
        return False

def generate_hardware_spec(output_path=None):
    """Generate a YAML file with hardware specifications."""
    spec = {
        'core_count': get_core_count(),
        'cache_line_size': get_cache_line_size(),
        'cpu_governor': 'performance' if set_cpu_governor('performance') else 'unknown'
    }
    
    if output_path:
        path = Path(output_path)
        with open(path, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False)
        return path
    else:
        # Default to state/ directory if it exists, else current dir
        state_dir = Path('state')
        state_dir.mkdir(exist_ok=True)
        output_file = state_dir / 'hardware_spec.yaml'
        with open(output_file, 'w') as f:
            yaml.dump(spec, f, default_flow_style=False)
        return output_file

def main():
    """Main entry point."""
    print("Generating hardware specification...")
    spec_file = generate_hardware_spec()
    print(f"Hardware spec written to: {spec_file}")
    with open(spec_file, 'r') as f:
        print(f.read())

if __name__ == '__main__':
    main()
