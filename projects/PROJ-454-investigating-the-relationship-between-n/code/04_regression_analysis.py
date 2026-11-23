import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Any
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from statsmodels.stats.outliers_influence import variance_inflation_factor
import json

# Local imports matching API surface
from utils.logging_config import setup_data_flow_logger, get_logger
from utils.stats_utils import (
    calculate_vif, 
    fit_ols_model, 
    fdr_benjamini_hochberg, 
    calculate_partial_r,
    classify_effect_size
)
from utils.resource_monitor import get_memory_usage_gb, check_resource_limits, log_resource_snapshot
from config import get_config

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for this module."""
    return setup_data_flow_logger(name)

logger = setup_logger(__name__)

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load entropy metrics and behavioral scores.
    Returns:
        Tuple of (entropy_df, behavioral_df)
    """
    config = get_config()
    entropy_path = Path(config['data_processed_dir']) / "entropy_metrics.csv"
    behavioral_path = Path(config['data_processed_dir']) / "behavioral_scores.csv"

    if not entropy_path.exists():
        raise FileNotFoundError(f"Entropy metrics not found at {entropy_path}. Run T015 first.")
    if not behavioral_path.exists():
        raise FileNotFoundError(f"Behavioral scores not found at {behavioral_path}. Run T012c first.")

    entropy_df = pd.read_csv(entropy_path)
    behavioral_df = pd.read_csv(behavioral_path)

    # Merge on participant_id
    merged = pd.merge(entropy_df, behavioral_df, on='participant_id', how='inner')
    logger.info(f"Loaded {len(merged)} participants for regression analysis.")
    return merged

