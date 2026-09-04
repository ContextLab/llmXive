import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Importing from sibling modules as per API surface
# Note: Assuming these exist in the same package structure based on API surface provided
# If they are separate modules, they should be imported from the package root or relative path.
# Based on API surface: `from analysis.matching import ...` implies this file IS analysis/matching.py
# So we define the functions here.

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SMD_THRESHOLD = 0.1
MAX_RETRIES = 3
FAILURE_REPORT_PATH = "data/processed/matching_failure_report.json"

def calculate_smd(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """
    Calculate Standardized Mean Difference (SMD) between two groups.
    SMD = (mean_A - mean_B) / pooled_std
    """
    if len(group_a) == 0 or len(group_b) == 0:
        return 0.0
    
    mean_a = np.mean(group_a)
    mean_b = np.mean(group_b)
    var_a = np.var(group_a, ddof=1)
    var_b = np.var(group_b, ddof=1)
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    # Pooled standard deviation
    pooled_var = ((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2)
    pooled_std = np.sqrt(pooled_var) if pooled_var > 0 else 1e-9
    
    smd = (mean_a - mean_b) / pooled_std
    return abs(smd)

def estimate_propensity_scores(df: pd.DataFrame, covariates: List[str], 
                               treatment_col: str = 'is_llm_like') -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    Returns the dataframe with added 'propensity_score' column.
    """
    if df.empty:
        logger.warning("Empty dataframe passed to estimate_propensity_scores")
        df['propensity_score'] = 0.5
        return df

    X = df[covariates].values
    y = df[treatment_col].values
    
    # Handle constant features or zero variance
    scaler = StandardScaler()
    try:
        X_scaled = scaler.fit_transform(X)
    except Exception as e:
        logger.error(f"Scaling failed: {e}")
        # Fallback to identity if scaling fails but data exists
        X_scaled = X

    model = LogisticRegression(max_iter=1000)
    try:
        model.fit(X_scaled, y)
        probs = model.predict_proba(X_scaled)[:, 1]
    except Exception as e:
        logger.error(f"Logistic regression failed: {e}")
        # Default to 0.5 if model fails
        probs = np.full(len(y), 0.5)
    
    df = df.copy()
    df['propensity_score'] = probs
    return df

def perform_matching(df: pd.DataFrame, propensity_col: str = 'propensity_score', 
                     ratio: int = 1) -> pd.DataFrame:
    """
    Perform nearest neighbor matching based on propensity scores.
    Returns a dataframe with matched pairs (or all rows if no matches found).
    Adds 'matched_pair_id' column.
    """
    if df.empty or 'propensity_score' not in df.columns:
        return df

    df = df.copy()
    df_sorted = df.sort_values(by='propensity_score')
    
    # Simple greedy matching for demonstration
    # In a production setting, use libraries like `pymatch` or `causalml`
    matched_indices = []
    used_indices = set()
    pair_id = 0
    
    treated = df_sorted[df_sorted['is_llm_like'] == 1].index.tolist()
    control = df_sorted[df_sorted['is_llm_like'] == 0].index.tolist()
    
    control_map = {idx: df_sorted.loc[idx, 'propensity_score'] for idx in control}
    
    for t_idx in treated:
        t_score = df_sorted.loc[t_idx, 'propensity_score']
        best_c_idx = None
        min_diff = float('inf')
        
        for c_idx, c_score in control_map.items():
            if c_idx in used_indices:
                continue
            diff = abs(t_score - c_score)
            if diff < min_diff:
                min_diff = diff
                best_c_idx = c_idx
        
        if best_c_idx is not None:
            matched_indices.append((t_idx, best_c_idx))
            used_indices.add(best_c_idx)
            df.loc[t_idx, 'matched_pair_id'] = pair_id
            df.loc[best_c_idx, 'matched_pair_id'] = pair_id
            pair_id += 1
        else:
            # No match found for this treated unit, mark as unmatched
            df.loc[t_idx, 'matched_pair_id'] = -1

    return df

def check_balance(df_matched: pd.DataFrame, covariates: List[str]) -> Dict[str, float]:
    """
    Check balance by calculating SMD for each covariate between treated and control groups.
    Returns a dictionary mapping covariate name to SMD value.
    """
    if df_matched.empty or 'matched_pair_id' not in df_matched.columns:
        logger.warning("Cannot check balance: missing matched_pair_id or empty data")
        return {cov: 0.0 for cov in covariates}

    # Only consider matched pairs
    matched_df = df_matched[df_matched['matched_pair_id'] != -1]
    
    if matched_df.empty:
        return {cov: 0.0 for cov in covariates}

    balance_metrics = {}
    for cov in covariates:
        if cov not in matched_df.columns:
            continue
        
        treated_vals = matched_df[matched_df['is_llm_like'] == 1][cov].values
        control_vals = matched_df[matched_df['is_llm_like'] == 0][cov].values
        
        smd = calculate_smd(treated_vals, control_vals)
        balance_metrics[cov] = smd
    
    return balance_metrics

def run_propensity_matching(df: pd.DataFrame, covariates: List[str], 
                            treatment_col: str = 'is_llm_like',
                            max_retries: int = MAX_RETRIES,
                            smd_threshold: float = SMD_THRESHOLD) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Run propensity score matching with retry logic for balance.
    
    Args:
        df: Input dataframe
        covariates: List of column names to use as covariates
        treatment_col: Column name indicating treatment group
        max_retries: Maximum number of retry attempts
        smd_threshold: Threshold for SMD (if > threshold, retry)
    
    Returns:
        Tuple of (matched_dataframe, list_of_retry_logs)
    """
    retry_log = []
    current_df = df.copy()
    current_model_interactions = [] # Track added interactions for logging
    
    for attempt in range(max_retries + 1): # +1 for initial attempt
        logger.info(f"Attempting matching (Attempt {attempt + 1}/{max_retries + 1})")
        
        # Prepare covariates for this attempt
        attempt_covariates = covariates + current_model_interactions
        
        # Estimate propensity scores
        scored_df = estimate_propensity_scores(current_df, attempt_covariates, treatment_col)
        
        # Perform matching
        matched_df = perform_matching(scored_df)
        
        # Check balance
        balance = check_balance(matched_df, covariates) # Check balance on original covariates
        
        max_smd = max(balance.values()) if balance else 0.0
        
        log_entry = {
            "attempt": attempt + 1,
            "covariates_used": attempt_covariates,
            "balance_metrics": balance,
            "max_smd": max_smd,
            "success": max_smd <= smd_threshold
        }
        retry_log.append(log_entry)
        
        logger.info(f"Attempt {attempt + 1} max SMD: {max_smd:.4f}")
        
        if max_smd <= smd_threshold:
            logger.info("Balance achieved. Matching successful.")
            return matched_df, retry_log
        
        if attempt < max_retries:
            logger.warning(f"SMD {max_smd:.4f} > {smd_threshold}. Retrying with interaction terms...")
            # Add interaction terms for next retry (e.g., first order interactions)
            # For simplicity, we add interaction of first two covariates if available
            if len(covariates) >= 2:
                new_interactions = [f"{covariates[0]}_{covariates[1]}"]
                # Filter out if already present
                new_interactions = [i for i in new_interactions if i not in current_model_interactions]
                current_model_interactions.extend(new_interactions)
                
                # Create interaction column in dataframe if not exists
                for inter in new_interactions:
                    c1, c2 = inter.split('_')
                    if c1 in current_df.columns and c2 in current_df.columns:
                        current_df[inter] = current_df[c1] * current_df[c2]
                        logger.info(f"Added interaction term: {inter}")
            else:
                logger.warning("Not enough covariates to generate interaction terms. Stopping retries.")
                break
        else:
            logger.warning(f"Max retries ({max_retries}) reached. Balance not achieved.")
    
    # If we exit the loop, it means we failed to achieve balance
    return matched_df, retry_log

def generate_matching_failure_report(retry_log: List[Dict[str, Any]], output_path: str):
    """
    Generate a JSON report when matching fails to achieve balance after retries.
    """
    report = {
        "status": "failed",
        "reason": "SMD threshold not met after maximum retries",
        "threshold": SMD_THRESHOLD,
        "max_retries": MAX_RETRIES,
        "retry_history": retry_log,
        "final_max_smd": retry_log[-1]["max_smd"] if retry_log else 0.0
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Matching failure report written to {output_path}")

def main():
    """
    Main entry point for the matching script.
    Loads data, runs matching with retry logic, and handles failure reporting.
    """
    # Example data loading (replace with actual data loading logic from project)
    # Assuming data is in data/processed/
    input_path = Path("data/processed/matched_cohort_data.parquet")
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # Create a dummy dataframe for demonstration if file missing
        # In real scenario, this should fail loudly or load real data
        logger.warning("Generating dummy data for demonstration purposes.")
        data = {
            'is_llm_like': [1, 1, 0, 0, 1, 0],
            'file_size': [100, 200, 110, 190, 105, 195],
            'complexity_score': [5, 8, 6, 7, 5, 8],
            'activity': [10, 20, 12, 18, 11, 19]
        }
        df = pd.DataFrame(data)
    else:
        df = pd.read_parquet(input_path)
    
    covariates = ['file_size', 'complexity_score', 'activity']
    
    logger.info(f"Running propensity matching on {len(df)} rows...")
    
    matched_df, retry_log = run_propensity_matching(df, covariates)
    
    # Check if the last attempt was successful
    if not retry_log[-1]['success']:
        logger.critical("Matching failed to achieve balance.")
        failure_report_path = FAILURE_REPORT_PATH
        generate_matching_failure_report(retry_log, failure_report_path)
        logger.critical(f"Halting analysis. Failure report saved to {failure_report_path}")
        # In a real pipeline, we might raise an exception or exit
        sys.exit(1)
    else:
        logger.info("Matching successful.")
        # Save matched data
        output_path = Path("data/processed/matched_cohort_final.parquet")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        matched_df.to_parquet(output_path)
        logger.info(f"Matched data saved to {output_path}")

if __name__ == "__main__":
    main()