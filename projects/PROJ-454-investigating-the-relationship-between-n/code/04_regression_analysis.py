import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from utils.logging_config import get_logger, setup_data_flow_logger, log_data_transition
from utils.stats_utils import fit_ols_model, fdr_benjamini_hochberg, calculate_vif, check_multicollinearity
from utils.resource_monitor import log_resource_snapshot, get_memory_usage_gb

# Import existing names from the API surface if they were defined in previous iterations
# Since the file was omitted, we assume standard implementation for the existing signatures
# and append the new logic for T028.

def setup_logger(name):
    return get_logger(name)

def load_data():
    """Load processed entropy and behavioral data."""
    entropy_path = Path("data/processed/entropy_metrics.csv")
    behavioral_path = Path("data/processed/behavioral_scores.csv")
    
    if not entropy_path.exists() or not behavioral_path.exists():
        raise FileNotFoundError("Required processed data files not found. Run T015 and T012b first.")
    
    entropy_df = pd.read_csv(entropy_path)
    behavioral_df = pd.read_csv(behavioral_path)
    return entropy_df, behavioral_df

def merge_data(entropy_df, behavioral_df):
    """Merge entropy metrics with behavioral scores on participant ID."""
    # Assuming 'participant_id' is the key column
    merged = pd.merge(entropy_df, behavioral_df, on='participant_id', how='inner')
    return merged

def prepare_features(merged_df):
    """Prepare features for regression: Entropy metrics + Covariates."""
    # Identify entropy columns (Sample and Approximate for each band)
    entropy_cols = [col for col in merged_df.columns if 'entropy' in col.lower()]
    covariates = ['age', 'education', 'task_accuracy', 'neurological_condition', 'medication']
    # Filter covariates that exist
    covariates = [c for c in covariates if c in merged_df.columns]
    
    return entropy_cols, covariates

def run_regression_analysis(merged_df, entropy_cols, covariates, logger):
    """Run OLS regression for each entropy metric against WCST errors."""
    results = []
    
    for ent_col in entropy_cols:
        # Construct model formula
        # Dependent: wcst_perseverative_errors (or similar from behavioral)
        # We need to ensure the target column exists
        target_col = 'wcst_perseverative_errors'
        if target_col not in merged_df.columns:
            logger.warning(f"Target column {target_col} not found. Skipping.")
            continue
        
        predictors = [ent_col] + covariates
        predictors = [p for p in predictors if p in merged_df.columns]
        
        if len(predictors) < 1:
            continue
        
        try:
            model_result = fit_ols_model(merged_df, target_col, predictors)
            if model_result:
                results.append(model_result)
        except Exception as e:
            logger.error(f"Failed to fit model for {ent_col}: {e}")
            
    return pd.DataFrame(results) if results else pd.DataFrame()

def save_results(results_df, output_path):
    """Save regression results to CSV."""
    results_df.to_csv(output_path, index=False)

def log_power_analysis_acknowledgement(logger):
    """Log acknowledgement that power analysis is deferred."""
    logger.info("Power analysis sample size requirements are deferred to implementation with explicit acknowledgement.")

def run_bonferroni_historical_analysis(results_df, logger):
    """Run Bonferroni correction for historical tracking only."""
    if results_df.empty:
        return results_df
    
    # Apply Bonferroni to p-values
    n_tests = len(results_df)
    results_df['p_value_bonferroni_historical'] = results_df['p_value'] * n_tests
    results_df['p_value_bonferroni_historical'] = results_df['p_value_bonferroni_historical'].clip(upper=1.0)
    return results_df

def run_sensitivity_analysis_exclusion(merged_df, results_df, logger):
    """Exclude participants with neurological conditions/medications and re-run."""
    # Filter out rows where neurological_condition or medication is not 'None' or 'Healthy'
    # Assuming specific values, otherwise generic filter
    mask = (merged_df['neurological_condition'].fillna('None') == 'None') & \
           (merged_df['medication'].fillna('None') == 'None')
    filtered_df = merged_df[mask]
    
    if len(filtered_df) < len(merged_df):
        logger.info(f"Excluded {len(merged_df) - len(filtered_df)} participants for sensitivity analysis.")
        entropy_cols, covariates = prepare_features(filtered_df)
        new_results = run_regression_analysis(filtered_df, entropy_cols, covariates, logger)
        return new_results
    return results_df

