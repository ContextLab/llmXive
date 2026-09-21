"""Collinearity diagnostics (VIF) for the cognitive fatigue pipeline.

Implements SC-004: Calculate Variance Inflation Factor (VIF) for all available
predictors. Identifies collinear predictors (VIF >= 5) and outputs a list of
valid predictors to be used in downstream ANCOVA models (T021).
"""
from __future__ import annotations

import os
import sys
import json
import logging
import yaml
import pandas as pd
import numpy as np

# Import from local project structure
# Note: Using relative imports is not allowed in standalone scripts,
# so we assume this script is run from the project root or code/ directory.
# If running from code/, we need to adjust sys.path.
if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, save_exclusion_log_csv
from config import load_config as load_pipeline_config

# Local imports for VIF calculation
try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    print("ERROR: statsmodels is required. Install with: pip install statsmodels")
    sys.exit(1)

# Constants
VIF_THRESHOLD = 5.0
DIAGNOSTICS_LOG_PATH = "data/analysis/vif_diagnostics.log"
VALID_PREDICTORS_JSON_PATH = "data/analysis/vif_valid_predictors.json"
CORRELATION_RESULTS_PATH = "data/analysis/correlation_results.csv"
COMPLEXITY_METRICS_PATH = "data/analysis/complexity_metrics.csv"
DELTA_SCORES_PATH = "data/analysis/delta_scores.csv"

