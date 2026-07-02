"""
Main entry point for the Solar Wind Correlation Pipeline.

Orchestrates the full pipeline:
1. US1: Data Acquisition & Synchronisation (download, validate, align)
2. US2: Lagged Correlation & Significance Testing (Neff, Bonferroni, thresholds)
"""
import os
import sys
import json

# Ensure code/ is in path for relative imports if running from root
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END, ACE_VARS, NOAA_VARS
from code import logger
from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_columns
from code.data.align import run_alignment
from code.analysis.correlation import run_correlation_analysis
from code.analysis.neff import calculate_neff
from code.analysis.significance import calculate_local_neff_and_pvalue


def calculate_global_thresholds(df_synced: pd.DataFrame) -> dict:
    """
    Calculate global Neff values for all variables and the global Bonferroni threshold.
    
    This function implements the logic for T025:
    1. Computes Neff for each variable in the FULL continuous series (1998-2020).
    2. Calculates the global Bonferroni divisor (30) and alpha_adj.
    3. Returns a dictionary of results.
    """
    import pandas as pd
    import numpy as np

    # Ensure we are working with the full dataset
    if df_synced.empty:
        raise ValueError("Synced dataframe is empty. Cannot calculate thresholds.")

    # Variables to process
    # ACE vars: N_p, T_p, He2+_ratio
    # NOAA vars: Kp, Dst
    all_vars = ACE_VARS + NOAA_VARS
    
    # Filter dataframe to only these columns to avoid errors
    available_vars = [v for v in all_vars if v in df_synced.columns]
    missing_vars = [v for v in all_vars if v not in df_synced.columns]
    
    if missing_vars:
        logger.warning(f"Missing variables for global threshold calculation: {missing_vars}")
        # We proceed with available variables, but note the missing ones
    
    neff_results = {}
    for var in available_vars:
        series = df_synced[var].dropna()
        if len(series) < 10:
            logger.warning(f"Not enough data points for {var} to calculate Neff. Skipping.")
            continue
        
        # Calculate Neff using the detrended method
        neff_val = calculate_neff(series)
        neff_results[var] = {
            "N": len(series),
            "neff": neff_val,
            "n_eff_ratio": neff_val / len(series) if len(series) > 0 else 0.0
        }
        logger.info(f"Global Neff for {var}: {neff_val:.2f} (N={len(series)})")

    # Global Bonferroni divisor: 3 params * 2 indices * 5 lags = 30
    # Even if some variables are missing, we use the fixed global divisor to control FWER
    # as per T023 requirement to derive 30 dynamically but use it as a fixed global count.
    # However, if variables are missing, the actual tests run are fewer. 
    # The spec says "derive the divisor 30 dynamically... regardless of actual data availability".
    # So we stick to 30.
    global_divisor = 30
    alpha = 0.05
    alpha_adj = alpha / global_divisor

    return {
        "calculation_date": datetime.now().isoformat(),
        "period": f"{TRAIN_START}-{TEST_END}",
        "global_divisor": global_divisor,
        "alpha": alpha,
        "alpha_adj": alpha_adj,
        "variables": neff_results,
        "missing_variables": missing_vars
    }


def main():
    """Execute the full pipeline: US1 -> US2 (Global Thresholds)."""
    logger.info("Starting Full Pipeline: US1 + US2 Global Thresholds")

    # Define date range based on config
    # Using the full span for the analysis as per SC-001
    start_date = datetime(TRAIN_START, 1, 1)
    end_date = datetime(TEST_END, 12, 31)

    logger.info(f"Fetching data for period: {start_date} to {end_date}")

    # --- US1: Data Acquisition & Synchronisation ---
    
    # Step 1: Fetch Data
    try:
        ace_path = fetch_ace(start_date, end_date)
        noaa_path = fetch_noaa(start_date, end_date)
        logger.info(f"Data fetched successfully. ACE: {ace_path}, NOAA: {noaa_path}")
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        sys.exit(1)

    # Step 2: Validate Data
    try:
        import pandas as pd
        df_ace = pd.read_csv(ace_path)
        df_noaa = pd.read_csv(noaa_path)

        validate_columns(df_ace, ACE_VARS)
        validate_columns(df_noaa, NOAA_VARS)

        logger.info("Data validation passed.")
    except ValueError as ve:
        logger.error(f"Validation failed: {ve}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during validation step: {e}")
        sys.exit(1)

    # Step 3: Align and Sync
    try:
        synced_path = run_alignment(ace_path, noaa_path)
        logger.info(f"Alignment complete. Output written to: {synced_path}")
    except Exception as e:
        logger.error(f"Alignment failed: {e}")
        sys.exit(1)

    # Load synced data for US2
    try:
        df_synced = pd.read_csv(synced_path, parse_dates=['timestamp'])
        logger.info(f"Loaded {len(df_synced)} rows from synced data.")
    except Exception as e:
        logger.error(f"Failed to load synced data: {e}")
        sys.exit(1)

    # --- US2: Lagged Correlation & Significance Testing ---

    # Step 4: Run Correlation Analysis (Global)
    # This computes correlations at lags 0,1,2,3,6h
    try:
        logger.info("Starting US2: Correlation Analysis")
        results_df = run_correlation_analysis(df_synced)
        
        # Save results
        output_correlation_path = "data/processed/correlation_results.csv"
        results_df.to_csv(output_correlation_path, index=False)
        logger.info(f"Correlation results saved to {output_correlation_path}")
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}")
        sys.exit(1)

    # Step 5: Calculate Global Thresholds (Neff + Bonferroni)
    # This is the core requirement of T025
    try:
        logger.info("Calculating global Neff and Bonferroni thresholds...")
        thresholds = calculate_global_thresholds(df_synced)
        
        # Save thresholds to artifacts/thresholds/global_threshold.json
        os.makedirs("artifacts/thresholds", exist_ok=True)
        threshold_path = "artifacts/thresholds/global_threshold.json"
        with open(threshold_path, "w") as f:
            json.dump(thresholds, f, indent=2)
        
        logger.info(f"Global thresholds saved to {threshold_path}")
        logger.info(f"Global Bonferroni adjusted alpha: {thresholds['alpha_adj']:.6f}")
    except Exception as e:
        logger.error(f"Failed to calculate global thresholds: {e}")
        sys.exit(1)

    logger.info("Full Pipeline completed successfully.")
    return {
        "synced_data": synced_path,
        "correlation_results": output_correlation_path,
        "global_thresholds": threshold_path
    }


if __name__ == "__main__":
    main()
