import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Import shared utilities from sibling modules to maintain API consistency
from analysis.bias import load_study_count_from_json, load_effect_sizes_and_se
from utils.logger import get_logger, log_error_context

logger = get_logger(__name__)

# Constants
DEFAULT_ALPHA = 0.05

def load_tract_data_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load the list of tract-specific effect sizes from the meta-analysis output JSON.
    Expects the JSON to have a 'results' or 'tracts' key containing the list of studies/tracks.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Attempt to find the list of results. The structure depends on T014 output.
    # Assuming T014 outputs a list under 'results' or 'tract_results'.
    results = data.get('results') or data.get('tract_results') or data.get('studies')
    
    if not results:
        logger.warning("No tract data found in input JSON. Assuming empty result set.")
        return []
    
    return results

def count_unique_tracts(tract_data: List[Dict[str, Any]]) -> int:
    """
    Count the number of unique tracts in the provided data.
    """
    if not tract_data:
        return 0
    
    tracts = set()
    for item in tract_data:
        # Expecting a key like 'tract_name', 'tract', or 'id'
        name = item.get('tract_name') or item.get('tract') or item.get('id')
        if name:
            tracts.add(str(name))
    
    return len(tracts)

def apply_bonferroni_correction(p_values: List[float], k: int) -> List[Tuple[float, float]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        k: Number of comparisons (number of tracts).
    
    Returns:
        List of tuples (adjusted_p_value, is_significant_at_0.05).
        Adjusted p-value is min(p * k, 1.0).
    """
    if k == 0:
        return []
    
    adjusted_results = []
    for p in p_values:
        # Cap at 1.0
        adjusted_p = min(p * k, 1.0)
        is_significant = adjusted_p < DEFAULT_ALPHA
        adjusted_results.append((adjusted_p, is_significant))
    
    return adjusted_results

def run_correction_analysis(
    input_json_path: Path,
    output_json_path: Path
) -> Dict[str, Any]:
    """
    Main function to run the multiple comparison correction.
    
    Logic:
    1. Load study_count from T014 output (or the same input JSON if it contains it).
    2. If study_count < 10, skip correction and set narrative mode flag.
    3. Load tract data to determine k (number of tracts).
    4. If k < 2, skip correction (no multiple comparisons to make).
    5. If N >= 10 and k >= 2, apply Bonferroni correction.
    6. Write results to output JSON.
    
    Returns:
        Dictionary containing the correction results.
    """
    logger.info(f"Starting correction analysis on {input_json_path}")
    
    # 1. Load study count
    # We reuse the helper from bias.py to ensure consistency in reading the count
    try:
        study_count = load_study_count_from_json(input_json_path)
    except Exception as e:
        logger.error(f"Failed to load study count: {e}")
        study_count = 0

    # 2. Check N < 10 condition
    if study_count < 10:
        logger.info(f"Study count ({study_count}) < 10. Skipping correction (Narrative Mode).")
        result = {
            "correction_mode": "skipped_narrative",
            "reason": "Insufficient studies (N < 10) for quantitative correction.",
            "study_count": study_count,
            "adjusted_threshold": None,
            "results": [],
            "limitations": "Quantitative correction skipped due to low study count. Narrative synthesis recommended."
        }
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        return result

    # 3. Load tract data and count unique tracts (k)
    tract_data = load_tract_data_from_json(input_json_path)
    k = count_unique_tracts(tract_data)

    # 4. Check k < 2 condition
    if k < 2:
        logger.info(f"Unique tract count ({k}) < 2. Skipping correction (No multiple comparisons).")
        result = {
            "correction_mode": "skipped_single_comparison",
            "reason": "Only one tract or no tracts found. Bonferroni correction not applicable.",
            "study_count": study_count,
            "tract_count": k,
            "adjusted_threshold": DEFAULT_ALPHA,
            "results": [],
            "limitations": "Correction skipped as there is only a single comparison."
        }
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        return result

    # 5. Perform Bonferroni Correction
    logger.info(f"Applying Bonferroni correction: N={study_count}, k={k}")
    
    # Extract p-values. Assuming the input JSON has a 'p_value' or 'p' key per item.
    p_values = []
    for item in tract_data:
        p = item.get('p_value') or item.get('p')
        if p is not None:
            p_values.append(float(p))
    
    if not p_values:
        logger.warning("No p-values found in tract data to correct.")
        result = {
            "correction_mode": "no_data",
            "reason": "No p-values found in input data.",
            "study_count": study_count,
            "tract_count": k,
            "adjusted_threshold": DEFAULT_ALPHA,
            "results": [],
            "limitations": "No p-values available for correction."
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        return result

    adjusted_results = apply_bonferroni_correction(p_values, k)
    adjusted_threshold = DEFAULT_ALPHA / k

    # Construct output results
    output_results = []
    for i, (adj_p, sig) in enumerate(adjusted_results):
        # Map back to original item if possible, or just index
        original_item = tract_data[i] if i < len(tract_data) else {}
        output_results.append({
            "original_p_value": p_values[i],
            "adjusted_p_value": round(adj_p, 6),
            "is_significant": sig,
            "tract_name": original_item.get('tract_name', original_item.get('tract', f"tract_{i}"))
        })

    result = {
        "correction_mode": "bonferroni",
        "study_count": study_count,
        "tract_count": k,
        "adjusted_threshold": round(adjusted_threshold, 6),
        "results": output_results,
        "limitations": (
            "Bonferroni correction is conservative and assumes independence of tests. "
            "Since brain tracts are anatomically and functionally correlated, "
            "the true family-wise error rate may be lower than estimated here, "
            "potentially leading to an increased Type II error rate (false negatives)."
        )
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Correction analysis complete. Results written to {output_json_path}")
    return result

def main():
    """
    CLI entry point for correction analysis.
    Expects --input and --output arguments.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to meta-analysis results.")
    parser.add_argument("--input", type=Path, required=True, help="Path to input meta-analysis JSON (from T014).")
    parser.add_argument("--output", type=Path, required=True, help="Path to output correction JSON.")
    
    args = parser.parse_args()

    try:
        run_correction_analysis(args.input, args.output)
        print(f"Correction analysis completed successfully. Output: {args.output}")
    except Exception as e:
        logger.error(f"Correction analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()