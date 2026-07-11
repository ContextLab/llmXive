"""
Environment validation script for llmXive project.
Verifies CPU-only constraints and absence of CUDA dependencies.
"""

import sys
import subprocess
import os
import json
from typing import Dict, Any, List, Tuple

# Import project config for consistency
from config import get_config, format_bytes


def check_python_version() -> Tuple[bool, str]:
    """Verify Python version is 3.11+."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"Python {version.major}.{version.minor}.{version.micro} (OK)"
    return False, f"Python {version.major}.{version.minor}.{version.micro} (Required: 3.11+)"


def check_cuda_availability() -> Tuple[bool, str]:
    """
    Check if CUDA is available in the environment.
    Returns (is_available, message).
    If CUDA is available, we flag it as a warning since we require CPU-only.
    """
    cuda_available = False
    messages = []

    # Check 1: Environment variables
    cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_visible and cuda_visible != '-1':
        cuda_available = True
        messages.append(f"CUDA_VISIBLE_DEVICES set to '{cuda_visible}'")

    # Check 2: Try importing torch and checking CUDA
    try:
        import torch
        if torch.cuda.is_available():
            cuda_available = True
            messages.append(f"PyTorch CUDA available: {torch.cuda.device_count()} devices")
            messages.append(f"  Current device: {torch.cuda.current_device()}")
            messages.append(f"  Device name: {torch.cuda.get_device_name(0)}")
    except ImportError:
        messages.append("PyTorch not installed (OK for CPU-only)")
    except Exception as e:
        messages.append(f"PyTorch CUDA check error: {str(e)}")

    # Check 3: Check for nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10
        )
        if result.returncode == 0:
            cuda_available = True
            messages.append("nvidia-smi found (CUDA hardware present)")
    except FileNotFoundError:
        messages.append("nvidia-smi not found (No CUDA hardware detected)")
    except subprocess.TimeoutExpired:
        messages.append("nvidia-smi timeout (Skipping)")
    except Exception as e:
        messages.append(f"nvidia-smi check error: {str(e)}")

    status = "WARNING" if cuda_available else "OK"
    return cuda_available, f"{status}: {'; '.join(messages)}"


def check_gpu_packages() -> Tuple[bool, List[str]]:
    """
    Check if GPU-specific packages are installed that might force GPU usage.
    Returns (has_gpu_packages, list_of_packages).
    """
    gpu_packages = []
    packages_to_check = [
        'torch', 'tensorflow', 'tensorflow-gpu', 'jax', 'jaxlib',
        'cupy', 'cupy-cuda11x', 'cupy-cuda12x'
    ]

    for pkg in packages_to_check:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'show', pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=10
            )
            gpu_packages.append(pkg)
        except subprocess.CalledProcessError:
            pass  # Package not installed
        except subprocess.TimeoutExpired:
            pass  # Skip timeout

    return len(gpu_packages) > 0, gpu_packages


def check_memory_limit() -> Tuple[bool, str]:
    """Check if system memory meets the 7GB limit requirement."""
    try:
        import resource
        # Get current memory limit
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)

        # Convert to bytes if not unlimited
        if soft_limit != resource.RLIM_INFINITY:
            soft_gb = soft_limit / (1024 ** 3)
            if soft_gb < 7:
                return False, f"Memory limit too low: {soft_gb:.2f}GB (Required: 7GB)"
            return True, f"Memory limit: {soft_gb:.2f}GB (OK)"
        else:
            # No limit set, check available memory
            import psutil
            available = psutil.virtual_memory().available
            available_gb = available / (1024 ** 3)
            if available_gb < 7:
                return False, f"Available memory too low: {available_gb:.2f}GB (Required: 7GB)"
            return True, f"Available memory: {available_gb:.2f}GB (OK)"
    except ImportError:
        # psutil not installed, skip detailed check
        return True, "Memory check skipped (psutil not installed)"
    except Exception as e:
        return False, f"Memory check error: {str(e)}"


def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if required dependencies from requirements.txt are installed."""
    required = [
        'beir', 'sentence-transformers', 'datasketch', 'scikit-learn',
        'scipy', 'pandas', 'numpy', 'pytest', 'nltk', 'psutil'
    ]
    missing = []

    for pkg in required:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'show', pkg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                timeout=10
            )
        except subprocess.CalledProcessError:
            missing.append(pkg)
        except subprocess.TimeoutExpired:
            missing.append(f"{pkg} (timeout)")

    return len(missing) == 0, missing


def run_validation() -> Dict[str, Any]:
    """Run all validation checks and return results."""
    results = {
        "timestamp": None,
        "validation_passed": True,
        "checks": {}
    }

    # Python version
    passed, msg = check_python_version()
    results["checks"]["python_version"] = {"passed": passed, "message": msg}
    if not passed:
        results["validation_passed"] = False

    # CUDA availability
    has_cuda, msg = check_cuda_availability()
    results["checks"]["cuda_availability"] = {"passed": not has_cuda, "message": msg}
    # CUDA presence is a warning, not a hard failure, but we flag it
    if has_cuda:
        results["checks"]["cuda_availability"]["warning"] = True
        # We don't set validation_passed to False for CUDA, but we log it

    # GPU packages
    has_gpu_pkgs, pkgs = check_gpu_packages()
    results["checks"]["gpu_packages"] = {
        "passed": not has_gpu_pkgs,
        "message": f"Found GPU packages: {pkgs}" if has_gpu_pkgs else "No GPU-specific packages found"
    }
    if has_gpu_pkgs:
        results["checks"]["gpu_packages"]["warning"] = True

    # Memory limit
    passed, msg = check_memory_limit()
    results["checks"]["memory_limit"] = {"passed": passed, "message": msg}
    if not passed:
        results["validation_passed"] = False

    # Dependencies
    passed, missing = check_dependencies()
    results["checks"]["dependencies"] = {
        "passed": passed,
        "message": f"Missing packages: {missing}" if missing else "All required packages installed"
    }
    if not passed:
        results["validation_passed"] = False

    return results


def main():
    """Main entry point for environment validation."""
    print("=" * 60)
    print("llmXive Environment Validation")
    print("=" * 60)

    results = run_validation()

    print(f"\nOverall Status: {'PASSED' if results['validation_passed'] else 'FAILED'}")
    print("-" * 60)

    for check_name, check_result in results["checks"].items():
        status = "✓ PASS" if check_result["passed"] else "✗ FAIL"
        warning = " [WARNING]" if check_result.get("warning") else ""
        print(f"{status}{warning} | {check_name}: {check_result['message']}")

    print("-" * 60)

    # Save results to a JSON file in data/
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "env_validation_results.json")

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")

    # Exit with appropriate code
    sys.exit(0 if results["validation_passed"] else 1)


if __name__ == "__main__":
    main()
