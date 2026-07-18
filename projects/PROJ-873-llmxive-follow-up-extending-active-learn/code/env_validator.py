"""
Environment validation script for llmXive.
Verifies CPU-only constraints, absence of CUDA dependencies, and system resource limits.
"""
import sys
import subprocess
import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional
import resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_python_version(min_version: Tuple[int, int, int] = (3, 11, 0)) -> Dict[str, Any]:
    """
    Check if the running Python version meets the minimum requirement.
    
    Args:
        min_version: Minimum required version tuple (major, minor, micro)
        
    Returns:
        Dict with check results
    """
    current_version = sys.version_info
    is_valid = current_version >= min_version
    
    result = {
        "check": "python_version",
        "current": f"{current_version.major}.{current_version.minor}.{current_version.micro}",
        "required": f"{min_version[0]}.{min_version[1]}.{min_version[2]}",
        "passed": is_valid,
        "message": "Python version meets requirements" if is_valid else f"Python version {current_version.major}.{current_version.minor}.{current_version.micro} is below required {min_version[0]}.{min_version[1]}.{min_version[2]}"
    }
    
    return result


def check_cuda_availability() -> Dict[str, Any]:
    """
    Verify that CUDA is NOT available (CPU-only constraint).
    This ensures the pipeline runs in a CPU-only environment as required.
    
    Returns:
        Dict with check results
    """
    cuda_found = False
    error_message = None
    
    # Method 1: Check environment variables
    cuda_visible_devices = os.environ.get('CUDA_VISIBLE_DEVICES', '')
    if cuda_visible_devices and cuda_visible_devices != '-1':
        cuda_found = True
        error_message = "CUDA_VISIBLE_DEVICES is set to non-empty value (not '-1')"
    
    # Method 2: Try to import torch and check CUDA availability
    try:
        import torch
        if torch.cuda.is_available():
            cuda_found = True
            error_message = "PyTorch reports CUDA is available"
    except ImportError:
        # PyTorch not installed, which is fine for CPU-only
        pass
    except Exception as e:
        error_message = f"Error checking PyTorch CUDA: {str(e)}"
    
    # Method 3: Check for nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            cuda_found = True
            error_message = "nvidia-smi command succeeded, CUDA appears available"
    except FileNotFoundError:
        # nvidia-smi not found, which is expected in CPU-only env
        pass
    except subprocess.TimeoutExpired:
        error_message = "nvidia-smi command timed out"
    except Exception as e:
        error_message = f"Error running nvidia-smi: {str(e)}"
    
    # Method 4: Check for CUDA libraries
    cuda_lib_paths = [
        '/usr/local/cuda',
        '/usr/lib/x86_64-linux-gnu/libcuda.so',
        '/usr/lib64/libcuda.so'
    ]
    for path in cuda_lib_paths:
        if os.path.exists(path):
            cuda_found = True
            error_message = f"CUDA library path found: {path}"
            break
    
    is_valid = not cuda_found
    
    result = {
        "check": "cuda_availability",
        "passed": is_valid,
        "cuda_detected": cuda_found,
        "message": "CUDA is not available (CPU-only environment confirmed)" if is_valid else f"CUDA detected: {error_message}"
    }
    
    return result


def check_gpu_packages() -> Dict[str, Any]:
    """
    Verify that GPU-specific packages are not installed or are configured for CPU.
    
    Returns:
        Dict with check results
    """
    gpu_packages = {
        'torch': {'import_name': 'torch', 'check_cuda': True},
        'tensorflow': {'import_name': 'tensorflow', 'check_cuda': False},
        'tensorflow-gpu': {'import_name': 'tensorflow', 'check_cuda': False},
        'cupy': {'import_name': 'cupy', 'check_cuda': False},
    }
    
    issues = []
    warnings = []
    
    for pkg_name, pkg_info in gpu_packages.items():
        try:
            module = __import__(pkg_info['import_name'])
            
            # Special check for PyTorch
            if pkg_info['check_cuda']:
                if hasattr(module, 'cuda') and module.cuda.is_available():
                    issues.append(f"Package '{pkg_name}' has CUDA available")
                elif hasattr(module, 'cuda') and not module.cuda.is_available():
                    warnings.append(f"Package '{pkg_name}' is installed but CUDA not available (CPU mode)")
                else:
                    warnings.append(f"Package '{pkg_name}' is installed")
            else:
                warnings.append(f"Package '{pkg_name}' is installed")
                
        except ImportError:
            pass  # Package not installed, which is fine
        except Exception as e:
            warnings.append(f"Error checking package '{pkg_name}': {str(e)}")
    
    is_valid = len(issues) == 0
    
    result = {
        "check": "gpu_packages",
        "passed": is_valid,
        "issues": issues,
        "warnings": warnings,
        "message": "No GPU packages with active CUDA detected" if is_valid else f"GPU package issues found: {', '.join(issues)}"
    }
    
    return result


