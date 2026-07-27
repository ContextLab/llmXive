"""
LMM Model Implementation for US2.
Computes Linear Mixed-Effects Models using statsmodels mixedlm.
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.regression.mixed_linear_model import MixedLM

# Import project utilities
from utils.config import get_project_root, get_data_path, get_output_path, set_global_seed
from utils.logger import get_logger
from utils.directories import ensure_directory

# Constants
RANDOM_SEED = 42
REQUIRED_COLUMNS = ['participant_id', 'recall_score', 'valence', 'fixation_duration', 'saccade_amplitude', 'gaze_distribution']
ATTENTION_METRICS = ['fixation_duration', 'saccade_amplitude', 'gaze_distribution']
VALENCE_CATEGORIES = ['positive', 'negative', 'neutral']  # Default, will be overridden by data if needed

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Loads the processed eye-tracking and recall data from the ingestion phase.
    Expects data to be in data/processed/merged_data.csv (standardized by US1).
    """
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "merged_data.csv"
    
    if not data_path.exists():
        logger.error(f"Processed data file not found: {data_path}")
        logger.error("US1 (Data Ingestion) must complete successfully before running US2.")
        sys.exit(1)

    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
        
        # Validate required columns exist
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in processed data: {missing_cols}")
            sys.exit(1)
        
        # Filter out rows with missing recall scores (Edge Case T025)
        initial_count = len(df)
        df = df.dropna(subset=['recall_score'] + ATTENTION_METRICS)
        dropped_count = initial_count - len(df)
        if dropped_count > 0:
            logger.warning(f"Dropped {dropped_count} rows due to missing recall or metric values.")
        
        return df
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

def fit_lmm_for_combination(df: pd.DataFrame, metric: str, valence: str) -> Dict[str, Any]:
    """
    Fits a Linear Mixed-Effects Model for a specific metric and valence category.
    Model: recall_score ~ metric + (1 | participant_id)
    """
    subset = df[df['valence'] == valence].copy()
    
    if len(subset) < 10:
        logger.warning(f"Insufficient data for {metric} in {valence} category ({len(subset)} rows). Skipping.")
        return None

    # Ensure numeric
    subset[metric] = pd.to_numeric(subset[metric], errors='coerce')
    subset = subset.dropna(subset=[metric, 'recall_score'])

    if len(subset) < 10:
        logger.warning(f"After numeric conversion, insufficient data for {metric} in {valence}. Skipping.")
        return None

    # Define formula
    formula = f"recall_score ~ {metric}"
    groups = "participant_id"

    try:
        # Fit model
        # Note: mixedlm requires 'exog' for fixed effects if using the low-level interface,
        # but using the formula interface via from_formula is cleaner.
        # However, statsmodels mixedlm does not have a direct from_formula in older versions,
        # so we construct the design matrices manually or use the high-level API if available.
        # Using the standard MixedLM.from_formula is the most robust approach if available,
        # otherwise we use the constructor.
        
        # Attempt to use from_formula (available in recent statsmodels)
        if hasattr(MixedLM, 'from_formula'):
            model = MixedLM.from_formula(formula, groups=subset[groups], data=subset)
        else:
            # Fallback for older versions: construct arrays
            # This is less clean but ensures compatibility if 'from_formula' is missing
            endog = subset['recall_score'].values
            exog = subset[[metric]].values
            groups_col = subset[groups].values
            # We need to map groups to indices for the low-level interface
            # But MixedLM constructor expects a dict of groups or a groups array
            model = MixedLM(endog, exog, groups=groups_col)

        result = model.fit()
        
        # Extract results
        # Fixed effects: intercept + metric coef
        # We are interested in the slope of the metric
        coef = result.params[metric]
        p_raw = result.pvalues[metric]
        
        return {
            "metric": metric,
            "valence": valence,
            "coef": float(coef),
            "p_raw": float(p_raw),
            "n_observations": len(subset),
            "n_groups": subset[groups].nunique()
        }
    except Exception as e:
        logger.warning(f"Failed to fit LMM for {metric} in {valence}: {e}")
        return None

def run_lmm_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Runs LMM analysis for all combinations of attention metrics and valence categories.
    """
    results = []
    
    # Determine unique valences in data if not hardcoded
    unique_valences = df['valence'].unique().tolist()
    if not unique_valences:
        logger.error("No valence categories found in data.")
        return results
    
    logger.info(f"Running LMM for {len(ATTENTION_METRICS)} metrics x {len(unique_valences)} valences.")

    for metric in ATTENTION_METRICS:
        for valence in unique_valences:
            logger.info(f"Fitting model: {metric} vs recall for {valence}")
            res = fit_lmm_for_combination(df, metric, valence)
            if res:
                results.append(res)
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Saves the LMM summary to a CSV file.
    Columns: metric, valence, coef, p_raw
    """
    if not results:
        logger.warning("No results to save.")
        return

    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "output" / "results" / "lmm_summary.csv"
    
    ensure_directory(output_path)
    
    df_results = pd.DataFrame(results)
    # Ensure column order
    cols = ['metric', 'valence', 'coef', 'p_raw']
    # Add any extra columns if present, but ensure these are first
    existing_cols = [c for c in df_results.columns if c in cols]
    other_cols = [c for c in df_results.columns if c not in cols]
    final_cols = existing_cols + other_cols
    df_results = df_results[final_cols]
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved LMM results to {output_path}")

def main():
    """
    Main entry point for T020.
    """
    set_global_seed(RANDOM_SEED)
    logger.info("Starting LMM Analysis (T020)...")
    
    # Check for data blocker condition from US1
    # We assume US1 creates a marker or we check the existence of processed data
    # The ingestion script should have exited 1 if data was missing, so if we are here, data exists.
    
    df = load_processed_data()
    
    results = run_lmm_analysis(df)
    
    if not results:
        logger.error("LMM analysis produced no results. Exiting.")
        sys.exit(1)
    
    save_results(results)
    
    logger.info("LMM Analysis (T020) completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
