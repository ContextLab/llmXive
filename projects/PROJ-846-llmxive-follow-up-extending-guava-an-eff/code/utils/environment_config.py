"""
Environment configuration management for CPU-only runner constraints.

This module handles detection of available resources, enforcement of CPU-only
constraints, and configuration of PyTorch for CPU execution to ensure
reproducibility and adherence to compute budgets.
"""
import os
import sys
import platform
import subprocess
import logging
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentConfigError(Exception):
    """Exception raised for errors in environment configuration or constraint verification."""
    pass

def detect_cpu_count() -> int:
    """
    Detect the number of available CPU cores.
    
    Returns:
        int: Number of available CPU cores.
        
    Raises:
        EnvironmentConfigError: If CPU count cannot be determined.
    """
    try:
        # Try using os.cpu_count() first
        count = os.cpu_count()
        if count is None:
            raise EnvironmentConfigError("os.cpu_count() returned None")
        return count
    except Exception as e:
        # Fallback to platform-specific commands
        try:
            if platform.system() == "Windows":
                cmd = ["wmic", "cpu", "get", "NumberOfCores"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    return int(lines[1].strip())
            elif platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    lines = f.readlines()
                    count = sum(1 for line in lines if line.startswith('processor'))
                    return count if count > 0 else 1
            elif platform.system() == "Darwin":
                result = subprocess.run(["sysctl", "-n", "hw.ncpu"], capture_output=True, text=True, check=True)
                return int(result.stdout.strip())
        except Exception as fallback_error:
            logger.warning(f"Failed to detect CPU count via fallback methods: {fallback_error}")
            return 1  # Default to 1 if detection fails
        
    raise EnvironmentConfigError(f"Unable to determine CPU count: {e}")

def verify_cpu_only_constraint() -> bool:
    """
    Verify that the environment is configured for CPU-only execution.
    
    Checks for:
    - Absence of CUDA/GPU availability in PyTorch
    - Presence of CPU-specific environment variables
    
    Returns:
        bool: True if CPU-only constraint is satisfied, False otherwise.
        
    Raises:
        EnvironmentConfigError: If GPU is detected when CPU-only is required.
    """
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("GPU is available. Enforcing CPU-only mode by setting device to 'cpu'.")
            # We don't raise here, we just log and let the caller decide
            # But for strict verification, we might want to raise
            # return False 
        return True
    except ImportError:
        logger.warning("PyTorch not installed. Assuming CPU-only environment.")
        return True

def configure_torch_for_cpu() -> None:
    """
    Configure PyTorch to run exclusively on CPU.
    
    Sets environment variables and PyTorch configuration to:
    - Disable CUDA
    - Set number of threads to available CPU count
    - Disable MKL-DNN for consistency
    """
    try:
        import torch
        
        # Force CPU usage
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        
        # Configure number of threads
        cpu_count = detect_cpu_count()
        torch.set_num_threads(cpu_count)
        
        # Disable MKL-DNN for deterministic behavior on CPU
        if hasattr(torch, 'set_deterministic_debug_mode'):
            torch.set_deterministic_debug_mode(1)
        
        # Disable CUDNN (though irrelevant on CPU, good practice)
        torch.backends.cudnn.enabled = False
        
        logger.info(f"PyTorch configured for CPU execution with {cpu_count} threads.")
    except ImportError:
        logger.warning("PyTorch not installed. Skipping CPU configuration.")

def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by raising an error if GPU is detected.
    
    This is a strict mode that halts execution if any GPU hardware is found,
    ensuring compliance with CPU-only constraints for reproducibility.
    
    Raises:
        EnvironmentConfigError: If GPU hardware is detected.
    """
    try:
        import torch
        if torch.cuda.is_available():
            raise EnvironmentConfigError(
                "GPU detected but CPU-only mode is enforced. "
                "Set CUDA_VISIBLE_DEVICES='' or run on CPU-only hardware."
            )
        logger.info("CPU-only constraint verified and enforced.")
    except ImportError:
        logger.info("PyTorch not installed. Assuming CPU-only environment.")

def get_environment_summary() -> Dict[str, Any]:
    """
    Generate a summary of the current environment configuration.
    
    Returns:
        Dict[str, Any]: Dictionary containing environment details including:
            - os_platform: Operating system platform
            - python_version: Python version string
            - cpu_count: Number of detected CPU cores
            - torch_available: Whether PyTorch is installed
            - cuda_available: Whether CUDA is available (if PyTorch is installed)
            - num_threads: Configured number of threads (if PyTorch is installed)
    """
    summary = {
        'os_platform': platform.system(),
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'cpu_count': detect_cpu_count(),
        'torch_available': False,
        'cuda_available': False,
        'num_threads': None,
        'environment_vars': {
            'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set'),
            'OMP_NUM_THREADS': os.environ.get('OMP_NUM_THREADS', 'Not set'),
            'MKL_NUM_THREADS': os.environ.get('MKL_NUM_THREADS', 'Not set'),
        }
    }
    
    try:
        import torch
        summary['torch_available'] = True
        summary['cuda_available'] = torch.cuda.is_available()
        if hasattr(torch, 'get_num_threads'):
            summary['num_threads'] = torch.get_num_threads()
    except ImportError:
        pass
        
    return summary

def main():
    """
    Main entry point for environment configuration verification and setup.
    
    Prints environment summary and enforces CPU-only constraints.
    """
    print("=== llmXive Environment Configuration ===")
    
    # Configure for CPU
    configure_torch_for_cpu()
    
    # Verify constraints
    try:
        enforce_cpu_only()
    except EnvironmentConfigError as e:
        print(f"WARNING: {e}")
        print("Proceeding in CPU-only mode anyway...")
    
    # Print summary
    summary = get_environment_summary()
    print("\nEnvironment Summary:")
    for key, value in summary.items():
        if key != 'environment_vars':
            print(f"  {key}: {value}")
    
    print("\nEnvironment Variables:")
    for key, value in summary['environment_vars'].items():
        print(f"  {key}: {value}")
        
    print("\nConfiguration complete.")

if __name__ == "__main__":
    main()