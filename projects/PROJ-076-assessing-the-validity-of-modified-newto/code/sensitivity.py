import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from utils import get_logger, ensure_directory
from metrics import calculate_reduced_chi2

# Define the representative set of chi2 thresholds as per SC-006
CHI2_THRESHOLDS = [1.0, 1.25, 1.5, 1.75]

def load_fit_summary(csv_path: str) -> pd.DataFrame:
    """
    Loads the fit summary CSV containing reduced chi2 values per galaxy and model.
    Expects columns: ['galaxy_id', 'model', 'reduced_chi2', ...]
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Fit summary file not found at {csv_path}. "
                                "Run T025 (fitting) before running sensitivity analysis.")
    
    df = pd.read_csv(csv_path)
    required_cols = ['galaxy_id', 'model', 'reduced_chi2']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Fit summary missing required columns: {missing}")
    
    return df

def compute_pass_rates(df: pd.DataFrame, thresholds: List[float]) -> pd.DataFrame:
    """
    Computes the pass rate (fraction of galaxies passing the chi2 threshold)
    for each model and each threshold in the provided list.
    
    A galaxy 'passes' a threshold if its reduced_chi2 <= threshold.
    """
    results = []
    
    models = df['model'].unique()
    
    for model in models:
        model_df = df[df['model'] == model]
        total_galaxies = len(model_df)
        
        if total_galaxies == 0:
            continue
        
        for threshold in thresholds:
            # Count how many galaxies have reduced_chi2 <= threshold
            passes = model_df[model_df['reduced_chi2'] <= threshold].shape[0]
            pass_rate = passes / total_galaxies
            
            results.append({
                'model': model,
                'chi2_threshold': threshold,
                'total_galaxies': total_galaxies,
                'passes': passes,
                'pass_rate': pass_rate
            })
    
    return pd.DataFrame(results)

def run_sensitivity_analysis(fit_summary_path: str, output_path: str) -> pd.DataFrame:
    """
    Main entry point for the sensitivity analysis task.
    1. Loads the fit summary from T025.
    2. Sweeps across the defined CHI2_THRESHOLDS.
    3. Calculates pass rates for each model/threshold combination.
    4. Writes the results to a CSV file.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting sensitivity analysis with thresholds: {CHI2_THRESHOLDS}")
    
    # Load data
    df = load_fit_summary(fit_summary_path)
    logger.info(f"Loaded {len(df)} fit records for {df['galaxy_id'].nunique()} galaxies.")
    
    # Compute metrics
    results_df = compute_pass_rates(df, CHI2_THRESHOLDS)
    
    # Ensure output directory exists
    ensure_directory(output_path)
    
    # Save results
    results_df.to_csv(output_path, index=False)
    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    
    return results_df

def main():
    """
    CLI entry point.
    Expects the fit summary to be at data/fit_summary.csv (or configured path).
    Outputs to results/sensitivity_data.csv.
    """
    logger = get_logger(__name__)
    logger.info("Running sensitivity analysis script.")
    
    # Define paths relative to project root
    # Assuming project root is the directory where 'code/' and 'data/' reside
    project_root = Path(__file__).resolve().parent.parent
    
    fit_summary_path = project_root / "results" / "fit_summary.csv"
    output_path = project_root / "results" / "sensitivity_data.csv"
    
    if not fit_summary_path.exists():
        logger.error(f"Required input file missing: {fit_summary_path}")
        logger.error("Please ensure T025 has been run to generate fit_summary.csv.")
        return 1
    
    try:
        run_sensitivity_analysis(str(fit_summary_path), str(output_path))
        return 0
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        raise

if __name__ == "__main__":
    import sys
    sys.exit(main())
