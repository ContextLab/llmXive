"""
Heterogeneity Analysis Module (Task T018)

Calculates I² (I-squared) statistic from meta-analysis results.
Reads meta_results.json and writes heterogeneity_results.json.
"""
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# --- Utility Functions (Shared with other analysis modules) ---

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def load_json(file_path: Path) -> Dict[str, Any]:
    """Loads a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Saves data to a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def load_effect_sizes_and_se(meta_results: Dict[str, Any]) -> Tuple[List[float], List[float]]:
    """
    Extracts effect sizes (r) and standard errors (se) from meta_results.json.
    Handles both 'individual_studies' and 'studies' keys.
    """
    studies = meta_results.get('individual_studies') or meta_results.get('studies')
    
    if not studies:
        # If no individual studies are listed, we cannot calculate I2 properly
        # This might happen if the meta-analysis was skipped or failed early.
        # Return empty lists to signal this condition.
        return [], []
    
    r_values = []
    se_values = []
    
    for study in studies:
        r = study.get('r')
        se = study.get('se')
        
        # Handle cases where se might be derived or missing
        if r is not None and se is not None:
            r_values.append(float(r))
            se_values.append(float(se))
        elif r is not None and 'variance' in study:
            # Derive SE from variance if available
            var = study['variance']
            if var > 0:
                r_values.append(float(r))
                se_values.append(math.sqrt(float(var)))
            else:
                # Invalid variance, skip or handle as error
                pass
    
    return r_values, se_values

def load_study_count_from_json(file_path: Path) -> int:
    """Loads the study count N from study_count.json."""
    data = load_json(file_path)
    return int(data.get('N', 0))

# --- Core Calculation Logic ---

def calculate_i_squared(q_statistic: float, k: int) -> float:
    """
    Calculates I² statistic given Q and k.
    I² = max(0, (Q - df) / Q) * 100
    where df = k - 1
    """
    if k < 2:
        return 0.0
    
    df = k - 1
    if q_statistic <= df:
        return 0.0
    
    i_squared = ((q_statistic - df) / q_statistic) * 100.0
    return max(0.0, i_squared)

def get_heterogeneity_interpretation(i_squared: float) -> str:
    """
    Returns a qualitative interpretation of the I² value.
    Based on standard Cochrane guidelines.
    """
    if i_squared < 25:
        return "Low heterogeneity"
    elif i_squared < 50:
        return "Moderate heterogeneity"
    elif i_squared < 75:
        return "Substantial heterogeneity"
    else:
        return "Considerable heterogeneity"

def update_output_json(base_results: Dict[str, Any], i_squared: float, 
                       q_statistic: float, df: int, p_value: Optional[float],
                       interpretation: str) -> Dict[str, Any]:
    """
    Updates the base meta-analysis results with heterogeneity metrics.
    Ensures I² is formatted to exactly two decimal places.
    """
    result = base_results.copy()
    
    # Format I² to exactly two decimal places as a float
    # JSON serialization will handle the float, but we ensure precision here.
    result['heterogeneity'] = {
        'i_squared': round(i_squared, 2),
        'q_statistic': round(q_statistic, 4),
        'df': df,
        'p_value': round(p_value, 4) if p_value is not None else None,
        'interpretation': interpretation
    }
    
    return result

# --- Main Execution Logic ---

def run_heterogeneity_analysis(meta_results_path: Path, study_count_path: Path, 
                               output_path: Path) -> Dict[str, Any]:
    """
    Main function to run heterogeneity analysis.
    1. Loads meta_results.json.
    2. Extracts effect sizes and SEs.
    3. Calculates Q statistic (Cochran's Q).
    4. Calculates I².
    5. Writes results to heterogeneity_results.json.
    """
    # Load inputs
    meta_results = load_json(meta_results_path)
    study_count_data = load_json(study_count_path)
    n_studies = study_count_data.get('N', 0)
    
    # Extract effect sizes and SEs
    r_values, se_values = load_effect_sizes_and_se(meta_results)
    k = len(r_values)
    
    # Handle edge cases
    if k < 2:
        # Cannot calculate heterogeneity with < 2 studies
        result = {
            'status': 'skipped',
            'reason': f'Insufficient studies for heterogeneity analysis (k={k}). Requires k >= 2.',
            'i_squared': None,
            'q_statistic': None,
            'df': None,
            'p_value': None,
            'interpretation': None
        }
        save_json(output_path, result)
        return result
    
    # Calculate Q Statistic (Cochran's Q)
    # Q = sum(w_i * (theta_i - theta_bar)^2)
    # where w_i = 1 / se_i^2
    # theta_bar = sum(w_i * theta_i) / sum(w_i)
    
    weights = [1.0 / (se * se) for se in se_values]
    sum_w = sum(weights)
    weighted_sum = sum(w * r for w, r in zip(weights, r_values))
    theta_bar = weighted_sum / sum_w
    
    q_statistic = sum(w * ((r - theta_bar) ** 2) for w, r in zip(weights, r_values))
    
    # Calculate I²
    df = k - 1
    i_squared = calculate_i_squared(q_statistic, k)
    interpretation = get_heterogeneity_interpretation(i_squared)
    
    # Calculate p-value for Q (Chi-squared distribution)
    try:
        from scipy.stats import chi2
        p_value = 1.0 - chi2.cdf(q_statistic, df)
    except ImportError:
        # Fallback if scipy is not available (though it should be per requirements)
        p_value = None
    
    # Prepare output
    # We update the base meta_results to include heterogeneity info, 
    # or create a standalone heterogeneity result.
    # The task asks to write to heterogeneity_results.json.
    # We will include the core metrics and the interpretation.
    
    output_data = {
        'status': 'completed',
        'k': k,
        'i_squared': round(i_squared, 2),
        'q_statistic': round(q_statistic, 4),
        'df': df,
        'p_value': round(p_value, 4) if p_value is not None else None,
        'interpretation': interpretation,
        'source': 'meta_results.json'
    }
    
    save_json(output_path, output_data)
    return output_data

def main():
    """Entry point for the heterogeneity analysis script."""
    project_root = get_project_root()
    
    # Define paths relative to project root
    meta_results_path = project_root / 'data' / 'derived' / 'meta_results.json'
    study_count_path = project_root / 'data' / 'processed' / 'study_count.json'
    output_path = project_root / 'data' / 'derived' / 'heterogeneity_results.json'
    
    # Check if inputs exist
    if not meta_results_path.exists():
        print(f"Error: {meta_results_path} not found. Run meta_analysis.py first.")
        sys.exit(1)
    
    if not study_count_path.exists():
        print(f"Error: {study_count_path} not found. Run study_counter.py first.")
        sys.exit(1)
    
    try:
        result = run_heterogeneity_analysis(meta_results_path, study_count_path, output_path)
        print(f"Heterogeneity analysis complete. Results saved to {output_path}")
        print(f"I² = {result.get('i_squared')}, Q = {result.get('q_statistic')}")
    except Exception as e:
        print(f"Error during heterogeneity analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()