"""
Task T1213: Audit code/cleanup_utils.py, code/profiler.py, and code/utils.py
to identify duplicate or overlapping functions.

Generates a diff report of overlapping functions in `data/processed/audit_report.json`.
"""
import json
import inspect
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple

# Import the real modules to inspect their public APIs
# We need to add the code directory to sys.path to import them correctly
import sys
from pathlib import Path

# Ensure we can import from the code directory
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import setup_logging, pin_random_seed, compute_file_checksum
from utils import profile_function, profile_block, run_cprofile
from utils import save_profile_report, identify_bottlenecks, reset_profile_data

# cleanup_utils and profiler are now stubs, but we check them for completeness
try:
    import cleanup_utils
    cleanup_utils_funcs = [name for name in dir(cleanup_utils) if not name.startswith('_')]
except ImportError:
    cleanup_utils_funcs = []

try:
    import profiler
    profiler_funcs = [name for name in dir(profiler) if not name.startswith('_')]
except ImportError:
    profiler_funcs = []

def get_public_functions(module: Any) -> Dict[str, str]:
    """Extract public function names and their signatures from a module."""
    functions = {}
    for name in dir(module):
        if name.startswith('_'):
            continue
        obj = getattr(module, name)
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            # Get signature string
            try:
                sig = str(inspect.signature(obj))
                functions[name] = sig
            except (ValueError, TypeError):
                functions[name] = "<uninspectable>"
    return functions

def find_duplicates(
    utils_funcs: Dict[str, str],
    cleanup_funcs: List[str],
    profiler_funcs: List[str]
) -> Dict[str, Any]:
    """Compare function sets and identify overlaps."""
    report = {
        "audit_summary": {
            "utils_module_functions": list(utils_funcs.keys()),
            "cleanup_utils_module_functions": cleanup_funcs,
            "profiler_module_functions": profiler_funcs
        },
        "overlaps": [],
        "consolidation_status": {}
    }

    # Check for functions in cleanup_utils that exist in utils
    for func_name in cleanup_funcs:
        if func_name in utils_funcs:
            report["overlaps"].append({
                "function": func_name,
                "source": "cleanup_utils.py (should be deleted)",
                "target": "utils.py (consolidated)",
                "status": "DUPLICATE_FOUND"
            })
        else:
            report["overlaps"].append({
                "function": func_name,
                "source": "cleanup_utils.py",
                "target": "NOT_FOUND_IN_UTILS",
                "status": "MISSING_IN_CONSOLIDATION"
            })

    # Check for functions in profiler that exist in utils
    for func_name in profiler_funcs:
        if func_name in utils_funcs:
            report["overlaps"].append({
                "function": func_name,
                "source": "profiler.py (should be deleted)",
                "target": "utils.py (consolidated)",
                "status": "DUPLICATE_FOUND"
            })
        else:
            report["overlaps"].append({
                "function": func_name,
                "source": "profiler.py",
                "target": "NOT_FOUND_IN_UTILS",
                "status": "MISSING_IN_CONSOLIDATION"
            })

    # Verify expected utilities are present in utils
    expected_utils = [
        "setup_logging", "pin_random_seed", "compute_file_checksum",
        "profile_function", "profile_block", "run_cprofile",
        "save_profile_report", "identify_bottlenecks", "reset_profile_data"
    ]
    
    missing_in_utils = []
    for func_name in expected_utils:
        if func_name not in utils_funcs:
            missing_in_utils.append(func_name)
    
    report["consolidation_status"] = {
        "all_expected_functions_present": len(missing_in_utils) == 0,
        "missing_functions": missing_in_utils,
        "cleanup_utils_is_stub": len(cleanup_funcs) == 0 or cleanup_funcs == ['pass'],
        "profiler_is_stub": len(profiler_funcs) == 0 or profiler_funcs == ['pass']
    }

    return report

def main():
    """Run the audit and write the report."""
    logger = setup_logging("INFO")
    logger.info("Starting T1213: Audit utility modules for duplicates")

    # Get functions from utils
    utils_funcs = get_public_functions(sys.modules['utils'])
    logger.info(f"Found {len(utils_funcs)} public functions in utils.py")

    # Get functions from stubs
    cleanup_funcs = cleanup_utils_funcs
    profiler_funcs = profiler_funcs

    logger.info(f"Found {len(cleanup_funcs)} items in cleanup_utils.py")
    logger.info(f"Found {len(profiler_funcs)} items in profiler.py")

    # Generate report
    report = find_duplicates(utils_funcs, cleanup_funcs, profiler_funcs)

    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "audit_report.json"

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Audit report written to {output_path}")
    logger.info(f"Overlaps found: {len(report['overlaps'])}")
    
    if report['consolidation_status']['all_expected_functions_present']:
        logger.info("SUCCESS: All expected functions are present in utils.py")
    else:
        logger.warning(f"WARNING: Missing functions in utils.py: {report['consolidation_status']['missing_functions']}")

    return report

if __name__ == "__main__":
    main()