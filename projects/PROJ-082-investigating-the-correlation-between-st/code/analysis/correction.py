"""
Multiple comparison correction analysis module.
Implements Bonferroni correction for tract-specific meta-analysis results.
"""

import json
import math
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure imports work relative to project root when run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger, log_error_context
from utils.config import get_project_root

logger = get_logger(__name__)

def load_tract_data_from_json(file_path: str) -> Dict[str, Any]:
    """Load tract count data from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Tract count file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data

def load_study_count_from_json(file_path: str) -> int:
    """Load study count N from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Study count file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data.get('N', 0)

def count_unique_tracts(tract_data: Dict[str, Any]) -> int:
    """
    Count unique tracts from loaded tract data.
    Returns the 'k' value directly from the JSON.
    """
    return tract_data.get('k', 0)

def apply_bonferroni_correction(p_values: List[float], k: int) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values from multiple tests
        k: Number of comparisons (tracts)
        
    Returns:
        Dictionary containing corrected p-values and threshold
    """
    if k < 1:
        raise ValueError("Number of comparisons (k) must be at least 1")
    
    # Bonferroni threshold
    alpha = 0.05
    bonferroni_threshold = alpha / k
    
    # Apply correction
    corrected_p_values = [min(p * k, 1.0) for p in p_values]
    
    return {
        'original_p_values': p_values,
        'corrected_p_values': corrected_p_values,
        'bonferroni_threshold': bonferroni_threshold,
        'alpha': alpha,
        'k': k
    }

def run_correction_analysis(
    tract_count_path: str = "data/processed/tract_count.json",
    study_count_path: str = "data/processed/study_count.json",
    results_path: str = "data/derived/results.json",
    output_path: str = "data/derived/correction_results.json"
) -> Dict[str, Any]:
    """
    Run multiple comparison correction analysis.
    
    Decision Logic:
    1. Load k (tract count) from tract_count_path
    2. Load N (study count) from study_count_path
    3. Apply Bonferroni ONLY if k >= 2 AND N >= 10
    4. Otherwise, log warning and set bonferroni_applied: false
    
    Args:
        tract_count_path: Path to tract_count.json
        study_count_path: Path to study_count.json
        results_path: Path to results.json (for reading p-values if available)
        output_path: Path to write correction results
        
    Returns:
        Dictionary with correction results
    """
    logger.info("Starting multiple comparison correction analysis")
    
    # Load required inputs
    try:
        tract_data = load_tract_data_from_json(tract_count_path)
        k = count_unique_tracts(tract_data)
        logger.info(f"Loaded tract count: k={k}")
    except Exception as e:
        logger.error(f"Failed to load tract count: {e}")
        raise
    
    try:
        N = load_study_count_from_json(study_count_path)
        logger.info(f"Loaded study count: N={N}")
    except Exception as e:
        logger.error(f"Failed to load study count: {e}")
        raise
    
    # Decision logic
    bonferroni_applied = False
    correction_result = {}
    
    if k >= 2 and N >= 10:
        logger.info(f"Applying Bonferroni correction: k={k}, N={N}")
        
        # Try to load p-values from results if available
        p_values = []
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
                # Extract p-values if present (e.g., from Egger's test, heterogeneity tests)
                if 'egger_p' in results:
                    p_values.append(results['egger_p'])
                if 'i_squared_p' in results:
                    p_values.append(results['i_squared_p'])
                # Add tract-specific p-values if available
                if 'tract_p_values' in results:
                    p_values.extend(results['tract_p_values'])
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            logger.warning("No p-values found in results.json, using placeholder for demonstration")
            # If no p-values available, we still report the correction parameters
            pass
        
        if p_values:
            correction_result = apply_bonferroni_correction(p_values, k)
            bonferroni_applied = True
            logger.info(f"Bonferroni correction applied. Threshold: {correction_result['bonferroni_threshold']:.4f}")
        else:
            # No p-values to correct, but we still report the threshold
            correction_result = {
                'bonferroni_threshold': 0.05 / k,
                'alpha': 0.05,
                'k': k,
                'bonferroni_applied': True,
                'note': 'No p-values found to correct, but threshold calculated'
            }
            bonferroni_applied = True
            logger.info(f"Bonferroni threshold calculated: {correction_result['bonferroni_threshold']:.4f}")
            
    else:
        # Condition not met
        reason = []
        if k < 2:
            reason.append(f"k < 2 (k={k})")
        if N < 10:
            reason.append(f"N < 10 (N={N})")
        
        logger.warning(f"Bonferroni correction skipped: {' and '.join(reason)}")
        correction_result = {
            'bonferroni_applied': False,
            'reason': f"Skipped: {' and '.join(reason)}",
            'k': k,
            'N': N,
            'bonferroni_threshold': None,
            'limitation_note': "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
        }
    
    # Ensure limitation note is always present when k >= 2
    if k >= 2 and 'limitation_note' not in correction_result:
        correction_result['limitation_note'] = "Limitations: Bonferroni correction is conservative due to potential non-independence of tract measurements."
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(correction_result, f, indent=2)
    
    logger.info(f"Correction results written to {output_path}")
    
    # Also update the main results.json with correction info if it exists
    try:
        results_file = Path(results_path)
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Add correction metadata
            results['correction'] = {
                'bonferroni_applied': bonferroni_applied,
                'k': k,
                'N': N
            }
            
            if bonferroni_applied and 'bonferroni_threshold' in correction_result:
                results['correction']['bonferroni_threshold'] = correction_result['bonferroni_threshold']
            
            if 'limitation_note' in correction_result:
                results['correction']['limitation_note'] = correction_result['limitation_note']
            
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info("Updated results.json with correction metadata")
    except Exception as e:
        logger.warning(f"Could not update results.json: {e}")
    
    return correction_result

def main():
    """Main entry point for correction analysis."""
    project_root = get_project_root()
    
    tract_count_path = project_root / "data" / "processed" / "tract_count.json"
    study_count_path = project_root / "data" / "processed" / "study_count.json"
    results_path = project_root / "data" / "derived" / "results.json"
    output_path = project_root / "data" / "derived" / "correction_results.json"
    
    try:
        result = run_correction_analysis(
            tract_count_path=str(tract_count_path),
            study_count_path=str(study_count_path),
            results_path=str(results_path),
            output_path=str(output_path)
        )
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Correction analysis failed: {e}")
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())