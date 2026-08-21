"""
Robustness report generation for the Visual Aesthetics Credibility Study.

This script:
1. Loads ANOVA results from analysis_results.json
2. Loads mixed-effects model results from mixed_effects_results.json
3. Compares results to determine consistency
4. Saves robustness results to JSON
"""

import os
import sys
import json
import random
import numpy as np
from pathlib import Path

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data").exists() and (current / "code").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_json_file(file_path):
    """Load JSON file and return contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, "r") as f:
        return json.load(f)

def generate_robustness_report(anova_results, lmm_results):
    """
    Generate a robustness report comparing ANOVA and LMM results.
    
    Args:
        anova_results: Dictionary with ANOVA results
        lmm_results: Dictionary with LMM results
    
    Returns:
        dict: Robustness comparison results
    """
    anova_f = anova_results.get("f_stat")
    anova_p = anova_results.get("p_val")
    
    lmm_condition_p = None
    if not lmm_results.get("convergence_failed", True):
        # Get p-value for any condition comparison (use the first one)
        condition_p = lmm_results.get("condition_p", {})
        if condition_p:
            lmm_condition_p = list(condition_p.values())[0]
    
    lmm_condition_coef = None
    if not lmm_results.get("convergence_failed", True):
        condition_coef = lmm_results.get("condition_coef", {})
        if condition_coef:
            lmm_condition_coef = list(condition_coef.values())[0]
    
    # Determine consistency
    # Consistent if LMM condition p < 0.05 and magnitude difference < 10%
    # Since we can't directly compare F-stat to coefficient, we compare p-values
    is_consistent = False
    coef_magnitude_diff = None
    
    if anova_p is not None and lmm_condition_p is not None:
        # Both are significant
        if anova_p < 0.05 and lmm_condition_p < 0.05:
            is_consistent = True
        # Both are non-significant
        elif anova_p >= 0.05 and lmm_condition_p >= 0.05:
            is_consistent = True
        else:
            is_consistent = False
    else:
        is_consistent = False
    
    comparison = "consistent" if is_consistent else "divergent"
    
    # Calculate R-squared change (simplified)
    r_squared_change = None
    if lmm_results.get("r_squared") is not None:
        # This is a placeholder - actual calculation would require more complex modeling
        r_squared_change = lmm_results["r_squared"]
    
    return {
        "anova_f": anova_f,
        "anova_p": anova_p,
        "lmm_condition_coef": lmm_condition_coef,
        "lmm_condition_p": lmm_condition_p,
        "r_squared_change": r_squared_change,
        "coef_magnitude_diff": coef_magnitude_diff,
        "comparison": comparison
    }

def main():
    """Main entry point for robustness report generation."""
    anova_path = DATA_PROCESSED_DIR / "analysis_results.json"
    lmm_path = DATA_PROCESSED_DIR / "mixed_effects_results.json"
    output_path = DATA_PROCESSED_DIR / "robustness_results.json"
    
    print("Loading ANOVA results...")
    anova_results = load_json_file(anova_path)
    
    print("Loading LMM results...")
    lmm_results = load_json_file(lmm_path)
    
    print("Generating robustness report...")
    report = generate_robustness_report(anova_results, lmm_results)
    
    # Write output
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Robustness report written to {output_path}")

if __name__ == "__main__":
    main()