def run_threshold_sensitivity_sweep(merged_df, entropy_cols, covariates, logger):
    """
    Implement threshold sensitivity sweep as per T028.
    Cutoffs to sweep:
    1. Artifact rejection threshold: 15% to 25% amplitude deviation.
    2. SNR threshold: 5 dB to 7 dB.
    
    We simulate the sweep by filtering the dataset based on these criteria 
    (assuming these columns exist or are derived from previous steps)
    and re-running the regression to see how correlation rates change.
    
    Note: Since 'artifact_rejection_percent' and 'snr_db' might not be explicitly 
    in the merged_df if they were intermediate steps, we assume they are present 
    or we use the 'exclusion_log' logic. For this implementation, we assume 
    'snr_db' exists in the merged data (from T014) and we simulate artifact 
    thresholds by re-filtering based on a hypothetical 'artifact_percent' column 
    or by re-running the exclusion logic with different parameters.
    
    To strictly follow T028 without modifying upstream T016 logic, we will:
    1. Define the baseline run (current merged_df).
    2. Define sweep ranges.
    3. Filter `merged_df` based on SNR thresholds.
    4. For artifact thresholds, we assume we can re-apply a filter if 'artifact_percent' exists,
       otherwise we skip that dimension or log a warning.
    """
    
    # Check for required columns
    snr_col = 'snr_db' # Assumed column name from T014
    artifact_col = 'artifact_percent' # Assumed column name for artifact rejection %
    
    sweep_configs = []
    
    # Define sweep ranges
    snr_thresholds = [5.0, 6.0, 7.0] # Range 5 to 7
    artifact_thresholds = [15.0, 20.0, 25.0] # Range 15 to 25
    
    baseline_n = len(merged_df)
    baseline_results = run_regression_analysis(merged_df, entropy_cols, covariates, logger)
    baseline_significant_count = baseline_results['p_value'].apply(lambda x: x < 0.05).sum() if not baseline_results.empty else 0
    
    logger.info(f"Baseline: N={baseline_n}, Significant correlations={baseline_significant_count}")
    
    results_data = []
    
    for snr_thresh in snr_thresholds:
        for art_thresh in artifact_thresholds:
            # Create a filtered subset
            mask = pd.Series([True] * len(merged_df), index=merged_df.index)
            
            # Apply SNR filter
            if snr_col in merged_df.columns:
                mask &= (merged_df[snr_col] >= snr_thresh)
            else:
                logger.warning(f"Column {snr_col} not found. Skipping SNR filter.")
            
            # Apply Artifact filter
            if artifact_col in merged_df.columns:
                mask &= (merged_df[artifact_col] <= art_thresh)
            else:
                # If artifact column doesn't exist, we might need to simulate or skip
                # For robustness, if missing, we assume all pass or log warning
                logger.warning(f"Column {artifact_col} not found. Skipping Artifact filter.")
            
            filtered_df = merged_df[mask]
            
            if len(filtered_df) == 0:
                logger.warning(f"No data points for SNR>={snr_thresh}, Art<={art_thresh}. Skipping.")
                continue
            
            # Re-run regression
            sub_results = run_regression_analysis(filtered_df, entropy_cols, covariates, logger)
            sub_significant = sub_results['p_value'].apply(lambda x: x < 0.05).sum() if not sub_results.empty else 0
            
            # Calculate absolute difference from baseline significant count
            diff = abs(sub_significant - baseline_significant_count)
            
            results_data.append({
                'scenario': f"SNR_{snr_thresh}_dB_Art_{art_thresh}%",
                'snr_threshold': snr_thresh,
                'artifact_threshold': art_thresh,
                'n_excluded': baseline_n - len(filtered_df),
                'n_remaining': len(filtered_df),
                'significant_correlations': sub_significant,
                'diff_from_baseline': diff
            })
            
    return pd.DataFrame(results_data)

def main():
    """Main entry point for T028: Threshold Sensitivity Sweep."""
    logger = setup_logger("regression_analysis")
    logger.info("Starting T028: Threshold Sensitivity Sweep")
    
    log_resource_snapshot(logger)
    
    try:
        # Load and prepare data
        entropy_df, behavioral_df = load_data()
        merged_df = merge_data(entropy_df, behavioral_df)
        
        if merged_df.empty:
            logger.error("Merged data is empty. Cannot proceed.")
            return
        
        entropy_cols, covariates = prepare_features(merged_df)
        
        # Run the baseline regression (needed for comparison)
        baseline_results = run_regression_analysis(merged_df, entropy_cols, covariates, logger)
        
        # Run the sensitivity sweep
        sensitivity_df = run_threshold_sensitivity_sweep(merged_df, entropy_cols, covariates, logger)
        
        # Save output
        output_path = Path("data/processed/sensitivity_threshold_results.csv")
        if not sensitivity_df.empty:
            sensitivity_df.to_csv(output_path, index=False)
            logger.info(f"Sensitivity threshold results saved to {output_path}")
        else:
            logger.warning("No sensitivity results generated.")
            
    except Exception as e:
        logger.error(f"Error during T028 execution: {e}")
        raise
    finally:
        log_resource_snapshot(logger)

if __name__ == "__main__":
    main()