def check_memory_limit(max_memory_gb: float = 7.0) -> Dict[str, Any]:
    """
    Check if the system has sufficient memory and validate the limit.
    
    Args:
        max_memory_gb: Maximum allowed memory in GB (default 7GB as per FR-006)
        
    Returns:
        Dict with check results
    """
    try:
        # Get total system memory
        if sys.platform == 'win32':
            # Windows
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong
            
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', c_ulonglong),
                    ('ullAvailPhys', c_ulonglong),
                    ('ullTotalPageFile', c_ulonglong),
                    ('ullAvailPageFile', c_ulonglong),
                    ('ullTotalVirtual', c_ulonglong),
                    ('ullAvailVirtual', c_ulonglong),
                    ('ullAvailExtendedVirtual', c_ulonglong),
                ]
            
            memoryStatus = MEMORYSTATUSEX()
            memoryStatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memoryStatus))
            total_memory_bytes = memoryStatus.ullTotalPhys
        else:
            # Unix/Linux/Mac
            total_memory_bytes = resource.getconf('SC_PHYS_PAGES') * resource.getconf('SC_PAGE_SIZE')
        
        total_memory_gb = total_memory_bytes / (1024 ** 3)
        is_valid = total_memory_gb <= max_memory_gb + 1.0  # Allow slight buffer
        
        result = {
            "check": "memory_limit",
            "total_memory_gb": round(total_memory_gb, 2),
            "max_allowed_gb": max_memory_gb,
            "passed": is_valid,
            "message": f"System memory ({total_memory_gb:.2f}GB) is within acceptable range" if is_valid else f"System memory ({total_memory_gb:.2f}GB) exceeds recommended limit ({max_memory_gb}GB)"
        }
        
    except Exception as e:
        result = {
            "check": "memory_limit",
            "passed": False,
            "error": str(e),
            "message": f"Error checking memory: {str(e)}"
        }
    
    return result


def check_dependencies(required_packages: List[str] = None) -> Dict[str, Any]:
    """
    Verify that required dependencies are installed.
    
    Args:
        required_packages: List of package names to check (uses defaults if None)
        
    Returns:
        Dict with check results
    """
    if required_packages is None:
        required_packages = [
            'beir',
            'sentence-transformers',
            'datasketch',
            'scikit-learn',
            'scipy',
            'pandas',
            'numpy',
            'pytest',
            'nltk',
            'pyyaml'
        ]
    
    missing = []
    installed = []
    errors = []
    
    for package in required_packages:
        try:
            # Normalize package name for import
            import_name = package.replace('-', '_')
            __import__(import_name)
            installed.append(package)
        except ImportError:
            # Try original name as fallback
            try:
                __import__(package)
                installed.append(package)
            except ImportError:
                missing.append(package)
        except Exception as e:
            errors.append(f"{package}: {str(e)}")
    
    is_valid = len(missing) == 0 and len(errors) == 0
    
    result = {
        "check": "dependencies",
        "passed": is_valid,
        "installed": installed,
        "missing": missing,
        "errors": errors,
        "message": "All required dependencies are installed" if is_valid else f"Missing dependencies: {', '.join(missing)}"
    }
    
    return result


def run_validation(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run all environment validation checks.
    
    Args:
        config: Optional configuration dict with custom parameters
        
    Returns:
        Dict containing all check results and overall status
    """
    logger.info("Starting environment validation...")
    
    checks = [
        check_python_version(),
        check_cuda_availability(),
        check_gpu_packages(),
        check_memory_limit(
            max_memory_gb=config.get('max_memory_gb', 7.0) if config else 7.0
        ),
        check_dependencies(
            required_packages=config.get('required_packages') if config else None
        )
    ]
    
    all_passed = all(check['passed'] for check in checks)
    
    result = {
        "validation_status": "passed" if all_passed else "failed",
        "timestamp": os.popen('date -Iseconds 2>/dev/null || date').read().strip(),
        "checks": checks,
        "summary": {
            "total_checks": len(checks),
            "passed": sum(1 for check in checks if check['passed']),
            "failed": sum(1 for check in checks if not check['passed'])
        }
    }
    
    # Log results
    for check in checks:
        status = "✓ PASS" if check['passed'] else "✗ FAIL"
        logger.info(f"{status} - {check['check']}: {check['message']}")
    
    if all_passed:
        logger.info("Environment validation PASSED. Ready to run pipeline.")
    else:
        failed_checks = [c['check'] for c in checks if not c['passed']]
        logger.error(f"Environment validation FAILED. Failed checks: {', '.join(failed_checks)}")
    
    return result


def main():
    """Main entry point for the environment validator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate environment for llmXive pipeline (CPU-only constraints)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output file path for JSON results (optional)'
    )
    parser.add_argument(
        '--max-memory-gb',
        type=float,
        default=7.0,
        help='Maximum allowed memory in GB (default: 7.0)'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if any check fails'
    )
    
    args = parser.parse_args()
    
    config = {
        'max_memory_gb': args.max_memory_gb
    }
    
    result = run_validation(config)
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Results written to {args.output}")
    else:
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION RESULTS")
        print("="*60)
        print(f"Status: {result['validation_status'].upper()}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Checks: {result['summary']['passed']}/{result['summary']['total_checks']} passed")
        print("-"*60)
        
        for check in result['checks']:
            status = "✓ PASS" if check['passed'] else "✗ FAIL"
            print(f"{status} | {check['check']}")
            print(f"       {check['message']}")
            if not check['passed'] and 'error' in check:
                print(f"       Error: {check['error']}")
            print()
        
        print("="*60)
    
    # Exit with appropriate code
    if args.strict and result['validation_status'] == 'failed':
        sys.exit(1)
    
    sys.exit(0 if result['validation_status'] == 'passed' else 1)


if __name__ == '__main__':
    main()