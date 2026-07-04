"""
Scaling Confidence Intervals Analysis (Task T029)

Computes 95% confidence intervals for fitted power-law exponents using bootstrapping.
Outputs results to projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Import existing scaling utilities
try:
    from analysis.scaling import load_scaling_data, fit_power_law
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis.scaling import load_scaling_data, fit_power_law


def bootstrap_power_law_ci(
    x: np.ndarray,
    y: np.ndarray,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None,
) -> Tuple[float, float, float]:
    """
    Compute 95% confidence intervals for power-law exponent using bootstrapping.
    
    Args:
        x: Independent variable values (agent counts)
        y: Dependent variable values (metrics)
        n_bootstrap: Number of bootstrap resamples
        random_state: Random seed for reproducibility
    
    Returns:
        Tuple of (exponent, lower_ci, upper_ci)
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 paired data points for bootstrapping")
    
    # Filter out NaN/Inf values
    valid_mask = ~(np.isnan(x) | np.isnan(y) | np.isinf(x) | np.isinf(y))
    x_clean = x[valid_mask]
    y_clean = y[valid_mask]
    
    if len(x_clean) < 2:
        raise ValueError("Not enough valid data points after filtering")
    
    # Store bootstrap exponents
    bootstrap_exponents = []
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(len(x_clean), size=len(x_clean), replace=True)
        x_resample = x_clean[indices]
        y_resample = y_clean[indices]
        
        # Sort by x for consistent fitting
        sort_idx = np.argsort(x_resample)
        x_resample = x_resample[sort_idx]
        y_resample = y_resample[sort_idx]
        
        # Fit power law: y = a * x^b  =>  log(y) = log(a) + b * log(x)
        try:
            # Filter positive values for log transformation
            pos_mask = (x_resample > 0) & (y_resample > 0)
            if np.sum(pos_mask) < 2:
                continue
            
            x_log = np.log(x_resample[pos_mask])
            y_log = np.log(y_resample[pos_mask])
            
            # Linear regression on log-log data
            slope, intercept = np.polyfit(x_log, y_log, 1)
            bootstrap_exponents.append(slope)
            
        except (ValueError, RuntimeWarning):
            # Skip this resample if fitting fails
            continue
    
    if len(bootstrap_exponents) < 10:
        raise ValueError("Insufficient successful bootstrap fits")
    
    # Compute confidence intervals
    bootstrap_exponents = np.array(bootstrap_exponents)
    exponent_mean = np.mean(bootstrap_exponents)
    lower_ci = np.percentile(bootstrap_exponents, 2.5)
    upper_ci = np.percentile(bootstrap_exponents, 97.5)
    
    return float(exponent_mean), float(lower_ci), float(upper_ci)


def load_scaling_results_for_bootstrap(
    results_path: Path,
) -> Dict[str, pd.DataFrame]:
    """
    Load scaling data from the generated CSV file.
    
    Args:
        results_path: Path to the scaling results CSV file
    
    Returns:
        Dictionary mapping metric names to DataFrames
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Scaling results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    
    # Expected columns: agent_count, specialization_index, retrieval_efficiency
    required_cols = ['agent_count', 'specialization_index', 'retrieval_efficiency']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Clean data
    df = df.dropna(subset=required_cols)
    df = df[(df['agent_count'] > 0) & (df['specialization_index'] > 0) & (df['retrieval_efficiency'] > 0)]
    
    return {
        'specialization_index': df[['agent_count', 'specialization_index']],
        'retrieval_efficiency': df[['agent_count', 'retrieval_efficiency']],
    }


def run_scaling_ci_analysis(
    input_path: Path,
    output_path: Path,
    n_bootstrap: int = 1000,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Run the full confidence interval analysis for scaling exponents.
    
    Args:
        input_path: Path to the scaling results CSV
        output_path: Path for the JSON output
        n_bootstrap: Number of bootstrap resamples
        random_state: Random seed
    
    Returns:
        Dictionary with analysis results
    """
    # Load data
    data_dict = load_scaling_results_for_bootstrap(input_path)
    
    results = {
        "analysis_type": "power_law_confidence_intervals",
        "n_bootstrap": n_bootstrap,
        "random_state": random_state,
        "input_file": str(input_path),
        "metrics": {}
    }
    
    for metric_name, df in data_dict.items():
        x = df['agent_count'].values
        y = df[metric_name].values
        
        try:
            exponent, lower_ci, upper_ci = bootstrap_power_law_ci(
                x, y, n_bootstrap=n_bootstrap, random_state=random_state
            )
            
            results["metrics"][metric_name] = {
                "exponent": exponent,
                "lower_95_ci": lower_ci,
                "upper_95_ci": upper_ci,
                "n_data_points": len(x),
                "n_successful_bootstrap": n_bootstrap
            }
            
        except Exception as e:
            results["metrics"][metric_name] = {
                "error": str(e),
                "n_data_points": len(x)
            }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Compute 95% confidence intervals for scaling exponents"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_data.csv"),
        help="Path to scaling results CSV file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json"),
        help="Path for JSON output file"
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap resamples"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser


def main() -> int:
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args()
    
    print(f"Loading scaling data from: {args.input}")
    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}")
        print("Please run the scaling simulation first to generate the input data.")
        return 1
    
    print(f"Computing confidence intervals with {args.n_bootstrap} bootstrap resamples...")
    
    try:
        results = run_scaling_ci_analysis(
            input_path=args.input,
            output_path=args.output,
            n_bootstrap=args.n_bootstrap,
            random_state=args.random_state,
        )
        
        print(f"Results written to: {args.output}")
        print(json.dumps(results, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())