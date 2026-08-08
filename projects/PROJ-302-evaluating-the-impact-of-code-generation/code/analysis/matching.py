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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for matching
SMD_THRESHOLD = 0.1
MAX_RETRIES = 3
MATCHING_RATIO = 1  # 1:1 matching by default

def calculate_smd(group_a: pd.Series, group_b: pd.Series) -> float:
    """
    Calculate the Standardized Mean Difference (SMD) between two groups.
    SMD = (mean_a - mean_b) / sqrt((var_a + var_b) / 2)
    """
    mean_a = group_a.mean()
    mean_b = group_b.mean()
    var_a = group_a.var()
    var_b = group_b.mean()
    
    # Handle zero variance case
    pooled_std = np.sqrt((var_a + var_b) / 2)
    if pooled_std == 0:
        return 0.0
    
    return (mean_a - mean_b) / pooled_std

def estimate_propensity_scores(df: pd.DataFrame, covariates: List[str], 
                               treatment_col: str = 'is_llm_like') -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    Returns the dataframe with an added 'propensity_score' column.
    """
    X = df[covariates].values
    y = df[treatment_col].values
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)
    
    propensity_scores = model.predict_proba(X_scaled)[:, 1]
    df = df.copy()
    df['propensity_score'] = propensity_scores
    
    return df

def perform_matching(df: pd.DataFrame, propensity_col: str = 'propensity_score',
                     treatment_col: str = 'is_llm_like', ratio: int = 1) -> pd.DataFrame:
    """
    Perform 1:1 nearest neighbor matching based on propensity scores.
    Returns a dataframe containing only the matched pairs.
    """
    df = df.copy()
    treated = df[df[treatment_col] == 1].copy()
    control = df[df[treatment_col] == 0].copy()
    
    matched_indices = []
    control_indices = control.index.tolist()
    
    # Sort treated by propensity score
    treated = treated.sort_values(by=propensity_col)
    
    for _, t_row in treated.iterrows():
        t_score = t_row[propensity_col]
        
        # Find closest control
        if not control_indices:
            break
            
        control_scores = control.loc[control_indices, propensity_col]
        distances = np.abs(control_scores - t_score)
        closest_idx = distances.idxmin()
        
        matched_indices.append(t_row.name)
        matched_indices.append(closest_idx)
        
        # Remove used control
        control_indices.remove(closest_idx)
    
    if not matched_indices:
        logger.warning("No matches found.")
        return pd.DataFrame()
        
    return df.loc[matched_indices]

def check_balance(df_matched: pd.DataFrame, covariates: List[str], 
                  treatment_col: str = 'is_llm_like') -> Dict[str, float]:
    """
    Check balance of covariates after matching by calculating SMD for each.
    Returns a dictionary of covariate -> SMD value.
    """
    if df_matched.empty:
        return {}
        
    smd_results = {}
    for col in covariates:
        if col in df_matched.columns:
            treated_vals = df_matched[df_matched[treatment_col] == 1][col]
            control_vals = df_matched[df_matched[treatment_col] == 0][col]
            smd = calculate_smd(treated_vals, control_vals)
            smd_results[col] = smd
            
    return smd_results

def run_propensity_matching(input_path: str, output_path: str, 
                            covariates: List[str], 
                            treatment_col: str = 'is_llm_like') -> Tuple[bool, Dict[str, Any]]:
    """
    Main function to run propensity score matching with retry logic.
    Returns (success, report_dict).
    If success is False, report_dict contains failure details.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Ensure required columns exist
    required_cols = covariates + [treatment_col]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    best_smds = {}
    max_smd = float('inf')
    retry_count = 0
    success = False
    
    # Initial covariates
    current_covariates = covariates.copy()
    
    while retry_count <= MAX_RETRIES:
        logger.info(f"Attempt {retry_count + 1}/{MAX_RETRIES + 1} with covariates: {current_covariates}")
        
        # Estimate propensity scores
        df_with_scores = estimate_propensity_scores(df, current_covariates, treatment_col)
        
        # Perform matching
        df_matched = perform_matching(df_with_scores, treatment_col=treatment_col)
        
        if df_matched.empty:
            logger.warning("Matching resulted in empty dataset.")
            retry_count += 1
            continue
        
        # Check balance
        smds = check_balance(df_matched, current_covariates, treatment_col)
        current_max_smd = max(smds.values()) if smds else 0
        
        logger.info(f"SMDs: {smds}, Max SMD: {current_max_smd}")
        
        if current_max_smd <= SMD_THRESHOLD:
            success = True
            best_smds = smds
            max_smd = current_max_smd
            logger.info("Balance achieved.")
            break
        
        # If not balanced and we can retry, add interaction terms
        if retry_count < MAX_RETRIES:
            # Add interaction terms (e.g., product of first two covariates)
            if len(current_covariates) >= 2:
                interaction_name = f"{current_covariates[0]}_x_{current_covariates[1]}"
                if interaction_name not in df.columns:
                    df[interaction_name] = df[current_covariates[0]] * df[current_covariates[1]]
                current_covariates.append(interaction_name)
            retry_count += 1
        else:
            break
    
    report = {
        "success": success,
        "final_covariates": current_covariates,
        "retry_count": retry_count,
        "max_smd": max_smd,
        "smd_values": best_smds,
        "matched_count": len(df_matched) if not df_matched.empty else 0
    }
    
    if success:
        logger.info(f"Saving matched data to {output_path}")
        df_matched.to_parquet(output_path, index=False)
    else:
        logger.warning("Matching failed to achieve balance after retries.")
        # Generate failure report
        failure_report_path = str(Path(output_path).parent / "matching_failure_report.json")
        with open(failure_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Failure report saved to {failure_report_path}")
        
    return success, report

def main():
    """Entry point for running matching analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run propensity score matching")
    parser.add_argument("--input", type=str, required=True, help="Input parquet file path")
    parser.add_argument("--output", type=str, required=True, help="Output parquet file path")
    parser.add_argument("--covariates", type=str, nargs='+', 
                        default=['file_size', 'complexity_score', 'activity_score'],
                        help="Covariates to use for matching")
    parser.add_argument("--treatment-col", type=str, default='is_llm_like',
                        help="Name of the treatment column")
    
    args = parser.parse_args()
    
    success, report = run_propensity_matching(
        args.input, 
        args.output, 
        args.covariates, 
        args.treatment_col
    )
    
    if not success:
        print(f"Matching failed. See {Path(args.output).parent / 'matching_failure_report.json'} for details.")
        sys.exit(1)
    
    print(f"Matching successful. Max SMD: {report['max_smd']:.4f}")
    sys.exit(0)

if __name__ == "__main__":
    main()