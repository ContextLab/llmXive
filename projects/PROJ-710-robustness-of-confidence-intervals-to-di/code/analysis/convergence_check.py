"""
Convergence Check for Coverage Simulation

This module verifies that the simulation has run with sufficient iterations (seeds)
such that the standard error of the estimated coverage probability is below a
specified threshold (default 0.5%).

It loads the results from the main simulation, calculates the standard error for
each condition, and generates a report indicating which conditions have converged.
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Import config to get paths
# We use relative import logic to ensure it works when run as a script or module
try:
    from config import Config
except ImportError:
    # Fallback for running directly in the code directory context if needed
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import Config

# Constants
DEFAULT_SE_THRESHOLD = 0.005  # 0.5%
MIN_SE_THRESHOLD = 0.001      # Hard floor for safety
MAX_SE_THRESHOLD = 0.05       # Hard ceiling for sanity check

def calculate_coverage_se(coverage_rate: float, n_sim: int) -> float:
    """
    Calculate the standard error of a coverage rate.

    Coverage is a Bernoulli trial (1 if covered, 0 if not).
    SE = sqrt(p * (1-p) / n)

    Args:
        coverage_rate: The observed coverage probability (0.0 to 1.0).
        n_sim: The number of simulations (trials).

    Returns:
        The standard error of the coverage estimate.
    """
    if n_sim <= 1:
        return float('inf')
    
    # Clamp coverage_rate to [0, 1] to avoid NaN from sqrt of negative numbers
    # due to floating point errors
    p = np.clip(coverage_rate, 0.0, 1.0)
    
    se = np.sqrt(p * (1.0 - p) / n_sim)
    return float(se)

def check_convergence(
    results_df: pd.DataFrame,
    se_threshold: float = DEFAULT_SE_THRESHOLD,
    group_cols: List[str] = ['dataset', 'epsilon', 'noise_type', 'statistic']
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Check convergence for all conditions in the results dataframe.

    Args:
        results_df: DataFrame containing simulation results. Expected to have
                    a 'covered' (bool/int) column and simulation metadata.
        se_threshold: The maximum acceptable standard error.
        group_cols: Columns to group by for aggregation.

    Returns:
        Tuple of (aggregated_df, summary_dict).
        aggregated_df: DataFrame with coverage rate, SE, and convergence status per group.
        summary_dict: Summary statistics about convergence.
    """
    if results_df.empty:
        return pd.DataFrame(), {"error": "No results to check"}

    # Ensure 'covered' is numeric
    if 'covered' not in results_df.columns:
        # Try to infer from a boolean column if named differently, or raise
        raise ValueError("Results dataframe must contain a 'covered' column (0/1 or True/False).")

    # Group by condition columns
    grouped = results_df.groupby(group_cols)

    # Aggregate: calculate mean coverage and count
    agg_df = grouped.agg(
        coverage_rate=('covered', 'mean'),
        n_sim=('covered', 'count')
    ).reset_index()

    # Calculate Standard Error
    agg_df['se'] = agg_df.apply(
        lambda row: calculate_coverage_se(row['coverage_rate'], int(row['n_sim'])),
        axis=1
    )

    # Determine convergence status
    agg_df['converged'] = agg_df['se'] <= se_threshold

    # Calculate summary stats
    total_conditions = len(agg_df)
    converged_conditions = agg_df['converged'].sum()
    non_converged = agg_df[~agg_df['converged']]

    summary = {
        "total_conditions": int(total_conditions),
        "converged_conditions": int(converged_conditions),
        "non_converged_conditions": int(total_conditions - converged_conditions),
        "threshold_used": se_threshold,
        "max_se_observed": float(agg_df['se'].max()) if not agg_df.empty else 0.0,
        "mean_se_observed": float(agg_df['se'].mean()) if not agg_df.empty else 0.0,
        "non_converged_details": []
    }

    if not non_converged.empty:
        summary["non_converged_details"] = non_converged.to_dict(orient='records')

    return agg_df, summary

def generate_convergence_report(
    results_path: Path,
    output_path: Path,
    se_threshold: float = DEFAULT_SE_THRESHOLD
) -> None:
    """
    Load results, check convergence, and write a report.

    Args:
        results_path: Path to the coverage_results.csv file.
        output_path: Path where the convergence report JSON will be saved.
        se_threshold: Target standard error threshold.
    """
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")

    logging.info(f"Loading results from {results_path}")
    df = pd.read_csv(results_path)

    # Determine the correct column for 'covered'
    # The main simulation (T013a) should output a 'covered' column (0 or 1).
    # If the schema from T013c is strictly 'coverage_rate' per row (already aggregated),
    # we need to handle that. However, T013c description says "Group by... and calculate mean".
    # If the file is already aggregated, we might not have the raw 'covered' count.
    # Assuming T013c outputs the raw per-simulation result or a structure where we can count.
    # Re-reading T013c: "Group by (dataset, epsilon, noise_type, statistic) and calculate mean coverage_rate."
    # If T013c outputs the AGGREGATED table, we cannot calculate SE from the mean alone without N.
    # We assume T013c outputs the RAW results (one row per simulation) OR the aggregated table includes 'n_sim'.
    # Let's check for 'n_sim' or 'count' column. If not, we assume the file is raw.
    
    if 'covered' not in df.columns:
        # Fallback: maybe it's 'is_covered' or similar?
        possible_cols = [c for c in df.columns if 'cover' in c.lower()]
        if possible_cols:
            df['covered'] = df[possible_cols[0]]
        else:
            # If we only have aggregated data, we can't compute SE without N.
            # We assume the pipeline produces raw data for this check, or we need to pass N_sim from config.
            # For robustness, let's assume if 'n_sim' is missing, we treat each row as 1 sim (bad) or error.
            # Better: Check if we can infer N from config if the file is aggregated.
            # For now, we assume the file has 'covered' (0/1) and we group.
            raise ValueError("Input file must contain a 'covered' column (0/1) or 'n_sim' column for aggregation.")

    agg_df, summary = check_convergence(df, se_threshold=se_threshold)

    # Save detailed report
    report = {
        "summary": summary,
        "detailed_results": agg_df.to_dict(orient='records')
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logging.info(f"Convergence report written to {output_path}")
    logging.info(f"Converged: {summary['converged_conditions']}/{summary['total_conditions']}")

    if summary['non_converged_conditions'] > 0:
        logging.warning(f"{summary['non_converged_conditions']} conditions did not meet SE threshold {se_threshold}.")

def main():
    """Main entry point for the convergence check script."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting convergence check analysis.")

    try:
        # Determine paths
        # config.ARTIFACTS_DIR is expected to be set in code/config.py
        # If it's missing, we try to infer or use defaults
        artifacts_dir = getattr(Config, 'ARTIFACTS_DIR', None)
        if artifacts_dir is None:
            # Fallback: assume 'artifacts' relative to project root
            project_root = Path(__file__).parent.parent
            artifacts_dir = project_root / 'artifacts'
        
        artifacts_path = Path(artifacts_dir)
        results_path = artifacts_path / "coverage_results.csv"
        report_path = artifacts_path / "convergence_report.json"

        if not results_path.exists():
            logger.error(f"Results file not found at {results_path}. "
                         "Did you run the main simulation (T013a/T042)?")
            sys.exit(1)

        # Run the check
        generate_convergence_report(
            results_path=results_path,
            output_path=report_path,
            se_threshold=DEFAULT_SE_THRESHOLD
        )

        logger.info("Convergence check completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid data format: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during convergence check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
