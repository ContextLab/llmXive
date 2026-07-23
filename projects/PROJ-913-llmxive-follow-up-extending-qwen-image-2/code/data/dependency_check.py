import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("dependency_check")

def check_package_versions() -> Dict[str, Any]:
    """
    Checks installed versions of critical packages.
    """
    packages = {
        "diffusers": None,
        "transformers": None,
        "torch": None,
        "pandas": None,
        "numpy": None,
        "datasets": None,
    }
    
    results = {}
    for pkg_name in packages:
        try:
            module = __import__(pkg_name)
            version = getattr(module, "__version__", "unknown")
            results[pkg_name] = {"installed": True, "version": version}
        except ImportError:
            results[pkg_name] = {"installed": False, "version": None}
    
    return results

def check_model_config_ops(model_id: str) -> bool:
    """
    Placeholder for checking if specific ops are required by the model config.
    Returns True if safe, False if unlisted ops are detected.
    """
    logger.info(f"Checking ops for {model_id}")
    # In a real implementation, this would load the config and inspect architecture
    return True

def run_dependency_check(model_id: Optional[str] = None) -> bool:
    """
    Runs the full dependency check.
    """
    logger.info("Running dependency check...")
    versions = check_package_versions()
    
    critical = ["diffusers", "transformers", "torch"]
    missing = [k for k, v in versions.items() if k in critical and not v["installed"]]
    
    if missing:
        logger.error(f"Missing critical packages: {missing}")
        return False
    
    if model_id:
        if not check_model_config_ops(model_id):
            logger.error(f"Model {model_id} requires unlisted ops.")
            return False
    
    logger.info("Dependency check passed.")
    return True

def main():
    if not run_dependency_check():
        sys.exit(1)

if __name__ == "__main__":
    main()
