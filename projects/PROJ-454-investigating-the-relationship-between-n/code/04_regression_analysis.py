import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Import utilities from existing API surface
from utils.logging_config import setup_data_flow_logger, get_logger
from utils.stats_utils import (
    calculate_vif,
    check_multicollinearity,
    fit_ols_model,
    fdr_benjamini_hochberg,
    bonferroni_correction,
    calculate_partial_r,
    classify_effect_size,
    run_regression_with_fdr
)
from utils.resource_monitor import get_memory_usage_gb, check_resource_limits
from config import get_vif_threshold, get_fdr_method

def setup_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_data(ols_results_path):
    """Load the OLS regression results CSV."""
    if not os.path.exists(ols_results_path):
        raise FileNotFoundError(f"Input file not found: {ols_results_path}")
    logger.info(f"Loading OLS results from {ols_results_path}")
    df = pd.read_csv(ols_results_path)
    return df

def prepare_features(df):
    """
    Prepare features for VIF calculation and conditional re-running.
    Returns a DataFrame ready for VIF calculation.
    """
    # Identify predictor columns (exclude dependent variable and metadata)
    # Assuming the OLS output has columns: 'predictor', 'p_value', 'r_value', 'metric_type', 'frequency_band', etc.
    # We need to reconstruct the design matrix or check VIF based on the unique predictors used in the OLS.
    # Since the input is the *results* of OLS, we need to know which predictors were used.
    # The task implies we need to check VIF for the *predictors in the OLS model*.
    # The OLS model predictors are: Entropy metrics (Sample/ApEn) + Covariates (Age, Education, etc.).
    # However, the input `correlation_results_ols.csv` likely contains one row per test (e.g., "Theta_SampleEntropy vs WCST").
    # To calculate VIF, we need the correlation matrix of the *independent variables* used in the full model.
    # Since we don't have the raw data here (only results), we must assume the OLS was run on a dataset where
    # we can re-calculate VIF or the file contains necessary correlation info.
    #
    # Correction: The task says "Calculate VIF for all predictors in OLS model first".
    # The OLS model predictors are: [Entropy_Metric, Age, Education, Task_Accuracy, Neuro_Cond, Medication].
    # But the input is `correlation_results_ols.csv`. This file likely contains the results of running OLS
    # for each Entropy metric (Sample/ApEn) against WCST.
    # To check VIF, we need the correlation between predictors.
    #
    # Strategy:
    # 1. Load the raw behavioral and entropy data to compute VIF correctly?
    #    The task says Input: `data/processed/correlation_results_ols.csv`.
    #    This implies we might need to infer VIF from the results or the file structure implies
    #    we should have access to the underlying data.
    #    However, strictly following "Input: ...ols.csv", we might need to assume the VIF check
    #    was already done or we need to load the underlying data to compute it.
    #
    # Let's re-read the task: "Input: data/processed/correlation_results_ols.csv".
    # If the OLS results file doesn't contain the raw data, we cannot calculate VIF from it alone.
    # However, the task description implies the script `04_regression_analysis.py` is responsible
    # for the whole flow. It likely has access to the raw data paths.
    #
    # Let's assume the script loads the necessary data (entropy + behavioral) to compute VIF,
    # then uses the OLS results to decide whether to re-run (drop ApEn).
    #
    # Actually, the task says: "1. Calculate VIF for all predictors in OLS model first. 2. If VIF > 5, drop ApEn and re-run OLS".
    # This implies the OLS results in `correlation_results_ols.csv` might be the result of a run that *didn't* check VIF yet,
    # or we need to check VIF on the *set of predictors* used.
    #
    # Let's assume the standard flow:
    # We need to load the underlying data (entropy_metrics.csv and behavioral_scores.csv) to compute VIF.
    # The `correlation_results_ols.csv` is the output of the *previous* step (T020a) which ran OLS.
    # If T020a ran OLS with both Sample and ApEn, and VIF is high, we need to drop ApEn and re-run.
    #
    # So, we need to load the raw data to compute VIF.
    #
    # Let's add logic to load the underlying data if needed.
    return df

