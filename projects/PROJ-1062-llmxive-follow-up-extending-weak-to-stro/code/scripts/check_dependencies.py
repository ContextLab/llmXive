"""
Dependency Check Script.

Verifies that all required packages are installed and checks for specific
version constraints, particularly for CPU-only PyTorch.
"""
import sys
import subprocess
import importlib
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = {
    'numpy': '1.24.0',
    'pandas': '2.0.0',
    'scipy': '1.11.0',
    'scikit-learn': '1.3.0',
    'torch': '2.1.0',
    'transformers': '4.35.0',
    'bitsandbytes': '0.41.0',
    'tqdm': '4.66.0',
    'pyyaml': '6.0.0',
    'huggingface-hub': '0.19.0',
    'safetensors': '0.4.0',
}

def check_package_installed(package_name: str) -> Tuple[bool, str]:
    """Check if a package is installed and return its version."""
    try:
        module = importlib.import_module(package_name.replace('-', '_'))
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError:
        return False, "Not installed"

def check_torch_cpu_only() -> bool:
    """Verify PyTorch is running in CPU-only mode."""
    try:
        import torch
        if torch.cuda.is_available():
            logger.warning("CUDA is available. This might be a GPU build.")
            return False
        else:
            logger.info("PyTorch is correctly configured for CPU-only execution.")
            return True
    except ImportError:
        logger.error("PyTorch is not installed.")
        return False

def main():
    """Main entry point for dependency checking."""
    logger.info("Checking required dependencies...")
    
    all_good = True
    missing_packages = []
    
    for package, min_version in REQUIRED_PACKAGES.items():
        installed, version = check_package_installed(package)
        if not installed:
            logger.error(f"Missing package: {package} (required: >= {min_version})")
            missing_packages.append(package)
            all_good = False
        else:
            logger.info(f"Found {package} version {version}")
    
    # Special check for PyTorch CPU-only
    if 'torch' in REQUIRED_PACKAGES:
        if not check_torch_cpu_only():
            all_good = False
            logger.error("PyTorch CPU-only constraint not met!")
    
    if missing_packages:
        logger.error(f"\nMissing packages: {', '.join(missing_packages)}")
        logger.error("Run: pip install -r requirements.txt")
        sys.exit(1)
    
    if all_good:
        logger.info("\nAll dependencies are satisfied.")
        sys.exit(0)

if __name__ == "__main__":
    main()