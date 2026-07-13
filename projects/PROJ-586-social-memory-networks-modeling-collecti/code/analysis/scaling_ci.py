"""
Task T029: Compute 95% confidence intervals for fitted power-law exponents using bootstrapping.

This module implements the bootstrap procedure to estimate confidence intervals
for the scaling exponents derived from the relationship between agent count and
performance metrics (specialization index, retrieval efficiency).

Output: projects/PROJ-586-social-memory-networks-modeling-collecti/results/scaling_confidence_intervals.json
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

# Import from existing project modules
from analysis.scaling import fit_power_law, load_scaling_data


def load_scaling_results_for_bootstrap(
    data_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load scaling data from CSV or use the default path.
    
    Args:
        data_path: Optional path to the scaling data CSV. If None, uses the default.
        
    Returns:
        DataFrame with columns: agent_count, specialization_index, retrieval_efficiency
    """
    if data_path is None:
        # Default path based on project structure
        default_path = Path(
            "projects/PROJ-586-social-memory-networks-modeling-collecti/data/scaling_results.csv"
        )
        if not default_path.exists():
            # Try alternative location if standard one doesn't exist
            alt_path = Path("data/scaling_results.csv")
            if alt_path.exists():
                default_path = alt_path
            else:
                raise FileNotFoundError(
                    f"Scaling data not found at {default_path} or {alt_path}. "
                    "Run the scaling experiment first."
                )
        data_path = str(default_path)
    
    df = pd.read_csv(data_path)
    required_cols = ["agent_count", "specialization_index", "retrieval_efficiency"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def bootstrap_power_law_ci(
    df: pd.DataFrame,
    metric: str,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Compute 95% confidence intervals for power-law exponent using bootstrapping.
    
    Args:
        df: DataFrame with agent_count and the metric column.
        metric: Name of the metric column (e.g., 'specialization_index').
        n_bootstrap: Number of bootstrap resamples.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary with point estimate, CI lower/upper bounds, and bootstrap stats.
    """
    if seed is not None:
        np.random.seed(seed)
    
    agent_counts = df["agent_count"].values
    metric_values = df[metric].values
    
    # Filter out non-positive values for log transformation
    valid_mask = (agent_counts > 0) & (metric_values > 0)
    if not np.all(valid_mask):
        warnings.warn(
            "Some data points have non-positive values and will be excluded from log-log fit."
        )
    
    x = agent_counts[valid_mask]
    y = metric_values[valid_mask]
    
    if len(x) < 2:
        raise ValueError(
            f"Not enough valid data points for {metric} to fit power law."
        )
    
    # Compute point estimate on original data
    try:
        point_estimate, _ = fit_power_law(x, y)
    except Exception as e:
        raise RuntimeError(f"Failed to fit power law on original data: {e}")
    
    # Bootstrap resampling
    bootstrap_exponents = []
    n_samples = len(x)
    
    for i in range(n_bootstrap):
        # Resample with replacement
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        
        # Sort to ensure consistent ordering (optional but good practice)
        sort_idx = np.argsort(x_boot)
        x_boot = x_boot[sort_idx]
        y_boot = y_boot[sort_idx]
        
        try:
            exp_boot, _ = fit_power_law(x_boot, y_boot)
            bootstrap_exponents.append(exp_boot)
        except Exception:
            # Skip this resample if fit fails
            continue
    
    if len(bootstrap_exponents) < 10:
        raise RuntimeError(
            f"Too few successful bootstrap fits for {metric} (only {len(bootstrap_exponents)})."
        )
    
    bootstrap_exponents = np.array(bootstrap_exponents)
    
    # Compute 95% CI using percentile method
    ci_lower = np.percentile(bootstrap_exponents, 2.5)
    ci_upper = np.percentile(bootstrap_exponents, 97.5)
    
    # Compute additional statistics
    bootstrap_mean = np.mean(bootstrap_exponents)
    bootstrap_std = np.std(bootstrap_exponents)
    
    return {
        "metric": metric,
        "point_estimate": float(point_estimate),
        "ci_95_lower": float(ci_lower),
        "ci_95_upper": float(ci_upper),
        "bootstrap_mean": float(bootstrap_mean),
        "bootstrap_std": float(bootstrap_std),
        "n_bootstrap_successful": len(bootstrap_exponents),
        "n_bootstrap_requested": n_bootstrap,
        "n_data_points": len(x)
    }


def run_scaling_ci_analysis(
    data_path: Optional[str] = None,
    output_path: Optional[str] = None,
    n_bootstrap: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full confidence interval analysis for both metrics.
    
    Args:
        data_path: Path to scaling data CSV.
        output_path: Path for output JSON. If None, uses default.
        n_bootstrap: Number of bootstrap resamples.
        seed: Random seed.
        
    Returns:
        Dictionary containing results for both metrics.
    """
    # Load data
    df = load_scaling_results_for_bootstrap(data_path)
    
    # Compute CIs for both metrics
    results = {
        "analysis_parameters": {
            "n_bootstrap": n_bootstrap,
            "seed": seed,
            "data_source": str(data_path) if data_path else "default",
            "n_data_points": len(df)
        },
        "specialization_index": bootstrap_power_law_ci(
            df, "specialization_index", n_bootstrap, seed
        ),
        "retrieval_efficiency": bootstrap_power_law_ci(
            df, "retrieval_efficiency", n_bootstrap, seed
        )
    }
    
    # Add summary note about data limitations
    if len(df) < 5:
        results["warning"] = (
            "Limited data points (N={}) for power-law fitting. ".format(len(df)) +
            "Confidence intervals should be interpreted with caution. " +
            "As noted in SC-005, 3 data points limit power-law reliability."
        )
    
    # Write output
    if output_path is None:
        output_path = (
            "projects/PROJ-586-social-memory-networks-modeling-collecti/"
            "results/scaling_confidence_intervals.json"
        )
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    return results


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI."""
    parser = argparse.ArgumentParser(
        description="Compute 95% confidence intervals for power-law exponents via bootstrapping."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to scaling data CSV. Default: data/scaling_results.csv"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for output JSON. Default: results/scaling_confidence_intervals.json"
    )
    parser.add_argument(
        "--n-resamples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples (default: 1000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    return parser


def main() -> None:
    """Main entry point for CLI."""
    parser = build_parser()
    args = parser.parse_args()
    
    print(f"Running bootstrap confidence interval analysis...")
    print(f"  Bootstrap resamples: {args.n_bootstrap}")
    print(f"  Random seed: {args.seed}")
    
    try:
        results = run_scaling_ci_analysis(
            data_path=args.data,
            output_path=args.output,
            n_bootstrap=args.n_bootstrap,
            seed=args.seed
        )
        
        print(f"\nResults written to: {args.output or 'default path'}")
        print(f"\nSpecialization Index:")
        print(f"  Point estimate: {results['specialization_index']['point_estimate']:.4f}")
        print(f"  95% CI: [{results['specialization_index']['ci_95_lower']:.4f}, "
              f"{results['specialization_index']['ci_95_upper']:.4f}]")
        
        print(f"\nRetrieval Efficiency:")
        print(f"  Point estimate: {results['retrieval_efficiency']['point_estimate']:.4f}")
        print(f"  95% CI: [{results['retrieval_efficiency']['ci_95_lower']:.4f}, "
              f"{results['retrieval_efficiency']['ci_95_upper']:.4f}]")
        
        if "warning" in results:
            print(f"\nWARNING: {results['warning']}")
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()