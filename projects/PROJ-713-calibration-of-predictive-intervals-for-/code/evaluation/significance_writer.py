"""
Implementation for T032: Serialize bootstrap p-values to results/significance_test.csv.

This module provides the `write_significance_results` function and a CLI entry point
to read aggregated coverage deviations and bootstrap p-values, then serialize them
to the required CSV format matching SC-004 measurement definition.

Columns: model_a, model_b, metric, p_value, significant
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import from existing project API
from config import Config, ensure_dirs, RESULTS_DIR
from utils.logger import get_logger
from utils.exceptions import DataValidationError, ConfigurationError

logger = get_logger(__name__)

def load_bootstrap_results(bootstrap_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load aggregated bootstrap results.
    
    Args:
        bootstrap_path: Path to the bootstrap results CSV. If None, uses default path.
        
    Returns:
        DataFrame with columns: model_a, model_b, metric, p_value
        
    Raises:
        DataValidationError: If file not found or schema invalid.
    """
    if bootstrap_path is None:
        bootstrap_path = str(RESULTS_DIR / "bootstrap_results.csv")
        
    path = Path(bootstrap_path)
    if not path.exists():
        raise DataValidationError(
            f"Bootstrap results file not found: {bootstrap_path}. "
            "Ensure T031a (bootstrap_test) has been executed successfully."
        )
    
    df = pd.read_csv(path)
    
    required_cols = {'model_a', 'model_b', 'metric', 'p_value'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise DataValidationError(
            f"Bootstrap results missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )
    
    logger.info(f"Loaded {len(df)} bootstrap comparison results from {path}")
    return df


def write_significance_results(
    bootstrap_df: pd.DataFrame,
    alpha: float = 0.05,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Serialize bootstrap p-values to results/significance_test.csv.
    
    This implements T032: Takes aggregated coverage deviations (via bootstrap results),
    applies the significance threshold, and writes the final table.
    
    Args:
        bootstrap_df: DataFrame from load_bootstrap_results() with p_values.
        alpha: Significance threshold (default 0.05).
        output_path: Path for output CSV. If None, uses results/significance_test.csv.
        
    Returns:
        DataFrame written to disk with columns:
            model_a, model_b, metric, p_value, significant
            
    Raises:
        ConfigurationError: If output directory cannot be created.
        DataValidationError: If input DataFrame is empty or invalid.
    """
    if bootstrap_df.empty:
        raise DataValidationError("Input bootstrap DataFrame is empty. Cannot write results.")
        
    # Validate required columns exist
    required_cols = {'model_a', 'model_b', 'metric', 'p_value'}
    if not required_cols.issubset(bootstrap_df.columns):
        missing = required_cols - set(bootstrap_df.columns)
        raise DataValidationError(
            f"Input DataFrame missing required columns: {missing}"
        )
    
    # Determine output path
    if output_path is None:
        output_path = str(RESULTS_DIR / "significance_test.csv")
    
    output_file = Path(output_path)
    
    # Ensure output directory exists
    ensure_dirs()
    
    # Compute significance
    result_df = bootstrap_df.copy()
    result_df['significant'] = result_df['p_value'] < alpha
    
    # Ensure column order matches SC-004 definition
    column_order = ['model_a', 'model_b', 'metric', 'p_value', 'significant']
    result_df = result_df[column_order]
    
    # Write to CSV
    result_df.to_csv(output_file, index=False)
    logger.info(f"Wrote significance test results to {output_file} ({len(result_df)} rows)")
    
    return result_df


def main():
    """CLI entry point for T032."""
    parser = argparse.ArgumentParser(
        description="Serialize bootstrap p-values to significance_test.csv (T032)"
    )
    parser.add_argument(
        "--bootstrap-input",
        type=str,
        default=None,
        help="Path to bootstrap_results.csv (default: results/bootstrap_results.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for significance_test.csv (default: results/significance_test.csv)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load bootstrap results
        bootstrap_df = load_bootstrap_results(args.bootstrap_input)
        
        # Write significance results
        result_df = write_significance_results(
            bootstrap_df=bootstrap_df,
            alpha=args.alpha,
            output_path=args.output
        )
        
        # Log summary
        significant_count = result_df['significant'].sum()
        logger.info(
            f"Significance analysis complete: "
            f"{significant_count}/{len(result_df)} comparisons are significant at α={args.alpha}"
        )
        
        return 0
        
    except (DataValidationError, ConfigurationError) as e:
        logger.error(f"Error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
