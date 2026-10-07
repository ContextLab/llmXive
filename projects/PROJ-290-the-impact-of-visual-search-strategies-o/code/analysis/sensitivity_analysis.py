import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import mixedlm

from config import get_config
from utils.logging import get_logger

def get_logger_wrapper(func):
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        return func(*args, logger=logger, **kwargs)
    return wrapper

def load_cluster_labels(k: int, logger: logging.Logger) -> pd.DataFrame:
    """
    Load cluster labels for a specific k from data/processed/labels_k{k}.csv.
    """
    config = get_config()
    path = config.PROCESSED_DATA_DIR / f"labels_k{k}.csv"
    if not path.exists():
        raise FileNotFoundError(f"Cluster labels file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded cluster labels for k={k}: {len(df)} rows from {path}")
    return df

def load_processed_features(logger: logging.Logger) -> pd.DataFrame:
    """
    Load the main processed features dataset.
    """
    config = get_config()
    path = config.PROCESSED_DATA_DIR / "features.csv"
    if not path.exists():
        raise FileNotFoundError(f"Processed features file not found: {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded processed features: {len(df)} rows from {path}")
    return df

def fit_descriptive_lmm(df: pd.DataFrame, cluster_col: str, logger: logging.Logger) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit a Linear Mixed-Effects Model with detection_time as outcome and 
    the cluster label as a fixed effect.
    
    Returns the fitted model and a dictionary of results (coefficients, p-values, etc.).
    """
    if cluster_col not in df.columns or 'detection_time' not in df.columns:
        raise ValueError(f"Required columns not found. Have: {df.columns.tolist()}")
    
    # Drop rows with missing values in relevant columns
    clean_df = df[[cluster_col, 'detection_time']].dropna()
    
    if len(clean_df) == 0:
        raise ValueError("No valid data remaining after dropping NaNs.")
    
    # Ensure cluster_col is treated as categorical
    clean_df[cluster_col] = pd.Categorical(clean_df[cluster_col])
    
    formula = f"detection_time ~ C({cluster_col})"
    
    try:
        # Fit LMM. Assuming 'participant_id' is the random effect grouping variable.
        # If the column name differs, this might need adjustment based on data schema.
        # Standard practice: random intercept per participant.
        if 'participant_id' in clean_df.columns:
            model = mixedlm(formula, clean_df, groups=clean_df["participant_id"])
        else:
            # Fallback if participant_id is missing, though unlikely in this context
            logger.warning("participant_id column not found. Using index as groups (invalid for mixed effects, but proceeding).")
            model = mixedlm(formula, clean_df, groups=range(len(clean_df)))
        
        result = model.fit(maxiter=500)
        
        if not result.converged:
            logger.warning(f"LMM for k={cluster_col} did not converge. Results may be unreliable.")
        
        # Extract summary data
        summary_dict = {
            "formula": formula,
            "converged": result.converged,
            "n_obs": len(clean_df),
            "n_groups": len(clean_df["participant_id"].unique()) if 'participant_id' in clean_df.columns else 0,
            "coefficients": {},
            "p_values": {},
            "std_err": {}
        }
        
        # Parse results table
        # result.summary2().tables[1] contains coefficient info
        summary_str = result.summary().as_text()
        # Easier to access via result.params, result.bse, result.pvalues
        
        for name, param in result.params.items():
            summary_dict["coefficients"][name] = float(param)
            summary_dict["std_err"][name] = float(result.bse[name])
            summary_dict["p_values"][name] = float(result.pvalues[name])
        
        return result, summary_dict

    except Exception as e:
        logger.error(f"Failed to fit LMM for k={cluster_col}: {e}")
        raise

@get_logger_wrapper
def run_sensitivity_analysis(k_values: List[int] = [2, 3], logger: logging.Logger = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis by fitting descriptive LMMs for different k values
    (cluster counts) and reporting coefficient variance.
    
    This validates the stability of the exploratory cluster-based approach.
    """
    config = get_config()
    results = {
        "description": "Sensitivity Analysis: Stability of cluster-based LMM",
        "k_values_tested": k_values,
        "models": {}
    }
    
    # Load base features once
    try:
        features_df = load_processed_features(logger)
    except FileNotFoundError as e:
        logger.error(f"Cannot run sensitivity analysis: {e}")
        return results

    for k in k_values:
        logger.info(f"Processing sensitivity analysis for k={k}")
        try:
            # Load labels for this k
            labels_df = load_cluster_labels(k, logger)
            
            # Merge with features to get detection_time
            # Assuming 'participant_id' and 'trial_id' (or similar) exist to merge
            # We need to join on the unique identifier present in both
            common_cols = set(labels_df.columns) & set(features_df.columns)
            if 'participant_id' not in common_cols:
                logger.warning("participant_id not found in both datasets. Attempting merge on all common cols.")
                merge_keys = list(common_cols)
            else:
                merge_keys = ['participant_id']
            
            # Ensure we have the necessary columns for merge
            if not merge_keys:
                logger.error("No common columns found to merge labels and features.")
                continue
            
            merged_df = pd.merge(labels_df, features_df, on=merge_keys, how='inner')
            
            # The cluster column name might vary, assume it's named 'cluster_label' or 'k{k}_cluster'
            # Based on T024b output, let's assume the column is named 'cluster_label' or similar.
            # If T024b saves a specific column, we need to know it. 
            # Let's assume the column is named 'cluster_label' for k=2 and k=3 respectively 
            # or the file contains a column 'cluster_label'.
            # If the file has multiple, we pick the one corresponding to this k.
            # Let's assume the column is simply 'cluster_label' in the saved file.
            cluster_col_name = 'cluster_label'
            if cluster_col_name not in merged_df.columns:
                # Try to find a column that looks like the k label
                candidates = [c for c in merged_df.columns if str(k) in c.lower() and 'cluster' in c.lower()]
                if candidates:
                    cluster_col_name = candidates[0]
                else:
                    logger.error(f"Could not find cluster label column for k={k} in merged data.")
                    continue

            logger.info(f"Fitting LMM for k={k} using cluster column: {cluster_col_name}")
            model, stats = fit_descriptive_lmm(merged_df, cluster_col_name, logger)
            
            results["models"][f"k_{k}"] = {
                "status": "success",
                "stats": stats,
                "model_summary": str(model.summary())
            }
            
        except FileNotFoundError as e:
            logger.warning(f"Skipping k={k} because labels file not found: {e}")
            results["models"][f"k_{k}"] = {"status": "skipped", "reason": "Labels file not found"}
        except Exception as e:
            logger.error(f"Error processing k={k}: {e}")
            results["models"][f"k_{k}"] = {"status": "failed", "reason": str(e)}
    
    # Calculate coefficient variance across models if multiple succeeded
    successful_models = [m for m in results["models"].values() if m["status"] == "success"]
    if len(successful_models) > 1:
        # Extract coefficients for the main effect (e.g., C(cluster_label)[T.1.0])
        # This is a simplified check; in reality, we'd compare specific contrasts.
        all_coeffs = []
        for m in successful_models:
            coeffs = m["stats"]["coefficients"]
            # Filter for the cluster effect (exclude intercept)
            cluster_coeffs = {k: v for k, v in coeffs.items() if k != 'Intercept'}
            if cluster_coeffs:
                all_coeffs.append(list(cluster_coeffs.values()))
        
        if all_coeffs:
            # Flatten and calculate variance
            flat_coeffs = [c for sublist in all_coeffs for c in sublist]
            if len(flat_coeffs) > 1:
                results["coefficient_variance"] = float(np.var(flat_coeffs))
                results["coefficient_mean"] = float(np.mean(flat_coeffs))
            else:
                results["coefficient_variance"] = None
        else:
            results["coefficient_variance"] = None
    else:
        results["coefficient_variance"] = None

    return results

@get_logger_wrapper
def save_sensitivity_report(report: Dict[str, Any], logger: logging.Logger = None) -> str:
    """
    Save the sensitivity analysis report to results/sensitivity_report.yaml.
    """
    config = get_config()
    output_path = config.RESULTS_DIR / "sensitivity_report.yaml"
    
    import yaml
    with open(output_path, 'w') as f:
        yaml.dump(report, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Sensitivity report saved to {output_path}")
    return str(output_path)

@get_logger_wrapper
def main(logger: logging.Logger = None) -> None:
    """
    Entry point for the sensitivity analysis script.
    """
    logger.info("Starting Sensitivity Analysis (T025)")
    
    try:
        report = run_sensitivity_analysis(k_values=[2, 3], logger=logger)
        save_sensitivity_report(report, logger=logger)
        logger.info("Sensitivity Analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