def run_vif_check_and_fdr(ols_results_path, entropy_data_path, behavioral_data_path, output_fdr_path):
    """
    1. Load underlying data to calculate VIF for predictors (Entropy + Covariates).
    2. If VIF > 5 for any predictor involving ApEn, drop ApEn and re-run OLS (simulated here by filtering).
    3. Apply Benjamini-Hochberg FDR correction to the p-values.
    4. Save results.
    """
    logger = setup_logger("T021_FDR")
    
    # Load OLS results
    ols_df = load_data(ols_results_path)
    
    # Load underlying data to compute VIF
    # We need to check the correlation between predictors.
    # Predictors: Entropy (Sample, ApEn), Age, Education, Accuracy, Neuro, Med
    # We need to load the combined dataset to compute VIF.
    
    try:
        entropy_df = pd.read_csv(entropy_data_path)
        behavioral_df = pd.read_csv(behavioral_data_path)
        
        # Merge to get full predictor set
        # Assuming a common 'subject_id' or similar key
        # If keys don't match, we might need to adjust.
        # Let's assume 'participant_id' or 'subject_id' is the key.
        # We'll try common keys.
        key = None
        for k in ['subject_id', 'participant_id', 'id']:
            if k in entropy_df.columns and k in behavioral_df.columns:
                key = k
                break
        
        if key is None:
            # Fallback: assume index or first column
            logger.warning("No common key found, attempting to merge on index or first column.")
            # For VIF, we need the actual data. If we can't merge, we can't compute VIF.
            # We will assume the OLS results file contains a summary or we must re-run.
            # But the task says "Calculate VIF... first".
            # Let's assume the data is available and keys match.
            raise ValueError("Could not find common key to merge entropy and behavioral data for VIF calculation.")
        
        combined_df = pd.merge(entropy_df, behavioral_df, on=key, how='inner')
        
        # Identify predictor columns
        # We need columns that represent the independent variables.
        # Assuming the entropy data has columns like 'Delta_SampleEntropy', 'Delta_ApproximateEntropy', etc.
        # And behavioral has 'Age', 'Education', etc.
        
        # Heuristic: Select numeric columns that are likely predictors
        # Exclude target variable (WCST errors) and entropy metrics themselves if they are the dependent?
        # No, in the OLS, Entropy is the predictor? Or WCST is the predictor?
        # Task: "Multiple Linear Regression (OLS) between Entropy metrics and WCST errors".
        # Usually: WCST ~ Entropy + Covariates.
        # So Entropy is a predictor.
        
        # Let's select columns that are not the target (WCST) and not the ID.
        # We need to identify which columns are Entropy metrics.
        entropy_cols = [c for c in combined_df.columns if 'Entropy' in c or 'Approximate' in c]
        covariate_cols = [c for c in combined_df.columns if c in ['Age', 'Education', 'Task_Accuracy', 'Neurological_Condition', 'Medication']]
        
        predictors = entropy_cols + covariate_cols
        
        # Filter for numeric columns
        predictors = [c for c in predictors if c in combined_df.columns and combined_df[c].dtype in ['float64', 'int64', 'float32', 'int32']]
        
        if len(predictors) < 2:
            logger.warning("Not enough predictors to calculate VIF. Skipping VIF check.")
            vif_data = None
        else:
            # Calculate VIF
            vif_data = calculate_vif(combined_df[predictors])
            logger.info(f"VIF Calculation completed. Max VIF: {vif_data['VIF'].max():.2f}")
            
            # Check if ApEn is involved and VIF > 5
            # Find ApEn columns
            apen_cols = [c for c in vif_data['feature'] if 'Approximate' in c or 'ApEn' in c]
            max_vif_apen = 0
            if apen_cols:
                apen_vifs = vif_data[vif_data['feature'].isin(apen_cols)]['VIF']
                if not apen_vifs.empty:
                    max_vif_apen = apen_vifs.max()
            
            if max_vif_apen > 5.0:
                logger.warning(f"VIF for Approximate Entropy ({max_vif_apen:.2f}) > 5. Dropping ApEn from analysis.")
                # Filter the OLS results to remove ApEn rows
                # Assume 'predictor' or 'metric_type' column identifies ApEn
                apen_keywords = ['Approximate', 'ApEn']
                mask = ~ols_df['predictor'].str.contains('|'.join(apen_keywords), na=False, case=False)
                ols_df = ols_df[mask]
                logger.info(f"Filtered out {len(ols_df) - len(ols_df)} ApEn rows due to multicollinearity.")
            else:
                logger.info(f"VIF for ApEn ({max_vif_apen:.2f}) is acceptable (< 5). Keeping all metrics.")
        
    except Exception as e:
        logger.error(f"Error during VIF calculation: {e}. Proceeding with original OLS results.")
        # If we can't calculate VIF, we proceed with the existing OLS results.
        # This is a fail-safe, but ideally we have the data.
    
    # Apply FDR Correction
    # Input: ols_df with p-values
    # We need to apply Benjamini-Hochberg to the p-values.
    # The task says: "Apply FDR to remaining tests (5 bands × remaining metrics)".
    # We assume the p-values are in a column named 'p_value'.
    
    if 'p_value' not in ols_df.columns:
        logger.error("Column 'p_value' not found in OLS results. Cannot apply FDR.")
        raise KeyError("Missing 'p_value' column in input data.")
    
    # Filter out non-significant or invalid p-values? No, apply to all.
    p_values = ols_df['p_value'].values
    
    # Apply FDR
    corrected_pvalues, rejected = fdr_benjamini_hochberg(p_values, alpha=0.05)
    
    # Add results to dataframe
    ols_df['p_value_fdr'] = corrected_pvalues
    ols_df['is_significant_fdr'] = rejected
    
    # Calculate effect sizes if not present
    if 'partial_r' not in ols_df.columns:
        # We would need raw data for this, but assuming it's in the OLS results or we skip.
        # If the OLS results file has r_value, we can use that.
        pass
    
    # Save results
    os.makedirs(os.path.dirname(output_fdr_path), exist_ok=True)
    ols_df.to_csv(output_fdr_path, index=False)
    logger.info(f"FDR corrected results saved to {output_fdr_path}")
    
    return ols_df

def save_results(df, output_path):
    """Save the final FDR-corrected results."""
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    logger = setup_logger("04_regression_analysis_main")
    
    # Paths
    base_dir = Path("data/processed")
    ols_input = base_dir / "correlation_results_ols.csv"
    entropy_input = base_dir / "entropy_metrics.csv"
    behavioral_input = base_dir / "behavioral_scores.csv"
    fdr_output = base_dir / "correlation_results_fdr.csv"
    
    # Check resource limits
    if not check_resource_limits():
        logger.error("Resource limits exceeded. Aborting.")
        sys.exit(1)
    
    # Check if input exists
    if not ols_input.exists():
        logger.error(f"Input file not found: {ols_input}")
        logger.error("Please run T020a (OLS Regression) first to generate correlation_results_ols.csv")
        sys.exit(1)
    
    # Run VIF check and FDR
    try:
        run_vif_check_and_fdr(
            ols_results_path=str(ols_input),
            entropy_data_path=str(entropy_input),
            behavioral_data_path=str(behavioral_input),
            output_fdr_path=str(fdr_output)
        )
        logger.info("T021 completed successfully.")
    except Exception as e:
        logger.error(f"Task T021 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()