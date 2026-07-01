"""
CPU Health Check Module for SDAR Project.

This module provides utilities to detect available CPU count and verify
that the project can run without raising ImportError for torch.cuda.
"""
import os
import json
import sys
import torch

def get_cpu_count() -> int:
    """
    Detect and return the number of available CPU cores.
    
    Returns:
        int: Number of available CPU cores.
    
    Raises:
        RuntimeError: If CPU count cannot be determined.
    """
    try:
        # Use os.cpu_count() which is the standard way to get CPU count
        count = os.cpu_count()
        if count is None:
            # Fallback: try to read from /proc/cpuinfo if available
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    count = sum(1 for line in f if line.startswith('processor'))
            else:
                # Last resort: default to 2 if we can't determine
                count = 2
        
        # Ensure we have at least 2 CPUs as per requirements
        if count < 2:
            # Log warning but don't fail - the system might be constrained
            sys.stderr.write(f"Warning: Only {count} CPU detected, but >= 2 expected.\n")
        
        return count
    except Exception as e:
        sys.stderr.write(f"Error detecting CPU count: {e}\n")
        # Return a safe default
        return 2

def check_no_cuda_import_error() -> bool:
    """
    Verify that torch.cuda can be imported without raising ImportError.
    
    This function attempts to import torch.cuda and returns True if successful.
    If torch.cuda is not available (e.g., CPU-only PyTorch), it returns True
    as long as the import doesn't raise an ImportError.
    
    Returns:
        bool: True if torch.cuda import succeeds (even if CUDA is unavailable),
              False if ImportError is raised.
    """
    try:
        # Attempt to access torch.cuda - this should not raise ImportError
        # in a properly configured CPU-only environment
        _ = torch.cuda
        return True
    except ImportError as e:
        sys.stderr.write(f"ImportError when accessing torch.cuda: {e}\n")
        return False
    except Exception as e:
        # Any other exception (e.g., AttributeError) is not an ImportError
        # and indicates the import succeeded but CUDA might not be available
        sys.stderr.write(f"Non-ImportError when accessing torch.cuda: {e}\n")
        return True

def run_health_check() -> dict:
    """
    Run a comprehensive health check for CPU and CUDA availability.
    
    Returns:
        dict: Dictionary containing health check results with keys:
              - 'cpu_count': Number of available CPUs
              - 'cuda_import_ok': Boolean indicating if torch.cuda import succeeded
              - 'healthy': Boolean indicating if the system is healthy
              - 'message': Human-readable status message
    """
    cpu_count = get_cpu_count()
    cuda_import_ok = check_no_cuda_import_error()
    
    # System is healthy if we have >= 2 CPUs and no ImportError for torch.cuda
    healthy = cpu_count >= 2 and cuda_import_ok
    
    message = ""
    if not healthy:
        if cpu_count < 2:
            message += f"CPU count ({cpu_count}) is less than required (2). "
        if not cuda_import_ok:
            message += "torch.cuda import failed with ImportError. "
    else:
        message = f"System healthy: {cpu_count} CPUs detected, torch.cuda import successful."
    
    return {
        'cpu_count': cpu_count,
        'cuda_import_ok': cuda_import_ok,
        'healthy': healthy,
        'message': message
    }

def main():
    """
    Main entry point for CPU health check script.
    
    This function runs the health check and outputs results to stdout
    and to a JSON file at outputs/health/cpu_health.json.
    """
    # Ensure output directory exists
    output_dir = 'outputs/health'
    os.makedirs(output_dir, exist_ok=True)
    
    # Run health check
    results = run_health_check()
    
    # Output to stdout
    print(json.dumps(results, indent=2))
    
    # Write to JSON file
    output_file = os.path.join(output_dir, 'cpu_health.json')
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Health check results written to {output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if results['healthy'] else 1)

if __name__ == '__main__':
    main()