def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Setup a logger that writes to file and console.
    
    This function is designed to be tolerant of different call signatures
    to satisfy the shared-module contract for logging utilities.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def load_config() -> dict:
    """Load pipeline configuration from code/config.yaml."""
    config_path = "code/config.yaml"
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results() -> pd.DataFrame:
    """Load the combined dataset for VIF calculation.
    
    Merges:
    1. Fatigue_Delta from delta_scores.csv
    2. Pre_Complexity (and other complexity metrics) from complexity_metrics.csv
    3. Correlation results (if needed for context)
    4. Any available covariates (age, time_of_day, medication_status)
    
    Returns a DataFrame with one row per participant and columns for all predictors.
    """
    # Load delta scores (contains Fatigue_Delta)
    if not os.path.exists(DELTA_SCORES_PATH):
        raise FileNotFoundError(f"Delta scores file not found: {DELTA_SCORES_PATH}")
    delta_df = pd.read_csv(DELTA_SCORES_PATH)
    
    # Load complexity metrics (contains Pre_Complexity, Post_Complexity, etc.)
    if not os.path.exists(COMPLEXITY_METRICS_PATH):
        raise FileNotFoundError(f"Complexity metrics file not found: {COMPLEXITY_METRICS_PATH}")
    complexity_df = pd.read_csv(COMPLEXITY_METRICS_PATH)
    
    # Identify participant IDs
    # We assume 'participant_id' is the key column
    participant_ids = delta_df['participant_id'].unique()
    
    # Initialize the combined dataframe
    combined_df = pd.DataFrame({'participant_id': participant_ids})
    
    # Merge Fatigue_Delta
    if 'fatigue_delta' in delta_df.columns:
        combined_df = combined_df.merge(
            delta_df[['participant_id', 'fatigue_delta']],
            on='participant_id',
            how='left'
        )
        combined_df.rename(columns={'fatigue_delta': 'Fatigue_Delta'}, inplace=True)
    elif 'Fatigue_Delta' in delta_df.columns:
        combined_df = combined_df.merge(
            delta_df[['participant_id', 'Fatigue_Delta']],
            on='participant_id',
            how='left'
        )
    else:
        # Try to find a column that looks like fatigue delta
        fatigue_cols = [c for c in delta_df.columns if 'fatigue' in c.lower() and 'delta' in c.lower()]
        if fatigue_cols:
            combined_df = combined_df.merge(
                delta_df[['participant_id', fatigue_cols[0]]],
                on='participant_id',
                how='left'
            )
            combined_df.rename(columns={fatigue_cols[0]: 'Fatigue_Delta'}, inplace=True)
        else:
            raise ValueError("Could not find Fatigue_Delta column in delta_scores.csv")
    
    # Merge Pre_Complexity
    # We need to aggregate complexity metrics per participant to get a single Pre_Complexity value
    # Assuming 'segment_id' or similar indicates pre/post
    pre_complexity_cols = [c for c in complexity_df.columns if 'pre' in c.lower() and 'complexity' in c.lower()]
    if pre_complexity_cols:
        # Use the first matching column, or aggregate if multiple
        # For simplicity, we'll take the mean across channels for pre-segments
        # But first we need to identify which rows are 'pre'
        # Assuming 'segment_id' contains 'pre' or 'post'
        if 'segment_id' in complexity_df.columns:
            pre_rows = complexity_df[complexity_df['segment_id'].str.contains('pre', case=False, na=False)]
            if not pre_rows.empty:
                # Aggregate by participant_id: mean of all pre complexity values
                pre_agg = pre_rows.groupby('participant_id').mean(numeric_only=True)
                # Find complexity columns
                complexity_cols = [c for c in pre_agg.columns if 'complexity' in c.lower() or 'lzc' in c.lower() or 'pe' in c.lower()]
                if complexity_cols:
                    # Create a single Pre_Complexity column as the mean of all complexity metrics
                    pre_agg['Pre_Complexity'] = pre_agg[complexity_cols].mean(axis=1)
                    combined_df = combined_df.merge(
                        pre_agg[['Pre_Complexity']],
                        left_on='participant_id',
                        right_index=True,
                        how='left'
                    )
            else:
                # Fallback: just take mean of all complexity for each participant
                # This is less ideal but prevents failure
                all_agg = complexity_df.groupby('participant_id').mean(numeric_only=True)
                complexity_cols = [c for c in all_agg.columns if 'complexity' in c.lower() or 'lzc' in c.lower() or 'pe' in c.lower()]
                if complexity_cols:
                    all_agg['Pre_Complexity'] = all_agg[complexity_cols].mean(axis=1)
                    combined_df = combined_df.merge(
                        all_agg[['Pre_Complexity']],
                        left_on='participant_id',
                        right_index=True,
                        how='left'
                    )
        else:
            # No segment_id, just aggregate all complexity metrics per participant
            all_agg = complexity_df.groupby('participant_id').mean(numeric_only=True)
            complexity_cols = [c for c in all_agg.columns if 'complexity' in c.lower() or 'lzc' in c.lower() or 'pe' in c.lower()]
            if complexity_cols:
                all_agg['Pre_Complexity'] = all_agg[complexity_cols].mean(axis=1)
                combined_df = combined_df.merge(
                    all_agg[['Pre_Complexity']],
                    left_on='participant_id',
                    right_index=True,
                    how='left'
                )
    else:
        # Fallback: try to find any complexity column and treat it as Pre_Complexity
        complexity_cols = [c for c in complexity_df.columns if 'complexity' in c.lower() or 'lzc' in c.lower() or 'pe' in c.lower()]
        if complexity_cols:
            all_agg = complexity_df.groupby('participant_id')[complexity_cols].mean()
            all_agg['Pre_Complexity'] = all_agg.mean(axis=1)
            combined_df = combined_df.merge(
                all_agg[['Pre_Complexity']],
                left_on='participant_id',
                right_index=True,
                how='left'
            )
    
    # Drop rows with missing values in key predictors
    key_cols = ['Fatigue_Delta', 'Pre_Complexity']
    combined_df = combined_df.dropna(subset=key_cols)
    
    # Check for covariates
    covariates = ['age', 'time_of_day', 'medication_status']
    # Try to find these in delta_df or complexity_df
    for cov in covariates:
        if cov in delta_df.columns:
            combined_df = combined_df.merge(
                delta_df[['participant_id', cov]],
                on='participant_id',
                how='left'
            )
        elif cov in complexity_df.columns:
            # Aggregate covariates if they exist in complexity metrics
            cov_agg = complexity_df.groupby('participant_id')[cov].first()
            combined_df = combined_df.merge(
                cov_agg.to_frame(),
                left_on='participant_id',
                right_index=True,
                how='left'
            )
    
    # Drop rows with any NaN in potential predictors
    combined_df = combined_df.dropna()
    
    if combined_df.empty:
        raise ValueError("No valid data rows after merging and dropping NaNs. Check input files.")
    
    return combined_df

def calculate_vif(df: pd.DataFrame, predictor_cols: list) -> dict:
    """Calculate VIF for each predictor in the list.
    
    Args:
        df: DataFrame containing all variables
        predictor_cols: List of column names to calculate VIF for
    
    Returns:
        Dictionary mapping predictor name to VIF value
    """
    if len(predictor_cols) < 2:
        return {col: 0.0 for col in predictor_cols}
    
    # Add intercept column for VIF calculation
    X = df[predictor_cols].copy()
    X['intercept'] = 1.0
    
    vif_results = {}
    for col in predictor_cols:
        # VIF for a variable is 1 / (1 - R^2) where R^2 is from regressing 
        # that variable against all other independent variables
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_results[col] = float(vif)
        except Exception as e:
            print(f"Warning: Could not calculate VIF for {col}: {e}")
            vif_results[col] = float('inf')
    
    return vif_results

