from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

# Import project utilities
# Note: utils.logging is the canonical logger provider
try:
    from utils.logging import get_logger, log_operation
except ImportError:
    # Fallback for direct execution or missing utils
    def get_logger(*args, **kwargs):
        class DummyLogger:
            def info(self, *a, **k): pass
            def error(self, *a, **k): pass
            def warning(self, *a, **k): pass
            def debug(self, *a, **k): pass
        return DummyLogger()
    
    def log_operation(*args, **kwargs):
        return None

# --- Configuration & Setup ---

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Configure a standard logging.Logger for the pipeline."""
    logger = get_logger(name)
    if isinstance(logger, logging.Logger):
        return logger
    
    # If the custom logger is used, we wrap it or return a standard one for compatibility
    # with statsmodels which expects a stdlib logger.
    std_logger = logging.getLogger(name)
    if not std_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        std_logger.addHandler(handler)
        std_logger.setLevel(logging.INFO)
    
    return std_logger

def load_config() -> dict:
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        # Fallback defaults if config is missing
        return {
            "filter_low": 1.0,
            "filter_high": 40.0,
            "random_seed": 42,
            "notch_frequency": 50.0
        }
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# --- Validation & Data Loading ---

def validate_inputs(logger) -> bool:
    """
    Validate that all required input files exist before proceeding.
    Required:
      1. data/analysis/vif_valid_predictors.json (T024 Success Gate)
      2. data/analysis/complexity_metrics.csv (T016)
      3. data/analysis/delta_scores.csv (T019)
    """
    required_files = [
        "data/analysis/vif_valid_predictors.json",
        "data/analysis/complexity_metrics.csv",
        "data/analysis/delta_scores.csv"
    ]
    
    missing = []
    for f in required_files:
        if not Path(f).exists():
            missing.append(f)
    
    if missing:
        logger.error(f"Required input files missing: {missing}")
        logger.error("Pipeline halted. Ensure T024 (VIF), T016 (Features), and T019 (Deltas) completed successfully.")
        return False
    
    logger.info("All required input files found.")
    return True

def load_vif_validators(logger) -> List[str]:
    """
    Load the list of valid predictors from T024 output.
    Exits with code 1 if file is missing or empty.
    """
    path = Path("data/analysis/vif_valid_predictors.json")
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        valid_predictors = data.get("valid_predictors", [])
        
        if not valid_predictors:
            logger.error("VIF validation returned an empty list of valid predictors.")
            logger.error("No valid predictors for ANCOVA. Pipeline halted per SC-004.")
            sys.exit(1)
        
        logger.info(f"Loaded {len(valid_predictors)} valid predictors from VIF diagnostics.")
        return valid_predictors
    except Exception as e:
        logger.error(f"Failed to load VIF validators: {e}")
        sys.exit(1)

def load_complexity_metrics(logger) -> pd.DataFrame:
    """Load complexity metrics from T016 output."""
    path = Path("data/analysis/complexity_metrics.csv")
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded complexity metrics: {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load complexity metrics: {e}")
        sys.exit(1)

def load_delta_scores(logger) -> pd.DataFrame:
    """Load delta scores from T019 output."""
    path = Path("data/analysis/delta_scores.csv")
    try:
        df = pd.read_csv(path)
        logger.info(f"Loaded delta scores: {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load delta scores: {e}")
        sys.exit(1)

# --- ANCOVA Implementation ---

def run_ancova_model(
    complexity_df: pd.DataFrame,
    delta_df: pd.DataFrame,
    valid_predictors: List[str],
    logger
) -> pd.DataFrame:
    """
    Fit the ANCOVA model: Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates.
    
    Logic:
    1. Merge complexity and delta data on participant_id.
    2. Filter predictors to only those in valid_predictors.
    3. Check for covariates (age, time_of_day, medication_status) in the merged data.
    4. Fit OLS model using statsmodels.
    5. Return summary table.
    """
    
    # 1. Merge Data
    # We need Post_Complexity (from complexity_df) and Fatigue_Delta (from delta_df)
    # complexity_df likely has columns: participant_id, channel, segment_id, lzc_value, pe_value
    # We need to identify which column is the 'Post' complexity. 
    # Assuming 'segment_id' distinguishes pre/post or we have specific columns.
    # Based on T019 logic, delta_df has Fatigue_Delta.
    # We need to align Pre_Complexity and Post_Complexity.
    
    # Assumption: complexity_df has 'segment_id' (e.g., 'pre', 'post') or specific columns.
    # Let's assume the standard structure from T016:
    # participant_id, channel, segment_id, lzc_value, pe_value
    
    if 'segment_id' not in complexity_df.columns:
        logger.error("complexity_metrics.csv must contain 'segment_id' to distinguish pre/post.")
        sys.exit(1)

    # Pivot to wide format for pre/post if necessary, or filter
    # For simplicity, assuming we want to model the 'post' complexity.
    # We need to join 'pre' complexity as a covariate.
    
    pre_data = complexity_df[complexity_df['segment_id'] == 'pre'][['participant_id', 'channel', 'lzc_value']].copy()
    pre_data.rename(columns={'lzc_value': 'Pre_Complexity'}, inplace=True)
    
    post_data = complexity_df[complexity_df['segment_id'] == 'post'][['participant_id', 'channel', 'lzc_value']].copy()
    post_data.rename(columns={'lzc_value': 'Post_Complexity'}, inplace=True)
    
    # Merge pre and post on participant_id and channel
    merged = post_data.merge(pre_data, on=['participant_id', 'channel'], how='inner')
    
    # Merge with delta scores (Fatigue_Delta)
    # delta_df should have participant_id, Fatigue_Delta
    if 'Fatigue_Delta' not in delta_df.columns:
        logger.error("delta_scores.csv must contain 'Fatigue_Delta'.")
        sys.exit(1)
        
    merged = merged.merge(delta_df[['participant_id', 'Fatigue_Delta']], on='participant_id', how='inner')
    
    if merged.empty:
        logger.error("No overlapping data found between complexity and delta scores.")
        sys.exit(1)
    
    logger.info(f"Merged dataset size: {len(merged)} rows.")
    
    # 2. Identify Predictors
    # Base predictors: Fatigue_Delta, Pre_Complexity
    # Covariates: age, time_of_day, medication_status (if present)
    
    base_predictors = ['Fatigue_Delta', 'Pre_Complexity']
    
    # Filter valid_predictors to only those present in the dataframe
    available_cols = set(merged.columns)
    valid_base = [p for p in base_predictors if p in available_cols]
    
    if len(valid_base) != len(base_predictors):
        logger.warning(f"Missing base predictors in data: {set(base_predictors) - set(valid_base)}")
        # If Pre_Complexity is missing, we can't do ANCOVA as defined.
        if 'Pre_Complexity' not in valid_base:
            logger.error("Pre_Complexity is missing. Cannot run ANCOVA.")
            sys.exit(1)
    
    # Check for covariates
    covariates = []
    for cov in ['age', 'time_of_day', 'medication_status']:
        if cov in available_cols:
            covariates.append(cov)
        else:
            logger.debug(f"Covariate '{cov}' not found in data. Skipping.")
    
    # Construct formula
    # Formula: Post_Complexity ~ Fatigue_Delta + Pre_Complexity + [Covariates]
    # Ensure all selected predictors are valid
    final_predictors = [p for p in valid_predictors if p in available_cols]
    
    # If the user specified predictors in vif_validators that aren't in our base/covariates,
    # we should try to include them if they exist in the data.
    # However, the model definition is specific: Post ~ Fatigue_Delta + Pre + Covariates.
    # We will use the intersection of valid_predictors and available columns.
    
    model_predictors = [p for p in final_predictors if p in available_cols]
    
    # Ensure base predictors are in the model if they are valid
    for p in valid_base:
        if p not in model_predictors:
            model_predictors.append(p)
    
    if not model_predictors:
        logger.error("No valid predictors found for the model.")
        sys.exit(1)
    
    formula = f"Post_Complexity ~ {' + '.join(model_predictors)}"
    logger.info(f"Fitting ANCOVA model with formula: {formula}")
    
    # 3. Fit Model
    try:
        # Handle categorical variables if any (e.g., medication_status)
        # For now, assume numeric or let statsmodels handle it if it's a string category
        model = ols(formula, data=merged).fit()
        logger.info("Model fitted successfully.")
    except Exception as e:
        logger.error(f"Failed to fit ANCOVA model: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    
    # 4. Extract Results
    results_df = model.summary2().tables[1]
    # Convert summary table to a cleaner DataFrame for output
    # summary2 tables are a bit messy, let's use params, pvalues, etc.
    
    output_data = []
    for var in model_predictors:
        row = {
            'predictor': var,
            'coefficient': model.params[var],
            'std_error': model.bse[var],
            't_statistic': model.tvalues[var],
            'p_value': model.pvalues[var]
        }
        # Add confidence interval if needed, but p-value is critical
        output_data.append(row)
    
    # Also add intercept if present
    if 'Intercept' in model.params:
        output_data.append({
            'predictor': 'Intercept',
            'coefficient': model.params['Intercept'],
            'std_error': model.bse['Intercept'],
            't_statistic': model.tvalues['Intercept'],
            'p_value': model.pvalues['Intercept']
        })
    
    results_df = pd.DataFrame(output_data)
    return results_df

def save_ancova_results(results_df: pd.DataFrame, logger) -> str:
    """Save ANCOVA results to data/analysis/ancova_results.csv."""
    output_path = "data/analysis/ancova_results.csv"
    try:
        results_df.to_csv(output_path, index=False)
        logger.info(f"ANCOVA results saved to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save ANCOVA results: {e}")
        sys.exit(1)

# --- Main Entry Point ---

def main():
    parser = argparse.ArgumentParser(description="Run ANCOVA analysis for Cognitive Fatigue Study (T021)")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    args = parser.parse_args()

    logger = setup_logger("analysis_ancova")
    logger.info("Starting ANCOVA Analysis Pipeline (T021).")

    # 1. Validate Inputs
    if not validate_inputs(logger):
        sys.exit(1)

    # 2. Load Valid Predictors (Gate from T024)
    valid_predictors = load_vif_validators(logger)

    # 3. Load Data
    complexity_df = load_complexity_metrics(logger)
    delta_df = load_delta_scores(logger)

    # 4. Run Model
    results_df = run_ancova_model(complexity_df, delta_df, valid_predictors, logger)

    # 5. Save Output
    save_ancova_results(results_df, logger)

    logger.info("ANCOVA Analysis completed successfully.")

if __name__ == "__main__":
    main()