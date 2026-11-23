"""
Non-monotonicity checker for US3.

Analyzes the collapse sweep results to identify if there is a peak effective
reasoning depth at an intermediate alpha value, indicating a non-monotonic
relationship between alpha and reasoning depth.

Outputs results to docs/results/hypothesis_validation.json
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

def load_sweep_results(csv_path: str) -> pd.DataFrame:
    """
    Load the collapse sweep results from CSV.
    
    Args:
        csv_path: Path to the collapse_sweep.csv file
        
    Returns:
        DataFrame with the sweep results
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Sweep results file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from {csv_path}")
    
    # Expected columns based on T028 output
    required_cols = ['alpha', 'horizon', 'mean_effective_depth', 'collapse_ratio']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in sweep results: {missing}")
    
    return df

def find_peak_alpha(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Find the alpha value that maximizes the mean effective reasoning depth.
    
    This checks for non-monotonicity by identifying if the peak occurs at
    an intermediate alpha value (not at the extremes).
    
    Args:
        df: DataFrame with alpha and mean_effective_depth columns
        
    Returns:
        Tuple of (peak_alpha, peak_depth)
    """
    # Group by alpha and get the mean effective depth for each alpha
    # (in case there are multiple horizons per alpha)
    alpha_depth = df.groupby('alpha')['mean_effective_depth'].mean().reset_index()
    alpha_depth = alpha_depth.sort_values('alpha')
    
    # Find the alpha with maximum mean effective depth
    peak_idx = alpha_depth['mean_effective_depth'].idxmax()
    peak_alpha = alpha_depth.loc[peak_idx, 'alpha']
    peak_depth = alpha_depth.loc[peak_idx, 'mean_effective_depth']
    
    logger.info(f"Peak effective depth: {peak_depth:.4f} at alpha = {peak_alpha}")
    
    return peak_alpha, peak_depth

def check_nonmonotonicity(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for non-monotonic relationship between alpha and effective depth.
    
    A non-monotonic relationship is indicated when:
    1. The peak effective depth occurs at an intermediate alpha (not 0.1 or 0.9)
    2. The depth at the peak is significantly higher than at the extremes
    
    Args:
        df: DataFrame with sweep results
        
    Returns:
        Dictionary with non-monotonicity analysis results
    """
    alpha_values = sorted(df['alpha'].unique())
    logger.info(f"Analyzing alpha values: {alpha_values}")
    
    if len(alpha_values) < 3:
        logger.warning("Not enough alpha values to detect non-monotonicity")
        return {
            "peak_alpha": None,
            "peak_depth": None,
            "is_nonmonotonic": False,
            "hypothesis_validated": False,
            "reason": "Insufficient alpha values for analysis"
        }
    
    # Get mean effective depth per alpha
    alpha_depth = df.groupby('alpha')['mean_effective_depth'].mean().reset_index()
    alpha_depth = alpha_depth.sort_values('alpha')
    
    # Find peak
    peak_idx = alpha_depth['mean_effective_depth'].idxmax()
    peak_alpha = alpha_depth.loc[peak_idx, 'alpha']
    peak_depth = alpha_depth.loc[peak_idx, 'mean_effective_depth']
    
    # Get depths at extremes
    min_alpha = alpha_values[0]
    max_alpha = alpha_values[-1]
    depth_at_min = alpha_depth[alpha_depth['alpha'] == min_alpha]['mean_effective_depth'].values[0]
    depth_at_max = alpha_depth[alpha_depth['alpha'] == max_alpha]['mean_effective_depth'].values[0]
    
    # Check if peak is at an intermediate alpha
    is_intermediate = (peak_alpha != min_alpha) and (peak_alpha != max_alpha)
    
    # Check if peak is significantly higher than extremes
    # Using a threshold of 5% higher than both extremes
    threshold = 0.05
    significantly_higher = (
        peak_depth > depth_at_min * (1 + threshold) and
        peak_depth > depth_at_max * (1 + threshold)
    )
    
    is_nonmonotonic = is_intermediate and significantly_higher
    
    # Hypothesis validation: non-monotonicity suggests optimal alpha exists
    hypothesis_validated = is_nonmonotonic
    
    logger.info(f"Peak alpha: {peak_alpha}, Intermediate: {is_intermediate}, "
               f"Significantly higher: {significantly_higher}")
    logger.info(f"Non-monotonicity detected: {is_nonmonotonic}")
    logger.info(f"Hypothesis validated: {hypothesis_validated}")
    
    return {
        "peak_alpha": float(peak_alpha),
        "peak_depth": float(peak_depth),
        "depth_at_min_alpha": float(depth_at_min),
        "min_alpha": float(min_alpha),
        "depth_at_max_alpha": float(depth_at_max),
        "max_alpha": float(max_alpha),
        "is_intermediate_peak": bool(is_intermediate),
        "is_significantly_higher": bool(significantly_higher),
        "is_nonmonotonic": bool(is_nonmonotonic),
        "hypothesis_validated": bool(hypothesis_validated),
        "reason": (
            "Non-monotonic relationship detected: peak effective reasoning depth "
            f"occurs at intermediate alpha={peak_alpha}"
        ) if hypothesis_validated else (
            "No non-monotonic relationship detected: effective depth does not peak "
            f"at intermediate alpha values"
        )
    }

def write_hypothesis_validation(result: Dict[str, Any], output_path: str) -> None:
    """
    Write the hypothesis validation results to JSON file.
    
    Args:
        result: Dictionary with validation results
        output_path: Path to the output JSON file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Wrote hypothesis validation results to {output_path}")

def run_nonmonotonicity_check(
    input_csv: str = "data/processed/collapse_sweep.csv",
    output_json: str = "docs/results/hypothesis_validation.json"
) -> Dict[str, Any]:
    """
    Main function to run the non-monotonicity check.
    
    Args:
        input_csv: Path to the collapse sweep results CSV
        output_json: Path to write the hypothesis validation JSON
        
    Returns:
        Dictionary with the validation results
    """
    logger.info("Starting non-monotonicity check...")
    
    # Load sweep results
    df = load_sweep_results(input_csv)
    
    # Check for non-monotonicity
    result = check_nonmonotonicity(df)
    
    # Write results to JSON
    write_hypothesis_validation(result, output_json)
    
    logger.info("Non-monotonicity check completed.")
    
    return result

if __name__ == "__main__":
    # Run the non-monotonicity check
    results = run_nonmonotonicity_check()
    
    print("\n" + "="*60)
    print("HYPOTHESIS VALIDATION RESULTS")
    print("="*60)
    print(f"Peak Alpha: {results['peak_alpha']}")
    print(f"Peak Depth: {results['peak_depth']:.4f}")
    print(f"Is Non-monotonic: {results['is_nonmonotonic']}")
    print(f"Hypothesis Validated: {results['hypothesis_validated']}")
    print(f"Reason: {results['reason']}")
    print("="*60)
