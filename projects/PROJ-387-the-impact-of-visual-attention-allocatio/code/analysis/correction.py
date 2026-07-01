import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from statsmodels.stats.multitest import multipletests

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_project_root, get_output_path
from utils.logger import get_logger

logger = get_logger(__name__)

ASSOCIATION_LABEL = "associational"

def load_lmm_results(results_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load LMM results from JSON.
    """
    if results_path is None:
        output_dir = get_output_path()
        results_path = output_dir / "results" / "lmm_results.json"
    
    if not results_path.exists():
        logger.error(f"LMM results not found at {results_path}")
        raise FileNotFoundError(f"LMM results not found at {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def apply_bonferroni_correction(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to p-values.
    """
    # Extract valid p-values
    valid_results = [r for r in results if r.get('p_raw') is not None]
    
    if not valid_results:
        logger.warning("No valid p-values to correct")
        return results

    p_values = [r['p_raw'] for r in valid_results]
    n_tests = len(p_values)
    
    logger.info(f"Applying Bonferroni correction to {n_tests} tests")
    
    # statsmodels returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    # We use method='bonferroni'
    try:
        _, p_corrected, _, _ = multipletests(p_values, method='bonferroni')
    except Exception as e:
        logger.error(f"Correction failed: {e}")
        # Fallback: simple multiplication if statsmodels fails
        p_corrected = [min(p * n_tests, 1.0) for p in p_values]

    # Update results
    idx = 0
    for res in results:
        if res.get('p_raw') is not None:
            res['p_corrected'] = float(p_corrected[idx])
            res['association_label'] = ASSOCIATION_LABEL  # FR-005 Requirement
            idx += 1
        else:
            res['p_corrected'] = None
            res['association_label'] = ASSOCIATION_LABEL

    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Save corrected results to JSON.
    """
    if output_path is None:
        output_dir = get_output_path()
        output_path = output_dir / "results"
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / "correction_results.json"
    
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved correction results to {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Apply Multiple Comparison Correction to LMM Results")
    args = parser.parse_args()

    try:
        results = load_lmm_results()
        corrected_results = apply_bonferroni_correction(results)
        save_results(corrected_results)
        logger.info("Correction completed successfully.")
        sys.exit(0)
    except FileNotFoundError as e:
        logger.error(f"Input data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Correction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
