"""
Import verification utility for llmXive project.

This module verifies that all imports in the codebase are valid and that there are
no circular dependencies that would prevent the modules from being imported.

Usage:
    python -m code.utils.import_check
"""

import sys
import importlib
from pathlib import Path
from typing import List, Set, Dict, Tuple

# Define the modules to check based on the project structure
MODULES_TO_CHECK = [
    "main",
    "00_data_generation",
    "00_data_extraction",
    "00_teacher_inference",
    "00_validate_sources",
    "01_train_trees",
    "02_evaluate_fidelity",
    "030_compute_fidelity_metrics",
    "03_versioning",
    "_data_streaming",
    "setup_data_dirs",
    "statistics_runner",
    "models.inference",
    "utils.config",
    "utils.check_weights",
    "utils.cleanup_unused_imports",
    "utils.metrics",
    "utils.statistics",
]

def check_module_imports(module_name: str) -> Tuple[bool, str]:
    """
    Check if a module can be imported successfully.
    
    Args:
        module_name: The name of the module to check.
        
    Returns:
        A tuple (success, message) where success is True if the import succeeded.
    """
    try:
        importlib.import_module(module_name)
        return True, f"Successfully imported {module_name}"
    except ImportError as e:
        return False, f"Failed to import {module_name}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error importing {module_name}: {str(e)}"

def run_import_check() -> bool:
    """
    Run import checks on all specified modules.
    
    Returns:
        True if all imports succeeded, False otherwise.
    """
    print("Starting import verification for llmXive project...")
    print("=" * 60)
    
    all_success = True
    results: Dict[str, Tuple[bool, str]] = {}
    
    for module_name in MODULES_TO_CHECK:
        success, message = check_module_imports(module_name)
        results[module_name] = (success, message)
        status = "✓" if success else "✗"
        print(f"{status} {module_name}: {message}")
        if not success:
            all_success = False
    
    print("=" * 60)
    if all_success:
        print("All imports verified successfully. No circular dependencies detected.")
        return True
    else:
        print("Some imports failed. Please check the errors above.")
        return False

def main():
    """Main entry point for the import check utility."""
    success = run_import_check()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()