def prepare_features(data: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Prepare features for OLS regression.
    - Selects entropy columns (Sample and Approximate) for all bands.
    - Adds covariates: Age, Education, Task Accuracy, Neurological Condition, Medication Use.
    - Handles missing values by dropping rows.
    """
    # Identify entropy columns (assuming naming convention: {metric}_{band})
    # Based on T015 output: SampleEntropy_Delta, SampleEntropy_Theta, etc.
    entropy_cols = [col for col in data.columns if 'Entropy' in col]
    
    # Define covariates based on T020a spec
    covariates = ['age', 'education_years', 'task_accuracy', 'neurological_condition', 'medication_use']
    
    # Check presence
    missing_covs = [c for c in covariates if c not in data.columns]
    if missing_covs:
        logger.warning(f"Missing covariates in data: {missing_covs}. Dropping them.")
        covariates = [c for c in covariates if c in data.columns]
    
    feature_cols = entropy_cols + covariates
    
    # Drop rows with NaN in any feature or target
    # Target is wcst_perseverative_errors (from T012b validation)
    target_col = 'wcst_perseverative_errors'
    if target_col not in data.columns:
        raise ValueError(f"Target column '{target_col}' not found in data.")
    
    clean_data = data[feature_cols + [target_col]].dropna()
    logger.info(f"Prepared {len(clean_data)} rows for regression after dropping NaNs.")
    return clean_data

def run_ols_for_metric(data: pd.DataFrame, metric_col: str, target_col: str) -> Dict[str, Any]:
    """
    Run a single OLS regression for one entropy metric against target.
    Returns a dict with results or None if VIF check fails for this specific run context.
    """
    predictors = [c for c in data.columns if c != target_col]
    X = add_constant(data[predictors])
    y = data[target_col]

    try:
        model = OLS(y, X).fit()
        partial_r = calculate_partial_r(model, metric_col)
        p_val = model.pvalues[metric_col]
        coef = model.params[metric_col]
        
        return {
            "metric": metric_col,
            "coefficient": coef,
            "p_value": p_val,
            "partial_r": partial_r,
            "n": len(y),
            "r_squared": model.rsquared
        }
    except Exception as e:
        logger.error(f"OLS failed for {metric_col}: {e}")
        return None

def run_vif_check_and_fdr(data: pd.DataFrame, target_col: str, snr_threshold: float = 5.0, artifact_threshold: float = 10.0) -> pd.DataFrame:
    """
    Core logic for T020a + T021 + T028 sensitivity sweep.
    
    1. Calculates VIF for all predictors.
    2. If VIF > 5 for any Approximate Entropy metric, drops ALL Approximate Entropy metrics.
    3. Runs OLS for remaining metrics.
    4. Applies FDR correction to p-values.
    5. Returns a DataFrame of results.
    
    Parameters:
        snr_threshold: The SNR threshold (in dB) used for this run.
        artifact_threshold: The artifact threshold used for this run.
    """
    # Filter data by thresholds if columns exist (simulating the exclusion logic from T016/T014)
    # Note: In a full pipeline, this data would already be filtered. 
    # Here we apply the threshold filter dynamically for the sensitivity sweep.
    filtered_data = data.copy()
    
    # If SNR column exists, filter
    if 'snr_db' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['snr_db'] >= snr_threshold]
    
    # If artifact column exists (e.g., artifact_score), filter
    if 'artifact_score' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['artifact_score'] <= artifact_threshold]

    if len(filtered_data) < 10:
        logger.warning(f"Insufficient data points ({len(filtered_data)}) for regression with current thresholds.")
        return pd.DataFrame()

    # Identify entropy metrics
    entropy_cols = [col for col in filtered_data.columns if 'Entropy' in col]
    
    # VIF Check (T021 Logic)
    # We check VIF on the full set of predictors first
    predictors = [c for c in filtered_data.columns if c != target_col]
    X_vif = add_constant(filtered_data[predictors])
    
    vif_results = calculate_vif(X_vif)
    logger.info(f"VIF Check Results: {vif_results}")
    
    # Check if any Approximate Entropy metric has VIF > 5
    apen_cols = [c for c in entropy_cols if 'Approximate' in c]
    high_vif_apen = False
    for col in apen_cols:
        if col in vif_results:
            if vif_results[col] > 5.0:
                high_vif_apen = True
                logger.warning(f"VIF for {col} is {vif_results[col]:.2f} > 5. Dropping all Approximate Entropy metrics.")
                break
    
    # If high VIF found, drop ApEn columns
    if high_vif_apen:
        final_predictors = [c for c in predictors if 'Approximate' not in c]
    else:
        final_predictors = predictors

    # Re-run OLS with reduced set if needed
    X = add_constant(filtered_data[final_predictors])
    y = filtered_data[target_col]
    
    if len(X) < 2:
        return pd.DataFrame()

    try:
        model = OLS(y, X).fit()
    except Exception as e:
        logger.error(f"OLS fitting failed with reduced predictors: {e}")
        return pd.DataFrame()

    # Extract results for each metric in the final set
    results = []
    metrics_in_model = [c for c in final_predictors if 'Entropy' in c]
    
    for metric in metrics_in_model:
        p_val = model.pvalues[metric]
        coef = model.params[metric]
        partial_r = calculate_partial_r(model, metric)
        effect_class = classify_effect_size(partial_r)
        
        results.append({
            "metric": metric,
            "coefficient": coef,
            "p_value": p_val,
            "partial_r": partial_r,
            "effect_size_class": effect_class,
            "n": len(y),
            "snr_threshold": snr_threshold,
            "artifact_threshold": artifact_threshold
        })

    if not results:
        return pd.DataFrame()

    results_df = pd.DataFrame(results)

    # FDR Correction (T021)
    # Apply FDR to p-values within this specific regression run
    if len(results_df) > 0:
        corrected_p = fdr_benjamini_hochberg(results_df['p_value'].values)
        results_df['p_value_fdr'] = corrected_p
    
    return results_df

def save_results(results_df: pd.DataFrame, output_path: Path):
    """Save results to CSV."""
    if results_df.empty:
        logger.warning("No results to save.")
        return
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")

def main():
    """
    Main entry point for T028: Threshold Sensitivity Sweep.
    
    This function implements an iterative loop that re-runs the ENTIRE regression pipeline
    (T020a + T021 logic) for each offset value of:
    1. Artifact rejection threshold
    2. SNR threshold
    
    Output: data/processed/sensitivity_threshold_results.csv
    """
    config = get_config()
    base_snr = config.get('SNR_THRESHOLD', 5.0)
    base_artifact = config.get('ARTIFACT_THRESHOLD', 10.0) # Assuming a default or config value
    
    # Define sweep values (Offsets from baseline as per T028 description)
    # Offsets: 0.0, 0.05, 0.1 (interpreted as relative offsets or absolute steps)
    # Given the units (dB for SNR, arbitrary units for artifact), we interpret these as absolute offsets 
    # or relative multipliers. The spec says "Offsets from baseline".
    # We will use absolute offsets: -0.1, 0.0, +0.1 to cover the range {0.0, 0.05, 0.1} as steps?
    # Actually, T028 says: "Sweep Values: Artifact rejection threshold: Offsets from baseline. SNR threshold: Offsets from baseline."
    # And "Implement an iterative loop... for each offset value".
    # Let's define offsets as: [-0.1, 0.0, 0.1] relative to the base threshold.
    offsets = [-0.1, 0.0, 0.1] 
    
    # If the spec meant specific values {0.0, 0.05, 0.1} as the offsets themselves:
    # offsets = [0.0, 0.05, 0.1]
    # We will use the latter interpretation to match the "Sweep Values" description exactly.
    offsets = [0.0, 0.05, 0.1]

    all_results = []
    target_col = 'wcst_perseverative_errors'

    # Load base data
    try:
        full_data = load_data()
    except FileNotFoundError as e:
        logger.error(f"Cannot run sensitivity sweep: {e}")
        return

    logger.info(f"Starting Threshold Sensitivity Sweep. Offsets: {offsets}")

    for offset in offsets:
        # Calculate current thresholds
        current_snr = base_snr + offset
        current_artifact = base_artifact + offset # Assuming same offset logic applies to both

        logger.info(f"--- Running Sweep: SNR={current_snr:.2f}, Artifact={current_artifact:.2f} ---")
        
        # Check resources
        log_resource_snapshot()
        if not check_resource_limits():
            logger.error("Resource limits exceeded. Aborting sweep.")
            break

        # Run the full regression pipeline for this threshold set
        # This encapsulates T020a (OLS) and T021 (VIF/FDR) logic
        results = run_vif_check_and_fdr(
            data=full_data, 
            target_col=target_col, 
            snr_threshold=current_snr, 
            artifact_threshold=current_artifact
        )

        if not results.empty:
            all_results.append(results)
        else:
            logger.warning(f"No results for SNR={current_snr}, Artifact={current_artifact}")

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        output_path = Path(config['data_processed_dir']) / "sensitivity_threshold_results.csv"
        save_results(final_df, output_path)
        logger.info("Sensitivity sweep complete.")
    else:
        logger.error("Sensitivity sweep produced no results.")

if __name__ == "__main__":
    main()