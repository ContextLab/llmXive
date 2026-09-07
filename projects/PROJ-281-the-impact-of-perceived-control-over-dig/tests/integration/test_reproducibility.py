"""
Integration test for reproducibility audit (T044).

This script re-runs the statistical analysis pipeline with fixed seeds
and verifies that `data/processed/analysis_results.json` produces identical results
across two consecutive runs, satisfying SC-005.
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import pytest
import numpy as np
import pandas as pd

# Ensure project root is in path for imports
import sys
from pathlib import Path as PathLib
project_root = PathLib(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import CONFIG, set_seed, reset_seeds
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.services.merge_and_save import run_merge_and_save_pipeline
from code.services.scoring_saver import run_scoring_saver_pipeline
from code.services.proxy_saver import run_proxy_saver_pipeline


class ReproducibilityError(Exception):
    """Raised when reproducibility check fails."""
    pass


def load_json_results(filepath: Path) -> Dict[str, Any]:
    """Load and return JSON results."""
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)


def compare_results(run1_results: Dict[str, Any], run2_results: Dict[str, Any], tolerance: float = 1e-9) -> bool:
    """
    Compare two result dictionaries for numerical equality within tolerance.
    
    Args:
        run1_results: Results from first run
        run2_results: Results from second run
        tolerance: Maximum allowed difference for floating point numbers
        
    Returns:
        True if results are identical within tolerance, False otherwise
    """
    # Check that both have the same keys
    if set(run1_results.keys()) != set(run2_results.keys()):
        return False
    
    for key in run1_results.keys():
        val1 = run1_results[key]
        val2 = run2_results[key]
        
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if abs(val1 - val2) > tolerance:
                return False
        elif isinstance(val1, bool) and isinstance(val2, bool):
            if val1 != val2:
                return False
        elif isinstance(val1, str) and isinstance(val2, str):
            if val1 != val2:
                return False
        elif isinstance(val1, dict) and isinstance(val2, dict):
            if not compare_results(val1, val2, tolerance):
                return False
        else:
            # For other types, use direct comparison
            if val1 != val2:
                return False
    
    return True


@pytest.mark.integration
def test_reproducibility_fixed_seeds():
    """
    Test that running the pipeline twice with the same seed produces identical results.
    
    This test:
    1. Saves existing data files (if any)
    2. Runs the pipeline with a fixed seed
    3. Saves the first run's results
    4. Resets seeds and runs again
    5. Compares results to ensure they are identical
    6. Restores original data (if any)
    """
    # Configuration
    seed_value = 42
    results_file = CONFIG.PROCESSED_DIR / "analysis_results.json"
    final_analysis_file = CONFIG.PROCESSED_DIR / "final_analysis.csv"
    scoring_results_file = CONFIG.PROCESSED_DIR / "scoring_results.csv"
    proxy_results_file = CONFIG.PROCESSED_DIR / "proxy_results.csv"
    
    # Backup existing files if they exist
    backups = {}
    for filepath in [results_file, final_analysis_file, scoring_results_file, proxy_results_file]:
        if filepath.exists():
            backup_path = filepath.with_suffix(filepath.suffix + '.backup')
            shutil.copy2(filepath, backup_path)
            backups[filepath] = backup_path
    
    try:
        # Ensure processed directory exists
        CONFIG.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        # --- Run 1 ---
        print(f"\n=== Running Reproducibility Check - Run 1 (seed={seed_value}) ===")
        set_seed(seed_value)
        
        # Run the full pipeline (or at least the parts that lead to analysis_results.json)
        # We need to ensure all upstream steps are reproducible too
        run_scoring_saver_pipeline()
        run_proxy_saver_pipeline()
        run_merge_and_save_pipeline()
        run_statistical_analysis_pipeline()
        
        # Verify results file was created
        if not results_file.exists():
            raise ReproducibilityError(f"Run 1: Results file not created at {results_file}")
        
        run1_results = load_json_results(results_file)
        print(f"Run 1 results: correlation={run1_results.get('correlation_coefficient')}, "
              f"p_value={run1_results.get('p_value')}, is_significant={run1_results.get('is_significant')}")
        
        # --- Run 2 ---
        print(f"\n=== Running Reproducibility Check - Run 2 (seed={seed_value}) ===")
        reset_seeds()
        set_seed(seed_value)
        
        # Run the pipeline again
        run_scoring_saver_pipeline()
        run_proxy_saver_pipeline()
        run_merge_and_save_pipeline()
        run_statistical_analysis_pipeline()
        
        # Verify results file was created
        if not results_file.exists():
            raise ReproducibilityError(f"Run 2: Results file not created at {results_file}")
        
        run2_results = load_json_results(results_file)
        print(f"Run 2 results: correlation={run2_results.get('correlation_coefficient')}, "
              f"p_value={run2_results.get('p_value')}, is_significant={run2_results.get('is_significant')}")
        
        # --- Compare Results ---
        print("\n=== Comparing Results ===")
        if not compare_results(run1_results, run2_results):
            # Detailed comparison for debugging
            print("Results differ:")
            for key in set(run1_results.keys()) | set(run2_results.keys()):
                val1 = run1_results.get(key, "MISSING")
                val2 = run2_results.get(key, "MISSING")
                if val1 != val2:
                    print(f"  {key}: {val1} vs {val2}")
            raise ReproducibilityError(
                f"Reproducibility check failed: Results differ between runs with fixed seed {seed_value}. "
                f"Run 1: {run1_results}, Run 2: {run2_results}"
            )
        
        print("✓ Reproducibility check PASSED: Identical results across runs with fixed seed.")
        
    finally:
        # Restore original files if they existed
        for filepath, backup_path in backups.items():
            if backup_path.exists():
                shutil.move(backup_path, filepath)
                print(f"Restored {filepath} from backup")


if __name__ == "__main__":
    # Allow running as a script
    pytest.main([__file__, "-v", "-s"])
