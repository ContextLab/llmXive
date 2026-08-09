"""
Robustness Stability Check (T039)

Verifies that the direction and significance of the main effect remain consistent
across threshold variations defined in the robustness report.

Input: data/derived/robustness_report.csv
Output: output/stability_check.json
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("robustness_stability_check")

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_paths() -> Dict[str, Path]:
    """Return paths to input and output files."""
    root = get_project_root()
    return {
        "input": root / "data" / "derived" / "robustness_report.csv",
        "output": root / "output" / "stability_check.json"
    }

def load_robustness_report(path: Path) -> pd.DataFrame:
    """Load the robustness report CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    df = pd.read_csv(path)
    
    # Expected columns based on T033 spec
    required_cols = ['threshold', 'coef_fixation_duration', 'p_adj_fixation_duration', 
                     'ci_lower_fixation_duration', 'ci_upper_fixation_duration']
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in robustness report: {missing}")
    
    return df

def analyze_stability(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze the stability of the main effect across thresholds.
    
    Checks:
    1. Consistent direction: All coefficients have the same sign.
    2. Consistent significance: All p-values are below alpha (0.05) OR all above.
    3. CI Overlap: Check if confidence intervals overlap across thresholds.
    """
    results = {}
    
    # 1. Check Direction Consistency
    coef_signs = np.sign(df['coef_fixation_duration'])
    # Handle zeros as neutral, but if all non-zero are same sign, it's consistent
    non_zero_signs = coef_signs[coef_signs != 0]
    
    if len(non_zero_signs) == 0:
        results['consistent_direction'] = True
        results['direction_summary'] = "All coefficients are zero"
    else:
        unique_signs = np.unique(non_zero_signs)
        results['consistent_direction'] = len(unique_signs) == 1
        results['direction_summary'] = f"Signs observed: {unique_signs.tolist()}"
    
    # 2. Check Significance Consistency (using alpha=0.05)
    alpha = 0.05
    is_significant = df['p_adj_fixation_duration'] < alpha
    unique_sig = np.unique(is_significant.values)
    
    # Consistent if all are significant OR all are not significant
    results['consistent_significance'] = len(unique_sig) == 1
    results['significance_summary'] = f"Significant at alpha={alpha}: {unique_sig.tolist()}"
    
    # 3. CI Overlap Summary
    # Calculate if the CI of the first threshold overlaps with the last
    # and if the union of all CIs covers the mean effect.
    ci_lower = df['ci_lower_fixation_duration']
    ci_upper = df['ci_upper_fixation_duration']
    
    global_min_ci = ci_lower.min()
    global_max_ci = ci_upper.max()
    
    # Check pairwise overlap for consecutive thresholds
    overlaps = []
    for i in range(len(df) - 1):
        curr_upper = ci_upper.iloc[i]
        next_lower = ci_lower.iloc[i+1]
        # Overlap if current upper >= next lower
        overlap = curr_upper >= next_lower
        overlaps.append(overlap)
    
    results['ci_overlap_summary'] = {
        "all_consecutive_overlaps": all(overlaps),
        "global_ci_range": [float(global_min_ci), float(global_max_ci)],
        "overlap_details": overlaps
    }
    
    # Overall verdict
    results['overall_stable'] = (
        results['consistent_direction'] and 
        results['consistent_significance'] and 
        results['ci_overlap_summary']['all_consecutive_overlaps']
    )
    
    return results

def write_results(results: Dict[str, Any], path: Path) -> None:
    """Write results to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Stability check results written to {path}")

def main() -> None:
    """Main entry point."""
    paths = get_paths()
    logger.info(f"Starting robustness stability check. Input: {paths['input']}")
    
    try:
        df = load_robustness_report(paths['input'])
        logger.info(f"Loaded {len(df)} threshold iterations.")
        
        results = analyze_stability(df)
        
        write_results(results, paths['output'])
        
        logger.info(f"Stability Check Complete. Overall Stable: {results['overall_stable']}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()