def run_collinearity_diagnostics(df: pd.DataFrame, logger: logging.Logger) -> tuple[list, dict]:
    """Run VIF analysis and determine valid predictors.
    
    Args:
        df: DataFrame with all predictors
        logger: Logger instance
    
    Returns:
        Tuple of (list of valid predictors, dict of all VIF values)
    """
    # Identify predictors: Fatigue_Delta, Pre_Complexity, and any covariates
    base_predictors = ['Fatigue_Delta', 'Pre_Complexity']
    covariates = ['age', 'time_of_day', 'medication_status']
    
    # Filter to only available columns
    available_predictors = [col for col in base_predictors if col in df.columns]
    available_covariates = [col for col in covariates if col in df.columns]
    
    all_predictors = available_predictors + available_covariates
    
    if len(all_predictors) < 2:
        logger.warning(f"Insufficient predictors for VIF calculation. Found: {all_predictors}")
        # If we have less than 2 predictors, VIF is not meaningful
        # Return all as valid (no multicollinearity possible with <2 predictors)
        return all_predictors, {col: 0.0 for col in all_predictors}
    
    # Calculate VIF
    vif_results = calculate_vif(df, all_predictors)
    
    # Log results
    logger.info("VIF Diagnostics Results:")
    for pred, vif_val in vif_results.items():
        status = "PASS" if vif_val < VIF_THRESHOLD else "FAIL"
        logger.info(f"  {pred}: VIF = {vif_val:.4f} [{status}]")
    
    # Determine valid predictors
    valid_predictors = [pred for pred, vif_val in vif_results.items() if vif_val < VIF_THRESHOLD]
    
    # Log warnings for collinear predictors
    collinear = [pred for pred, vif_val in vif_results.items() if vif_val >= VIF_THRESHOLD]
    if collinear:
        logger.warning(f"Collinear predictors detected (VIF >= {VIF_THRESHOLD}): {collinear}")
        logger.warning(f"These predictors will be excluded from the ANCOVA model.")
    
    return valid_predictors, vif_results

def save_collinearity_report(valid_predictors: list, vif_results: dict, logger: logging.Logger):
    """Save VIF diagnostics to log and valid predictors to JSON."""
    
    # Write diagnostics log
    with open(DIAGNOSTICS_LOG_PATH, 'w') as f:
        f.write("VIF Collinearity Diagnostics Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Threshold: VIF < {VIF_THRESHOLD}\n")
        f.write(f"Total predictors tested: {len(vif_results)}\n")
        f.write(f"Valid predictors: {len(valid_predictors)}\n\n")
        f.write("Detailed Results:\n")
        for pred, vif_val in vif_results.items():
            status = "VALID" if vif_val < VIF_THRESHOLD else "COLLINEAR"
            f.write(f"  {pred}: VIF = {vif_val:.4f} [{status}]\n")
        
        if len(valid_predictors) == 0:
            f.write("\nWARNING: No valid predictors found. All predictors are collinear.\n")
            f.write("The ANCOVA model cannot be run without valid predictors.\n")
    
    logger.info(f"VIF diagnostics written to {DIAGNOSTICS_LOG_PATH}")
    
    # Write valid predictors JSON
    output_data = {
        "valid_predictors": valid_predictors,
        "vif_threshold": VIF_THRESHOLD,
        "all_vif_values": {k: v for k, v in vif_results.items()}
    }
    
    with open(VALID_PREDICTORS_JSON_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Valid predictors saved to {VALID_PREDICTORS_JSON_PATH}")

def main():
    """Main entry point for collinearity diagnostics."""
    print("Starting Collinearity Diagnostics (VIF) Pipeline...")
    
    # Setup logger
    logger = setup_logger("collinearity")
    
    try:
        # Load configuration
        config = load_config()
        logger.info(f"Loaded config: {config}")
        
        # Load and prepare data
        logger.info("Loading analysis results...")
        df = load_analysis_results()
        logger.info(f"Loaded {len(df)} participants with {len(df.columns)} columns")
        
        # Run diagnostics
        logger.info("Calculating VIF...")
        valid_predictors, vif_results = run_collinearity_diagnostics(df, logger)
        
        # Save results
        save_collinearity_report(valid_predictors, vif_results, logger)
        
        # Final summary
        logger.info(f"VIF diagnostics complete. {len(valid_predictors)} valid predictors found.")
        logger.info(f"Valid predictors: {valid_predictors}")
        
        print("Collinearity diagnostics completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
