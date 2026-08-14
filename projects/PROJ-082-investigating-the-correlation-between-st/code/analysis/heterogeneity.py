"""
Heterogeneity analysis module for meta-analysis.
Calculates I-squared statistics and updates results.
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Project root resolution
def get_project_root() -> Path:
    """Get the project root directory (parent of 'code')."""
    current = Path(__file__).resolve()
    code_dir = current.parent
    return code_dir.parent

def load_study_count_from_json() -> int:
    """
    Load the study count (N) from data/processed/study_count.json.
    Raises FileNotFoundError if the file does not exist.
    """
    project_root = get_project_root()
    file_path = project_root / "data" / "processed" / "study_count.json"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Study count file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return int(data.get("N", 0))

def load_effect_sizes_and_se() -> Tuple[List[float], List[float]]:
    """
    Load effect sizes (r) and standard errors (se) from data/processed/extracted_studies.csv.
    Returns two lists: r_values and se_values.
    Only includes rows where 'r' and 'se' are valid numbers.
    """
    project_root = get_project_root()
    file_path = project_root / "data" / "processed" / "extracted_studies.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Extracted studies file not found: {file_path}")
    
    r_values = []
    se_values = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Skip header
        header_line = f.readline()
        header = [col.strip() for col in header_line.split(',')]
        
        r_idx = None
        se_idx = None
        
        if 'r' in header:
            r_idx = header.index('r')
        if 'se' in header:
            se_idx = header.index('se')
        
        if r_idx is None or se_idx is None:
            raise ValueError("Required columns 'r' and 'se' not found in extracted_studies.csv")
        
        for line in f:
            parts = line.strip().split(',')
            if len(parts) <= max(r_idx, se_idx):
                continue
            
            try:
                r_val = float(parts[r_idx])
                se_val = float(parts[se_idx])
                
                if not math.isnan(r_val) and not math.isnan(se_val):
                    r_values.append(r_val)
                    se_values.append(se_val)
            except (ValueError, IndexError):
                continue
    
    return r_values, se_values

def calculate_i_squared(r_values: List[float], se_values: List[float]) -> float:
    """
    Calculate the I-squared (I²) statistic for heterogeneity.
    
    Formula:
    Q = sum( (effect_i - pooled_effect)^2 / se_i^2 )
    df = k - 1
    tau2 = max(0, (Q - df) / C) where C = sum(1/se_i^2) - (sum(1/se_i^2)^2 / sum(1/se_i^4))
    I2 = 100 * max(0, (Q - df) / Q)
    
    Returns I² as a percentage with exactly two decimal places.
    """
    if len(r_values) < 2:
        # Cannot calculate heterogeneity with fewer than 2 studies
        return 0.00
    
    k = len(r_values)
    df = k - 1
    
    # Calculate weights (w_i = 1 / se_i^2)
    weights = [1.0 / (se ** 2) for se in se_values]
    
    # Calculate pooled effect (fixed effects weight)
    sum_w = sum(weights)
    sum_w_r = sum(w * r for w, r in zip(weights, r_values))
    pooled_effect = sum_w_r / sum_w
    
    # Calculate Q statistic
    # Q = sum( w_i * (effect_i - pooled)^2 )
    Q = sum(w * (r - pooled_effect) ** 2 for w, r in zip(weights, r_values))
    
    # Calculate I-squared
    # I2 = 100 * max(0, (Q - df) / Q)
    if Q <= df:
        i_squared = 0.0
    else:
        i_squared = 100.0 * (Q - df) / Q
    
    # Round to exactly two decimal places
    return round(i_squared, 2)

def run_heterogeneity_analysis() -> Dict[str, Any]:
    """
    Run the full heterogeneity analysis.
    Returns a dictionary with i_squared and other metrics.
    """
    # Check study count
    N = load_study_count_from_json()
    
    if N < 2:
        return {
            "i_squared": 0.00,
            "status": "skipped",
            "reason": f"Insufficient studies (N={N}) for heterogeneity analysis"
        }
    
    # Load data
    r_values, se_values = load_effect_sizes_and_se()
    
    if len(r_values) < 2:
        return {
            "i_squared": 0.00,
            "status": "skipped",
            "reason": "Insufficient valid effect sizes for heterogeneity analysis"
        }
    
    # Calculate I-squared
    i_squared = calculate_i_squared(r_values, se_values)
    
    return {
        "i_squared": i_squared,
        "status": "completed",
        "k": len(r_values)
    }

def update_output_json(i_squared: float) -> None:
    """
    Update the data/derived/results.json file with the i_squared field.
    If the file doesn't exist, create it with minimal structure.
    """
    project_root = get_project_root()
    results_path = project_root / "data" / "derived" / "results.json"
    
    # Ensure directory exists
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing results if present
    if results_path.exists():
        with open(results_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = {}
    
    # Update with i_squared (formatted to 2 decimal places)
    results["i_squared"] = round(i_squared, 2)
    
    # Write back
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def main() -> None:
    """Main entry point for heterogeneity analysis."""
    try:
        print("Running heterogeneity analysis...")
        
        # Run analysis
        analysis_result = run_heterogeneity_analysis()
        
        if analysis_result["status"] == "completed":
            i_squared = analysis_result["i_squared"]
            print(f"I² statistic: {i_squared:.2f}%")
            
            # Update results.json
            update_output_json(i_squared)
            print("Updated data/derived/results.json with i_squared")
        else:
            print(f"Heterogeneity analysis skipped: {analysis_result['reason']}")
            # Still update results.json with 0.00 and status
            update_output_json(0.00)
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during heterogeneity analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()