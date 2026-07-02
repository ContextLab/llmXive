import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.config import get_project_root
from utils.logger import get_logger
from analysis.lmm_model import ASSOCIATION_LABEL

logger = get_logger(__name__)

def load_lmm_results(input_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load LMM results from a CSV file.
    """
    root = get_project_root()
    if input_path is None:
        input_path = str(root / "output" / "results" / "lmm_summary.csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"LMM results file not found at {input_path}")
    
    import pandas as pd
    df = pd.read_csv(input_path)
    results = df.to_dict(orient='records')
    
    # Ensure association label is present (sanity check)
    for res in results:
        if 'association_label' not in res:
            res['association_label'] = ASSOCIATION_LABEL
            
    return results

def apply_bonferroni_correction(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction to p-values.
    Correction factor = number of tests (9 combinations).
    """
    n_tests = len(results)
    if n_tests == 0:
        return []
    
    corrected_results = []
    for res in results:
        p_raw = res.get('p_raw', 1.0)
        p_corrected = min(p_raw * n_tests, 1.0)
        
        new_res = res.copy()
        new_res['p_corrected'] = p_corrected
        new_res['association_label'] = ASSOCIATION_LABEL  # Ensure label is preserved
        corrected_results.append(new_res)
        
    logger.info(f"Applied Bonferroni correction for {n_tests} tests.")
    return corrected_results

def save_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Save corrected results to JSON.
    """
    root = get_project_root()
    if output_path is None:
        output_path = str(root / "output" / "results" / "correction_results.json")
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Saved correction results to {output_path}")
    return output_path

def main():
    """
    Main entry point for correction script.
    """
    parser = argparse.ArgumentParser(description="Apply Bonferroni Correction to LMM Results")
    parser.add_argument("--input", type=str, help="Path to input LMM results CSV", default=None)
    parser.add_argument("--output", type=str, help="Path to output JSON", default=None)
    args = parser.parse_args()

    logger.info("Starting Correction...")
    
    try:
        results = load_lmm_results(args.input)
        corrected = apply_bonferroni_correction(results)
        save_results(corrected, args.output)
        logger.info("Correction complete.")
        return 0
    except Exception as e:
        logger.error(f"Correction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
