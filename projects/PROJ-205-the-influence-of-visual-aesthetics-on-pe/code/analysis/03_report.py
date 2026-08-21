"""
Report generation script for the Visual Aesthetics Credibility Study.

This script:
1. Loads ANOVA and pairwise results from JSON files
2. Generates a summary report
3. Saves results to analysis_results.json
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

def generate_summary_report(anova_results, pairwise_results):
    """
    Generate a summary report combining ANOVA and pairwise results.
    
    Args:
        anova_results: Dictionary with ANOVA results
        pairwise_results: Dictionary with pairwise test results
    
    Returns:
        dict: Summary report
    """
    report = {
        "f_stat": anova_results.get("f_stat"),
        "df": anova_results.get("df"),
        "n": anova_results.get("n"),
        "p_val": anova_results.get("p_val"),
        "eta_sq": anova_results.get("eta_sq"),
        "bonferroni_factor": anova_results.get("bonferroni_factor", pairwise_results.get("bonferroni_factor", 6)),
        "pairwise": pairwise_results.get("pairwise", [])
    }
    
    return report

def main():
    """Main entry point for report generation."""
    anova_path = DATA_PROCESSED_DIR / "anova_results.json"
    pairwise_path = DATA_PROCESSED_DIR / "pairwise_results.json"
    output_path = DATA_PROCESSED_DIR / "analysis_results.json"
    
    print("Loading ANOVA results...")
    anova_results = load_json_file(anova_path)
    
    print("Loading pairwise results...")
    pairwise_results = load_json_file(pairwise_path)
    
    print("Generating summary report...")
    report = generate_summary_report(anova_results, pairwise_results)
    
    # Write output
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to {output_path}")

if __name__ == "__main__":
    main()
