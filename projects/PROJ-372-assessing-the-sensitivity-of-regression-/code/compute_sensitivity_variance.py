"""
Compute the variance in classification rates from the Breusch-Pagan sensitivity sweep.

This script reads the output of the sensitivity sweep (T061) which contains 
classification rates for different BP p-value cutoffs, and computes the variance
of these rates to quantify the sensitivity of the classification to threshold selection.

Output: artifacts/meta_analysis/sensitivity_sweep.json
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def compute_variance_in_classification_rates(sweep_results: Dict[str, Any]) -> float:
    """
    Compute the variance of classification rates across different p-value cutoffs.
    
    Args:
        sweep_results: Dictionary containing the sensitivity sweep results with 
                     'classification_rates' key mapping cutoffs to rates.
                     
    Returns:
        Variance of the classification rates.
    """
    rates = list(sweep_results.get('classification_rates', {}).values())
    
    if len(rates) < 2:
        # Cannot compute variance with less than 2 points
        # Return 0.0 or raise an error depending on requirements
        # For robustness, return 0.0 but log a warning
        print("Warning: Less than 2 classification rates found. Variance set to 0.0.")
        return 0.0
    
    return float(np.var(rates, ddof=1))  # Sample variance (ddof=1)

def main():
    parser = argparse.ArgumentParser(
        description="Compute variance in classification rates from sensitivity sweep."
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="artifacts/meta_analysis/sensitivity_sweep_input.json",
        help="Path to the sensitivity sweep results JSON (from T061)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="artifacts/meta_analysis/sensitivity_sweep.json",
        help="Path to output JSON file"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load sweep results
        sweep_data = load_json_file(input_path)
        
        # Validate structure
        if 'classification_rates' not in sweep_data:
            raise ValueError("Input file must contain 'classification_rates' key")
        
        # Compute variance
        variance = compute_variance_in_classification_rates(sweep_data)
        
        # Prepare output
        output_data = {
            "variance_classification_rates": variance,
            "num_cutoffs_evaluated": len(sweep_data.get('classification_rates', {})),
            "cutoffs": list(sweep_data.get('classification_rates', {}).keys()),
            "rates": list(sweep_data.get('classification_rates', {}).values()),
            "mean_classification_rate": float(np.mean(list(sweep_data.get('classification_rates', {}).values()))) if sweep_data.get('classification_rates') else 0.0,
            "min_rate": float(min(sweep_data.get('classification_rates', {}).values())) if sweep_data.get('classification_rates') else 0.0,
            "max_rate": float(max(sweep_data.get('classification_rates', {}).values())) if sweep_data.get('classification_rates') else 0.0,
            "description": "Variance in dataset classification rates across different Breusch-Pagan p-value cutoffs. High variance indicates high sensitivity to threshold selection."
        }
        
        # Write output
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Successfully computed variance: {variance:.6f}")
        print(f"Output written to: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()