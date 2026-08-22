"""
Script to export significance test results and conformal comparison results to CSV.

This script aggregates results from the bootstrap tests and conformal prediction
wrapper evaluations, then writes them to the results directory as specified in T032.

Output files:
- results/significance_test.csv: Pairwise model comparison results with p-values
- results/conformal_results.csv: Baseline vs. conformal coverage comparison
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

import pandas as pd
import numpy as np

from config import RESULTS_DIR
from utils.logger import get_logger
from evaluation.bootstrap_test import (
    aggregate_bootstrap_results,
    run_all_pairwise_comparisons
)
from calibration.conformal import (
    aggregate_conformal_results,
    conformal_results_to_dataframe
)
from metrics.coverage import coverage_to_dataframe

logger = get_logger(__name__)


def load_and_aggregate_significance_results(
    results_dir: Path,
    model_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate bootstrap test results into a single dataframe.
    
    Args:
        results_dir: Path to the results directory
        model_names: Optional list of model names to include. If None, all available
                    models from the bootstrap results are used.
    
    Returns:
        DataFrame with significance test results (p-values for pairwise comparisons)
    """
    logger.info(f"Aggregating significance test results from {results_dir}")
    
    # Load aggregated bootstrap results
    bootstrap_df = aggregate_bootstrap_results(results_dir, model_names=model_names)
    
    if bootstrap_df.empty:
        logger.warning("No bootstrap results found. Returning empty dataframe.")
        return pd.DataFrame()
    
    logger.info(f"Found {len(bootstrap_df)} model pairs for significance testing")
    
    # Ensure required columns exist
    required_cols = ['model_a', 'model_b', 'p_value', 'significant_at_0.05']
    existing_cols = bootstrap_df.columns.tolist()
    
    # Add significance flag if not present
    if 'significant_at_0.05' not in existing_cols:
        bootstrap_df['significant_at_0.05'] = bootstrap_df['p_value'] < 0.05
    
    # Select and order columns
    output_cols = [col for col in required_cols if col in existing_cols]
    if len(output_cols) < len(required_cols):
        # Add missing columns with defaults
        for col in required_cols:
            if col not in output_cols:
                if col == 'significant_at_0.05':
                    bootstrap_df[col] = False
                else:
                    bootstrap_df[col] = np.nan
        output_cols = [col for col in required_cols]
    
    return bootstrap_df[output_cols]


def load_and_aggregate_conformal_results(
    results_dir: Path,
    model_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate conformal prediction comparison results.
    
    Args:
        results_dir: Path to the results directory
        model_names: Optional list of model names to include.
    
    Returns:
        DataFrame with baseline vs. conformal coverage comparison
    """
    logger.info(f"Aggregating conformal results from {results_dir}")
    
    # Load aggregated conformal results
    conformal_df = aggregate_conformal_results(results_dir, model_names=model_names)
    
    if conformal_df.empty:
        logger.warning("No conformal results found. Returning empty dataframe.")
        return pd.DataFrame()
    
    logger.info(f"Found {len(conformal_df)} model conformal comparisons")
    
    # Ensure required columns exist
    required_cols = [
        'model_name', 
        'baseline_coverage', 
        'conformal_coverage', 
        'coverage_improvement',
        'nominal_level'
    ]
    
    existing_cols = conformal_df.columns.tolist()
    
    # Calculate coverage improvement if not present
    if 'coverage_improvement' not in existing_cols:
        if 'baseline_coverage' in existing_cols and 'conformal_coverage' in existing_cols:
            conformal_df['coverage_improvement'] = (
                conformal_df['conformal_coverage'] - conformal_df['baseline_coverage']
            )
        else:
            conformal_df['coverage_improvement'] = np.nan
    
    # Select and order columns
    output_cols = [col for col in required_cols if col in existing_cols]
    if len(output_cols) < len(required_cols):
        for col in required_cols:
            if col not in output_cols:
                if col == 'coverage_improvement':
                    conformal_df[col] = np.nan
                else:
                    conformal_df[col] = np.nan
        output_cols = [col for col in required_cols]
    
    return conformal_df[output_cols]


def export_results(
    results_dir: Path,
    output_significance_path: Path,
    output_conformal_path: Path,
    model_names: Optional[List[str]] = None
) -> bool:
    """
    Main function to export significance and conformal results to CSV files.
    
    Args:
        results_dir: Path to the directory containing intermediate results
        output_significance_path: Path for the significance test CSV output
        output_conformal_path: Path for the conformal results CSV output
        model_names: Optional list of model names to filter results
    
    Returns:
        True if export was successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_significance_path.parent.mkdir(parents=True, exist_ok=True)
        output_conformal_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export significance test results
        logger.info(f"Exporting significance test results to {output_significance_path}")
        significance_df = load_and_aggregate_significance_results(
            results_dir, model_names
        )
        significance_df.to_csv(output_significance_path, index=False)
        logger.info(f"Saved {len(significance_df)} rows to significance test results")
        
        # Export conformal comparison results
        logger.info(f"Exporting conformal results to {output_conformal_path}")
        conformal_df = load_and_aggregate_conformal_results(
            results_dir, model_names
        )
        conformal_df.to_csv(output_conformal_path, index=False)
        logger.info(f"Saved {len(conformal_df)} rows to conformal results")
        
        logger.info("Successfully exported all results")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export results: {str(e)}", exc_info=True)
        return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Export significance test and conformal results to CSV"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=str(RESULTS_DIR),
        help="Path to the results directory containing intermediate files"
    )
    parser.add_argument(
        "--output-significance",
        type=str,
        default=None,
        help="Output path for significance test CSV (default: results/significance_test.csv)"
    )
    parser.add_argument(
        "--output-conformal",
        type=str,
        default=None,
        help="Output path for conformal results CSV (default: results/conformal_results.csv)"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=None,
        help="List of model names to include in the results"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir}")
        sys.exit(1)
    
    output_significance = (
        Path(args.output_significance) 
        if args.output_significance 
        else results_dir / "significance_test.csv"
    )
    output_conformal = (
        Path(args.output_conformal)
        if args.output_conformal
        else results_dir / "conformal_results.csv"
    )
    
    model_names = args.models if args.models else None
    
    # Export results
    success = export_results(
        results_dir,
        output_significance,
        output_conformal,
        model_names
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()