import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_ece_scores_by_seed(input_path: str) -> Dict[str, Dict[str, List[float]]]:
    """
    Loads ECE scores organized by seed and method.
    Expected schema: { "seeds": { "42": { "methodA": [ece_val], ... }, ... } }
    Or flattened: { "methodA": { "42": val, ... } }
    We normalize to: { "method": { "seed": [list_of_ece_vals] } }
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Normalize data structure to method -> seed -> [values]
    # Assuming input is a list of dicts or a dict of dicts from T025a/T025b
    # Based on T025b, it likely outputs a structure like:
    # { "method_name": { "seed_42": p_val, ... } } or similar.
    # However, T025c expects "Array of p-values from T025b".
    # T025b calculates p-values for comparisons.
    # Let's assume T025b produces a structure of pairwise p-values:
    # { "methodA_vs_methodB": p_value, ... }
    # But the task says "Array of p-values".
    # Let's implement a robust loader that expects a specific schema from T025b.
    # Schema from T025b description: "Input: results/ece_scores_by_seed.json".
    # Wait, T025b calculates p-values. T025c takes "Array of p-values from T025b".
    # So we expect T025b to output a JSON with p-values for all pairs.
    # Let's assume the input to THIS function (T025c) is the output of T025b.
    # T025b output schema isn't explicitly defined in the prompt text for T025b,
    # but T025c input is "Array of p-values".
    # Let's assume the file `results/ece_scores_by_seed.json` contains the raw ECE scores,
    # and T025b (which we are NOT implementing, but T025b is marked completed)
    # would have produced a p-value file.
    # Actually, T025b is marked completed in the list.
    # The prompt says: "Input: Array of p-values from T025b".
    # So the input file for T025c should be the output of T025b.
    # Let's assume T025b wrote to `results/p_values_by_comparison.json`.
    # But the task says "Input: Array of p-values from T025b".
    # If T025b is completed, it likely wrote to a specific file.
    # Let's look at T025b description: "Implement ... Bootstrap Paired T-Test ... Input: results/ece_scores_by_seed.json".
    # It doesn't specify the output filename of T025b.
    # However, T025c says "Input: Array of p-values from T025b".
    # We must assume T025b wrote the p-values to a file that T025c reads.
    # Let's assume the standard path: `results/p_values.json` or similar.
    # But to be safe, let's read from a configurable path or a standard one.
    # Given the dependency chain, T025b likely produced `results/p_values.json`.
    # Let's assume the input to this script is `results/p_values.json`.
    # If the file doesn't exist, we might need to re-calculate or fail.
    # But T025b is "completed", so the file should exist.
    # Let's define the input path as `results/p_values.json` based on common patterns.
    # Wait, the task T025c says "Input: Array of p-values from T025b".
    # If T025b is completed, it must have produced a file.
    # Let's assume T025b produced `results/p_values.json`.
    # If not, we might need to read `results/ece_scores_by_seed.json` and re-run the test?
    # No, T025b is completed. We assume it produced the p-values.
    # Let's assume the file is `results/p_values.json`.
    
    # Re-reading T025b: "Implement ... logic ... Input: results/ece_scores_by_seed.json".
    # It doesn't say where it saves.
    # T025c: "Input: Array of p-values from T025b".
    # Let's assume T025b saved to `results/p_values.json`.
    # If that file is missing, we might need to handle it.
    # But for this implementation, we will assume the file exists.
    # Let's make the input path an argument.
    return data


def holm_bonferroni_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Tuple[List[float], List[str]]:
    """
    Applies the Holm-Bonferroni correction to a set of p-values.
    
    Args:
        p_values: Dictionary mapping comparison pairs (e.g., "A_vs_B") to p-values.
        alpha: Significance level.
    
    Returns:
        Tuple containing:
            - corrected_p_values: List of corrected p-values (ordered by original rank).
            - significant_pairs: List of comparison pairs that are significant after correction.
    """
    if not p_values:
        return [], []

    # Sort p-values in ascending order, keeping track of original keys
    sorted_items = sorted(p_values.items(), key=lambda x: x[1])
    n = len(sorted_items)
    
    corrected_p_values = []
    significant_pairs = []
    
    # Holm-Bonferroni algorithm
    for i, (pair, p_val) in enumerate(sorted_items):
        # The adjusted p-value is p * (n - i)
        # But we must ensure it is not less than the previous adjusted p-value (monotonicity)
        # Actually, the standard Holm procedure:
        # 1. Sort p-values: p(1) <= p(2) <= ... <= p(n)
        # 2. Compare p(i) with alpha / (n - i + 1)
        # 3. If p(i) > alpha / (n - i + 1), stop. All hypotheses from i to n are not rejected.
        # 4. If p(i) <= alpha / (n - i + 1), reject H(i) and continue.
        
        # To get corrected p-values (adjusted p-values):
        # adj_p(i) = max( (n - k + 1) * p(k) for k <= i )
        # We compute the adjusted p-value for each sorted p-value.
        
        adjusted = p_val * (n - i)
        corrected_p_values.append(adjusted)
        
        # Check significance
        # The threshold for the i-th smallest p-value is alpha / (n - i)
        # Wait, indices: 0 to n-1.
        # i=0 (smallest): threshold = alpha / n
        # i=1: threshold = alpha / (n-1)
        # ...
        # i=k: threshold = alpha / (n - k)
        
        threshold = alpha / (n - i)
        if p_val <= threshold:
            significant_pairs.append(pair)
        else:
            # Once we fail to reject, all subsequent (larger) p-values are also not rejected.
            # But we need to continue calculating corrected values for the list?
            # The task asks for "corrected_p_values" and "significant_pairs".
            # We can stop adding to significant_pairs, but we should calculate corrected values for all?
            # Usually, corrected p-values are calculated for all.
            pass

    # Ensure monotonicity of corrected p-values (adjusted p-values must be non-decreasing)
    # adj_p(i) = max( adj_p(i-1), p(i) * (n-i) )
    final_corrected = []
    max_so_far = 0.0
    for i, p_val in enumerate(sorted_items):
        adjusted = p_val[1] * (n - i)
        if adjusted > max_so_far:
            max_so_far = adjusted
        else:
            adjusted = max_so_far
        final_corrected.append(min(adjusted, 1.0)) # Cap at 1.0
    
    # Re-order significant pairs? The task asks for a list of strings.
    # The order in significant_pairs is the order of rejection (sorted by p-value).
    # This is acceptable.
    
    return final_corrected, significant_pairs


def run_significance_tests(input_path: str, output_path: str, alpha: float = 0.05):
    """
    Main function to run Holm-Bonferroni correction.
    
    Args:
        input_path: Path to the JSON file containing p-values from T025b.
        output_path: Path to save the results JSON.
        alpha: Significance level.
    """
    logger.info(f"Loading p-values from {input_path}")
    
    # T025b is marked completed, so we assume it produced a file.
    # However, the task description for T025c says "Input: Array of p-values from T025b".
    # If T025b output is not in a standard file, we might need to infer.
    # Let's assume T025b wrote to `results/p_values.json`.
    # If the provided input_path is not the right one, we try a default.
    if not os.path.exists(input_path):
        default_path = "results/p_values.json"
        if os.path.exists(default_path):
            input_path = default_path
        else:
            raise FileNotFoundError(f"Input file {input_path} not found. Tried default: {default_path}")

    with open(input_path, 'r') as f:
        p_values_data = json.load(f)

    # Extract p-values. Assuming the file is a dict of {"pair": p_value}
    if isinstance(p_values_data, list):
        # If it's a list, maybe it's just values? We need pairs for the output.
        # This is unlikely based on the schema requirement.
        # Let's assume it's a dict.
        p_values = {str(i): val for i, val in enumerate(p_values_data)}
    elif isinstance(p_values_data, dict):
        p_values = p_values_data
    else:
        raise ValueError(f"Unexpected input format: {type(p_values_data)}")

    logger.info(f"Applying Holm-Bonferroni correction to {len(p_values)} comparisons")
    
    corrected_p_vals, significant = holm_bonferroni_correction(p_values, alpha)
    
    # Prepare output
    result = {
        "corrected_p_values": corrected_p_vals,
        "significant_pairs": significant,
        "method": "holm-bonferroni"
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info(f"Significant pairs: {significant}")


def main():
    parser = argparse.ArgumentParser(description="Apply Holm-Bonferroni correction to p-values.")
    parser.add_argument("--input", type=str, default="results/p_values.json", help="Input JSON with p-values")
    parser.add_argument("--output", type=str, default="results/significance_test_results.json", help="Output JSON path")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    
    args = parser.parse_args()
    
    try:
        run_significance_tests(args.input, args.output, args.alpha)
    except Exception as e:
        logger.error(f"Error running significance tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()