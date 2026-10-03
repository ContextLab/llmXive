"""
Generate fit_summary.csv with all metrics per galaxy-model.

This script loads the results from the fitting engine (fit_all_galaxies output),
aggregates the metrics (reduced chi2, AIC, BIC) for both MOND and NFW models,
and writes a summary CSV to results/fit_summary.csv.

Dependency: T023 (fitting engine) and T024 (metric calculator) must be complete.
"""

import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any

# Import from existing API surface
from fit import fit_all_galaxies
from metrics import compute_fit_metrics
from utils import get_logger, ensure_directory, log_stage
from config import get_config

logger = get_logger(__name__)


def load_fit_results(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Load fit results from the results directory.

    The fitting engine (T023) should have saved individual fit results
    or a combined results file. We expect a file named 'fit_results.parquet'
    or 'fit_results.csv' in the results directory.

    If not found, we run the fitting engine to generate them.
    """
    results_file = results_dir / "fit_results.csv"
    
    if not results_file.exists():
        logger.warning(f"Fit results file not found at {results_file}. Running fitting engine...")
        # Run the fitting engine to generate results
        # This assumes T023 has been executed and will populate the results
        fit_all_galaxies()
        
        if not results_file.exists():
            raise FileNotFoundError(
                f"Fit results file not generated at {results_file}. "
                "Ensure the fitting engine (T023) runs successfully."
            )
    
    df = pd.read_csv(results_file)
    logger.info(f"Loaded {len(df)} fit results from {results_file}")
    return df.to_dict('records')


def aggregate_metrics(fit_results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate fit metrics into a summary table.

    Expected columns in fit_results:
    - galaxy_id
    - model_type ('mond' or 'nfw')
    - reduced_chi2
    - aic
    - bic
    - n_params
    - n_points
    - fit_status

    Returns a DataFrame with one row per (galaxy_id, model_type) pair.
    """
    summary_data = []
    
    for result in fit_results:
        summary_data.append({
            'galaxy_id': result.get('galaxy_id'),
            'model_type': result.get('model_type'),
            'reduced_chi2': result.get('reduced_chi2'),
            'aic': result.get('aic'),
            'bic': result.get('bic'),
            'n_params': result.get('n_params'),
            'n_points': result.get('n_points'),
            'fit_status': result.get('fit_status', 'unknown')
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Ensure numeric columns are numeric
    numeric_cols = ['reduced_chi2', 'aic', 'bic', 'n_params', 'n_points']
    for col in numeric_cols:
        if col in df_summary.columns:
            df_summary[col] = pd.to_numeric(df_summary[col], errors='coerce')
    
    return df_summary


def write_fit_summary(df_summary: pd.DataFrame, output_path: Path) -> None:
    """
    Write the fit summary to a CSV file.
    """
    ensure_directory(output_path.parent)
    df_summary.to_csv(output_path, index=False)
    logger.info(f"Wrote fit summary to {output_path} with {len(df_summary)} rows")


def main():
    """
    Main entry point for generating the fit summary.
    """
    log_stage("Generating fit summary")
    
    config = get_config()
    results_dir = Path(config.get('paths', {}).get('results', 'results'))
    output_file = results_dir / "fit_summary.csv"
    
    try:
        # Load or generate fit results
        fit_results = load_fit_results(results_dir)
        
        if not fit_results:
            logger.error("No fit results found. Cannot generate summary.")
            return
        
        # Aggregate metrics
        df_summary = aggregate_metrics(fit_results)
        
        # Write output
        write_fit_summary(df_summary, output_file)
        
        # Log summary statistics
        logger.info(f"Summary statistics:")
        logger.info(f"  Total fits: {len(df_summary)}")
        logger.info(f"  Unique galaxies: {df_summary['galaxy_id'].nunique()}")
        logger.info(f"  Models: {df_summary['model_type'].unique().tolist()}")
        logger.info(f"  Successful fits: {(df_summary['fit_status'] == 'success').sum()}")
        
    except Exception as e:
        logger.error(f"Failed to generate fit summary: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
