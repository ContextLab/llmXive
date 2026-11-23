import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any

from fit import fit_all_galaxies
from metrics import compute_fit_metrics
from utils import get_logger, ensure_directory
from config import get_config

def load_fit_results(galaxy_data_path: Path, models: List[str] = ["mond", "nfw"]) -> pd.DataFrame:
    """
    Loads filtered galaxy data, performs fitting for specified models,
    and returns a DataFrame of fit results.
    
    This function orchestrates the fitting process (T023) and metric calculation (T024)
    to produce the raw data needed for the summary.
    """
    logger = get_logger(__name__)
    
    if not galaxy_data_path.exists():
        logger.error(f"Upstream artifact missing: {galaxy_data_path}. Cannot generate fit summary.")
        raise FileNotFoundError(f"Upstream artifact missing: {galaxy_data_path}")

    df_galaxies = pd.read_csv(galaxy_data_path)
    logger.info(f"Loaded {len(df_galaxies)} galaxies from {galaxy_data_path}")

    results = []

    for _, row in df_galaxies.iterrows():
        galaxy_name = row['galaxy_name']
        r = row['radial_distance']
        v = row['velocity']
        v_err = row['velocity_error']
        
        # Convert string representations of lists to numpy arrays if necessary
        if isinstance(r, str):
            r = np.fromstring(r.strip('[]'), sep=',')
        if isinstance(v, str):
            v = np.fromstring(v.strip('[]'), sep=',')
        if isinstance(v_err, str):
            v_err = np.fromstring(v_err.strip('[]'), sep=',')

        if len(r) == 0 or len(v) == 0:
            logger.warning(f"Skipping {galaxy_name}: Empty data arrays.")
            continue

        for model_name in models:
            try:
                # Fit the model
                fit_result = fit_all_galaxies(
                    r=r, 
                    v=v, 
                    v_err=v_err, 
                    model_name=model_name,
                    galaxy_name=galaxy_name
                )
                
                if fit_result is None or 'status' not in fit_result or fit_result['status'] != 'success':
                    logger.warning(f"Fitting failed for {galaxy_name} ({model_name}). Skipping metric calc.")
                    continue

                # Compute metrics
                metrics = compute_fit_metrics(
                    y_obs=v,
                    y_pred=fit_result['y_pred'],
                    y_err=v_err,
                    n_params=fit_result['n_params'],
                    n_points=len(v)
                )

                result_row = {
                    'galaxy_name': galaxy_name,
                    'model': model_name,
                    'chi2_reduced': metrics['chi2_reduced'],
                    'aic': metrics['aic'],
                    'bic': metrics['bic'],
                    'n_params': fit_result['n_params'],
                    'n_points': len(v),
                    'converged': fit_result.get('converged', False)
                }
                
                # Add specific parameter estimates if available
                if 'params' in fit_result:
                    for k, v_val in fit_result['params'].items():
                        result_row[f'param_{k}'] = v_val

                results.append(result_row)

            except Exception as e:
                logger.error(f"Error processing {galaxy_name} ({model_name}): {e}", exc_info=True)
                continue

    if not results:
        logger.error("No fit results generated. Check upstream data and fitting logic.")
        return pd.DataFrame()

    return pd.DataFrame(results)

def aggregate_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optional: Aggregate metrics if needed (e.g., mean chi2 per model).
    Currently returns the full detailed dataframe as required by T025.
    """
    return df

def write_fit_summary(df: pd.DataFrame, output_path: Path) -> None:
    """
    Writes the fit summary DataFrame to a CSV file.
    """
    ensure_directory(output_path.parent)
    df.to_csv(output_path, index=False)
    logging.info(f"Fit summary written to {output_path}")

def main():
    logger = get_logger(__name__)
    config = get_config()
    
    # Define paths based on project structure
    input_path = Path("data/processed/filtered_galaxies.csv")
    output_path = Path("results/fit_summary.csv")
    
    # Verify upstream artifact exists
    if not input_path.exists():
        logger.error(f"FATAL: Upstream artifact missing: {input_path}. T025 cannot proceed.")
        logger.error("Ensure T015 (filtered_galaxies.csv) and T023/T024 (fitting/metrics) are complete.")
        exit(1)

    try:
        logger.info("Generating fit summary...")
        df_results = load_fit_results(input_path)
        
        if df_results.empty:
            logger.error("FATAL: No fit results generated. Aborting.")
            exit(1)

        write_fit_summary(df_results, output_path)
        logger.info("T025 completed successfully.")

    except Exception as e:
        logger.error(f"FATAL: Unexpected error during T025 execution: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()