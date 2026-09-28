import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np

def load_regression_stats(input_path: Path) -> Dict[str, Any]:
    """
    Load regression statistics from input file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def bonferroni_correction(p_values: List[float], k: int) -> List[float]:
    """
    Apply Bonferroni correction to p-values.
    
    Args:
        p_values: List of raw p-values
        k: Number of comparisons (dynamic based on data)
    
    Returns:
        List of corrected p-values
    """
    if k == 0:
        return p_values
    
    alpha = 0.05 / k
    corrected = [min(p * k, 1.0) for p in p_values]
    return corrected

def apply_bonferroni_to_covariates(stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Apply Bonferroni correction to covariate p-values.
    """
    p_values = stats.get("p_values", [])
    k = len(p_values)  # Dynamic k based on number of covariates
    
    corrected = bonferroni_correction(p_values, k)
    
    return {
        "raw_p_values": p_values,
        "corrected_p_values": corrected,
        "k": k,
        "alpha": 0.05 / k if k > 0 else 1.0
    }

def save_corrected_pvalues(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save corrected p-values to output file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

def main():
    """
    CLI entry point for Bonferroni correction.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to pairwise comparisons")
    parser.add_argument("--input", type=str, required=True, help="Input file with pairwise comparison results")
    parser.add_argument("--output", type=str, required=True, help="Output file for corrected p-values")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Load stats
    stats = load_regression_stats(input_path)
    
    # Apply correction
    result = apply_bonferroni_to_covariates(stats)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_corrected_pvalues(result, output_path)
    
    print(f"Bonferroni correction applied. Saved to {args.output}")
    print(f"Number of comparisons: {result['k']}")
    print(f"Corrected alpha: {result['alpha']}")

if __name__ == "__main__":
    main()
