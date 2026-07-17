"""
CI Compatibility Verification Script.

Verifies that the execution environment meets the project constraints:
- 2 CPU cores minimum
- 7 GB RAM minimum
- No GPU required (but must not crash if present)
- R 4.3+ installed
- renv initialized

This script is designed to run on the CI runner to validate resource constraints
before executing the full analysis pipeline.
"""
import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional
import resource
import multiprocessing

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def check_cpu_cores() -> Tuple[bool, str, int]:
    """
    Check if the system has at least 2 CPU cores.
    
    Returns:
        Tuple of (success, message, count)
    """
    try:
        # Try to get CPU count using os.cpu_count()
        count = os.cpu_count()
        if count is None:
            return False, "Could not determine CPU count", 0
        
        if count < 2:
            return False, f"Insufficient CPU cores: {count} (minimum 2 required)", count
        
        return True, f"CPU cores check passed: {count} cores available", count
    except Exception as e:
        return False, f"Error checking CPU cores: {str(e)}", 0

def check_ram_gb() -> Tuple[bool, str, float]:
    """
    Check if the system has at least 7 GB of RAM.
    
    Returns:
        Tuple of (success, message, available_gb)
    """
    try:
        # Get total memory in bytes
        total_mem = resource.getrlimit(resource.RLIMIT_AS)[0]
        if total_mem == resource.RLIM_INFINITY:
            # If no limit, try to get system memory
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemTotal:'):
                            mem_kb = int(line.split()[1])
                            total_mem = mem_kb * 1024
                            break
            except:
                # Fallback for macOS or other systems
                try:
                    total_mem = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
                except:
                    return False, "Could not determine system memory", 0.0
        
        total_gb = total_mem / (1024 ** 3)
        
        if total_gb < 7.0:
            return False, f"Insufficient RAM: {total_gb:.2f} GB (minimum 7 GB required)", total_gb
        
        return True, f"RAM check passed: {total_gb:.2f} GB available", total_gb
    except Exception as e:
        return False, f"Error checking RAM: {str(e)}", 0.0

def check_gpu() -> Tuple[bool, str, bool]:
    """
    Check if a GPU is present and report status.
    
    The project does not require a GPU, but we verify that the system
    can run without one and report if one is detected.
    
    Returns:
        Tuple of (success, message, has_gpu)
    """
    try:
        # Check for NVIDIA GPU using nvidia-smi
        has_gpu = False
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                has_gpu = True
                gpu_info = result.stdout.strip()
                return True, f"GPU detected (not required): {gpu_info}", True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for Apple Silicon GPU
        if sys.platform == 'darwin':
            try:
                result = subprocess.run(
                    ['sysctl', '-n', 'machdep.cpu.brand_string'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if 'Apple' in result.stdout:
                    return True, "Apple Silicon GPU detected (not required)", True
            except:
                pass
        
        return True, "No GPU detected (acceptable for this project)", False
    except Exception as e:
        return False, f"Error checking GPU: {str(e)}", False

def check_r_installed() -> Tuple[bool, str, Optional[str]]:
    """
    Check if R is installed and meets version requirements.
    
    Returns:
        Tuple of (success, message, version)
    """
    try:
        result = subprocess.run(
            ['R', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False, "R is not installed or not in PATH", None
        
        # Parse version from output
        version_line = result.stdout.split('\n')[0]
        version = version_line.split(' ')[-1].split('-')[0]
        
        # Check version >= 4.3
        major, minor = map(int, version.split('.')[:2])
        if major < 4 or (major == 4 and minor < 3):
            return False, f"R version {version} is too old (minimum 4.3 required)", version
        
        return True, f"R version check passed: {version}", version
    except FileNotFoundError:
        return False, "R is not installed or not in PATH", None
    except Exception as e:
        return False, f"Error checking R installation: {str(e)}", None

def check_renv_initialized() -> Tuple[bool, str, bool]:
    """
    Check if renv is initialized in the project.
    
    Returns:
        Tuple of (success, message, is_initialized)
    """
    try:
        project_root = get_project_root()
        renv_lock = project_root / 'renv.lock'
        renv_folder = project_root / 'renv'
        
        if renv_lock.exists() and renv_folder.exists():
            return True, "renv is initialized", True
        else:
            return False, "renv is not initialized (missing renv.lock or renv/ folder)", False
    except Exception as e:
        return False, f"Error checking renv initialization: {str(e)}", False

def run_ci_compatibility_check() -> List[Tuple[str, bool, str]]:
    """
    Run all CI compatibility checks.
    
    Returns:
        List of tuples: (check_name, success, message)
    """
    checks = [
        ("CPU Cores", check_cpu_cores),
        ("RAM", check_ram_gb),
        ("GPU Status", check_gpu),
        ("R Installation", check_r_installed),
        ("renv Initialization", check_renv_initialized),
    ]
    
    results = []
    for name, check_func in checks:
        success, message, _ = check_func()
        results.append((name, success, message))
    
    return results

def generate_ci_report(results: List[Tuple[str, bool, str]]) -> dict:
    """
    Generate a JSON report of CI compatibility checks.
    
    Args:
        results: List of check results
        
    Returns:
        Dictionary with check results and summary
    """
    all_passed = all(success for _, success, _ in results)
    
    report = {
        "ci_compatibility_check": {
            "timestamp": None,  # Will be set by caller if needed
            "overall_status": "PASS" if all_passed else "FAIL",
            "checks": {}
        }
    }
    
    for name, success, message in results:
        report["ci_compatibility_check"]["checks"][name] = {
            "status": "PASS" if success else "FAIL",
            "message": message
        }
    
    return report

def main():
    """Main entry point for CI compatibility verification."""
    print("=" * 60)
    print("CI COMPATIBILITY VERIFICATION")
    print("=" * 60)
    
    results = run_ci_compatibility_check()
    
    all_passed = True
    for name, success, message in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} | {name}: {message}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("OVERALL: CI environment is COMPATIBLE")
        sys.exit(0)
    else:
        print("OVERALL: CI environment is INCOMPATIBLE")
        sys.exit(1)

if __name__ == "__main__":
    main()
