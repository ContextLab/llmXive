import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Tuple, Optional

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def check_cpu_cores() -> int:
    """Check available CPU cores."""
    try:
        if sys.platform == 'win32':
            return int(os.cpu_count() or 1)
        else:
            result = subprocess.run(['nproc'], capture_output=True, text=True, check=True)
            return int(result.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"Failed to check CPU cores: {e}")

def check_ram_gb() -> float:
    """Check available RAM in GB."""
    try:
        if sys.platform == 'win32':
            # Windows: use wmic or psutil if available
            try:
                import psutil
                return psutil.virtual_memory().total / (1024 ** 3)
            except ImportError:
                raise RuntimeError("psutil not installed on Windows")
        else:
            # Linux/Unix: use free command
            result = subprocess.run(['free', '-g'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            # Parse the 'Mem:' line
            for line in lines:
                if line.startswith('Mem:'):
                    parts = line.split()
                    if len(parts) >= 2:
                        return float(parts[1])
            raise RuntimeError("Could not parse RAM info from 'free' command")
    except Exception as e:
        raise RuntimeError(f"Failed to check RAM: {e}")

def check_gpu() -> bool:
    """Check if GPU is available."""
    try:
        if sys.platform == 'win32':
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
        else:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception as e:
        # Log warning but don't fail
        print(f"Warning: Could not check GPU: {e}")
        return False

def check_r_installed() -> Tuple[bool, str]:
    """Check if R is installed and get version."""
    try:
        result = subprocess.run(['R', '--version'], capture_output=True, text=True, check=True)
        # Extract version from first line
        first_line = result.stdout.split('\n')[0]
        return True, first_line
    except subprocess.CalledProcessError:
        return False, "R not installed"
    except FileNotFoundError:
        return False, "R command not found"

def check_renv_initialized() -> Tuple[bool, str]:
    """Check if renv is initialized."""
    project_root = get_project_root()
    renv_lock = project_root / 'renv.lock'
    renv_dir = project_root / 'renv'
    
    if renv_lock.exists() and renv_dir.exists():
        return True, "renv initialized"
    else:
        return False, "renv not initialized"

def run_ci_compatibility_check() -> dict:
    """Run all compatibility checks and return results."""
    results = {
        "timestamp": subprocess.run(['date', '-u', '+%Y-%m-%dT%H:%M:%SZ'], capture_output=True, text=True).stdout.strip(),
        "checks": {}
    }

    # Check CPU
    try:
        cores = check_cpu_cores()
        results["checks"]["cpu"] = {
            "status": "pass" if cores >= 2 else "warn",
            "value": cores,
            "unit": "cores",
            "message": f"Detected {cores} CPU cores"
        }
    except Exception as e:
        results["checks"]["cpu"] = {"status": "fail", "error": str(e)}

    # Check RAM
    try:
        ram = check_ram_gb()
        results["checks"]["ram"] = {
            "status": "pass" if ram >= 7.0 else "warn",
            "value": round(ram, 2),
            "unit": "GB",
            "message": f"Detected {ram:.2f} GB RAM"
        }
    except Exception as e:
        results["checks"]["ram"] = {"status": "fail", "error": str(e)}

    # Check GPU
    try:
        has_gpu = check_gpu()
        results["checks"]["gpu"] = {
            "status": "pass" if not has_gpu else "info",
            "value": has_gpu,
            "message": "GPU not required for this project (CPU-only)" if not has_gpu else "GPU detected but not used"
        }
    except Exception as e:
        results["checks"]["gpu"] = {"status": "warn", "error": str(e)}

    # Check R
    r_installed, r_msg = check_r_installed()
    results["checks"]["r_installed"] = {
        "status": "pass" if r_installed else "fail",
        "message": r_msg
    }

    # Check renv
    renv_ok, renv_msg = check_renv_initialized()
    results["checks"]["renv_initialized"] = {
        "status": "pass" if renv_ok else "warn",
        "message": renv_msg
    }

    # Overall status
    failed_checks = [k for k, v in results["checks"].items() if v.get("status") == "fail"]
    results["overall_status"] = "pass" if not failed_checks else "fail"
    results["failed_checks"] = failed_checks

    return results

def generate_ci_report(results: dict, output_path: Path) -> None:
    """Generate a human-readable CI run log."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("CI COMPATIBILITY CHECK REPORT\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Timestamp: {results['timestamp']}\n")
        f.write(f"Overall Status: {results['overall_status'].upper()}\n\n")
        
        f.write("DETAILED RESULTS:\n")
        f.write("-" * 40 + "\n")
        
        for check_name, check_data in results["checks"].items():
            status = check_data.get("status", "unknown").upper()
            f.write(f"\n[{status}] {check_name.replace('_', ' ').title()}\n")
            if "value" in check_data:
                f.write(f"  Value: {check_data['value']} {check_data.get('unit', '')}\n")
            f.write(f"  Message: {check_data.get('message', 'N/A')}\n")
            if "error" in check_data:
                f.write(f"  Error: {check_data['error']}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        if results["overall_status"] == "pass":
            f.write("SUCCESS: All critical checks passed.\n")
            f.write("The project is compatible with the CI runner constraints.\n")
        else:
            f.write("FAILURE: Some checks failed.\n")
            f.write(f"Failed checks: {', '.join(results['failed_checks'])}\n")
        f.write("=" * 60 + "\n")

def main():
    """Main entry point for CI compatibility check."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify CI runner compatibility")
    parser.add_argument("--output", type=str, default="logs/ci_run.log",
                      help="Path to output log file")
    args = parser.parse_args()

    project_root = get_project_root()
    output_path = project_root / args.output

    print("Running CI compatibility checks...")
    
    try:
        results = run_ci_compatibility_check()
        generate_ci_report(results, output_path)
        
        print(f"Report saved to: {output_path}")
        
        # Exit with error code if checks failed
        if results["overall_status"] == "fail":
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"ERROR: Compatibility check failed: {e}")
        # Write error to log
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(f"ERROR: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()