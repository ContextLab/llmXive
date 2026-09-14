import sys
import subprocess
import importlib
import logging
from pathlib import Path

def check_package_installed(package_name):
    """
    Checks if a Python package is installed.
    """
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def check_torch_cpu_only():
    """
    Checks if torch is installed without CUDA support (CPU-only).
    """
    try:
        import torch
        if torch.cuda.is_available():
            return False
        else:
            return True
    except ImportError:
        return False

def main():
    """
    Main function to check dependencies.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    required_packages = ["transformers", "scikit-learn", "scipy", "pandas", "numpy", "torch", "bitsandbytes"]

    for package in required_packages:
        if not check_package_installed(package):
            logging.error(f"Package '{package}' is not installed.")
            sys.exit(1)

    if not check_torch_cpu_only():
        logging.error("Torch is installed with CUDA support. CPU-only build is required.")
        sys.exit(1)

    logging.info("All dependencies are satisfied.")

if __name__ == "__main__":
    main()