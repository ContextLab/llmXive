"""
Import verification utility for llmXive project.

This module provides functionality to verify that all code modules
in the project can be imported without ImportError, specifically
checking for circular dependencies and missing imports.
"""
import sys
import importlib
from pathlib import Path
from typing import List, Set, Dict, Tuple


def check_module_imports(module_name: str, base_path: Path) -> Tuple[bool, str]:
    """
    Check if a specific module can be imported successfully.
    
    Args:
        module_name: The name of the module to check (e.g., 'code.main' or 'main')
        base_path: The root path to add to sys.path for imports
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Ensure base_path is in sys.path
        if str(base_path) not in sys.path:
            sys.path.insert(0, str(base_path))
        
        # Attempt to import the module
        importlib.import_module(module_name)
        return True, f"Successfully imported {module_name}"
    except ImportError as e:
        return False, f"ImportError for {module_name}: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error importing {module_name}: {str(e)}"


def run_import_check() -> Dict[str, bool]:
    """
    Run import checks on all major modules in the code directory.
    
    Returns:
        Dictionary mapping module names to their import success status
    """
    # Define the modules to check based on the project structure
    modules_to_check = [
        'main',
        '00_data_generation',
        '00_data_extraction',
        '00_teacher_inference',
        '00_validate_sources',
        '01_train_trees',
        '02_evaluate_fidelity',
        '02_evaluate_fidelity_parallel',
        '030_compute_fidelity_metrics',
        '03_versioning',
        '_data_streaming',
        'setup_data_dirs',
        'statistics_runner',
        'validate_sources',
        'models.inference',
        'utils.config',
        'utils.check_weights',
        'utils.import_check',
        'utils.memory_profiler',
        'utils.metrics',
        'utils.statistics',
        'utils.batch_processor',
        'utils.cleanup_unused_imports',
        'utils.vulture_runner',
    ]
    
    base_path = Path(__file__).parent.parent
    results: Dict[str, bool] = {}
    
    # Add base path to sys.path if not already present
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
    
    for module_name in modules_to_check:
        success, message = check_module_imports(module_name, base_path)
        results[module_name] = success
        status = "✓" if success else "✗"
        print(f"{status} {module_name}: {message}")
        
    return results


def main() -> int:
    """
    Main entry point for the import check script.
    
    Returns:
        Exit code: 0 if all imports succeed, 1 if any fail
    """
    print("Running import checks for llmXive project...")
    print("=" * 50)
    
    results = run_import_check()
    
    print("=" * 50)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"✓ All {total} modules imported successfully.")
        return 0
    else:
        failed = total - passed
        print(f"✗ {failed} of {total} modules failed to import.")
        print("\nFailed modules:")
        for module, success in results.items():
            if not success:
                print(f"  - {module}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
