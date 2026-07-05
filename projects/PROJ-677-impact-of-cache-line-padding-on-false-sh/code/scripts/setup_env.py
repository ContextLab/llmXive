"""
setup_env.py - Helper script to manage environment setup for benchmarks.

This script provides a Python interface to set CPU governors and pinning,
acting as a fallback or verification tool for the bash script.
It uses the functions from code/analysis/hardware_detect.py.
"""
import sys
import os
import subprocess
import time

# Add project root to path to import analysis modules
# Assumes this script is in code/scripts/ and analysis is in code/analysis/
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from analysis.hardware_detect import set_cpu_governor, get_core_count

def main():
    """
    Main entry point to set up the environment for benchmarking.
    """
    print("Setting up environment for benchmarking...")
    
    # Attempt to set governor
    try:
        # The hardware_detect module handles the cpupower/sysfs logic
        set_cpu_governor('performance')
        print("CPU governor set to 'performance'.")
    except PermissionError:
        print("Error: Permission denied. Try running with sudo.")
        print("  sudo python3 code/scripts/setup_env.py")
        sys.exit(1)
    except Exception as e:
        print(f"Warning: Could not set CPU governor: {e}")
        print("Continuing benchmark setup without governor change.")

    core_count = get_core_count()
    print(f"Detected {core_count} logical cores.")
    
    print("Environment setup complete.")

if __name__ == "__main__":
    main()