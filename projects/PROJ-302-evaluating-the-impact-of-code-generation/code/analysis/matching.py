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
from sklearn.model_selection import cross_val_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for matching configuration
MAX_RETRIES = 3
SMD_THRESHOLD = 0.1
MATCHING_FAILURE_REPORT_PATH = "data/processed/matching_failure_report.json"
COVARIATES = ["file_size", "complexity_score", "activity_score"]

def calculate_smd(treated: pd.Series, control: pd.Series) -> float:
    """
    Calculate Standardized Mean Difference (SMD) between treated and control groups.
    
    SMD = (mean_treated - mean_control) / pooled_std
    
    Args:
        treated: Series of values for the treated group
        control: Series of values for the control group
        
    Returns:
        float: SMD value
    """
    mean_treated = treated.mean()
    mean_control = control.mean()
    
    var_treated = treated.var(ddof=1)
    var_control = control.var(ddof=1)
    n_treated = len(treated)
    n_control = len(control)
    
    # Pooled standard deviation
    pooled_var = ((n_treated - 1) * var_treated + (n_control - 1) * var_control) / (n_treated + n_control - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        return 0.0
        
    smd = (mean_treated - mean_control) / pooled_std
    return abs(smd)  # Return absolute value for balance check

def estimate_propensity_scores(df: pd.DataFrame, covariates: List[str] = None) -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    
    Args:
        df: DataFrame containing covariates and treatment assignment
        covariates: List of covariate column names
        
    Returns:
        DataFrame with added 'propensity_score' column
    """
    if covariates is None:
        covariates = COVARIATES
        
    # Check if all covariates exist
    missing = [c for c in covariates if c not in df.columns]
    if missing:
        raise ValueError(f"Missing covariates: {missing}")
        
    X = df[covariates].values
    y = df['treatment'].values  # 1 for LLM-like, 0 for Human
    
    # Standardize covariates
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Fit logistic regression
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_scaled, y)
    
    # Get propensity scores (probability of being treated)
    propensity_scores = model.predict_proba(X_scaled)[:, 1]
    
    df_with_scores = df.copy()
    df_with_scores['propensity_score'] = propensity_scores
    
    return df_with_scores

def perform_matching(df: pd.DataFrame, ratio: int = 1) -> pd.DataFrame:
    """
    Perform 1:K propensity score matching.
    
    Args:
        df: DataFrame with propensity scores
        ratio: Number of control units to match per treated unit
        
    Returns:
        DataFrame with matched pairs and match IDs
    """
    treated = df[df['treatment'] == 1].copy()
    control = df[df['treatment'] == 0].copy()
    
    matched_indices = []
    match_id_counter = 0
    
    for _, t_row in treated.iterrows():
        # Calculate distance to all controls
        distances = np.abs(control['propensity_score'] - t_row['propensity_score'])
        
        # Get closest controls
        closest_indices = distances.nsmallest(ratio).index.tolist()
        
        for idx in closest_indices:
            matched_indices.append({
                'treated_id': t_row['snippet_id'],
                'control_id': control.loc[idx, 'snippet_id'],
                'match_id': match_id_counter,
                'treated_score': t_row['propensity_score'],
                'control_score': control.loc[idx, 'propensity_score']
            })
            match_id_counter += 1
    
    if not matched_indices:
        logger.warning("No matches found!")
        return pd.DataFrame()
        
    matched_df = pd.DataFrame(matched_indices)
    return matched_df

def check_balance(df: pd.DataFrame, covariates: List[str] = None) -> Dict[str, float]:
    """
    Check covariate balance after matching using SMD.
    
    Args:
        df: Matched DataFrame
        covariates: List of covariate column names
        
    Returns:
        Dictionary mapping covariate names to SMD values
    """
    if covariates is None:
        covariates = COVARIATES
        
    balance = {}
    
    for cov in covariates:
        if cov not in df.columns:
            continue
            
        # For matched data, we need to reconstruct the groups
        # In a real scenario, we'd have the original data linked by match_id
        # Here we assume df contains the matched pairs with original values
        
        # This is a simplified check - in practice, we'd compare the matched treated vs matched control
        # For now, we'll calculate SMD on the full dataset before matching as a proxy
        # A proper implementation would require the matched pairs to be linked
        
    return balance

def run_propensity_matching(df: pd.DataFrame, covariates: List[str] = None, max_retries: int = MAX_RETRIES) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
    """
    Run propensity score matching with retry logic for balance.
    
    Args:
        df: Input DataFrame with covariates and treatment assignment
        covariates: List of covariate column names
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (success, matched_df, result_details)
    """
    if covariates is None:
        covariates = COVARIATES
        
    logger.info(f"Starting propensity score matching with covariates: {covariates}")
    
    retry_count = 0
    current_covariates = covariates.copy()
    smd_values = {}
    success = False
    matched_df = pd.DataFrame()
    
    while retry_count <= max_retries:
        logger.info(f"Matching attempt {retry_count + 1} with covariates: {current_covariates}")
        
        try:
            # Estimate propensity scores
            df_with_scores = estimate_propensity_scores(df, current_covariates)
            
            # Perform matching
            matched_df = perform_matching(df_with_scores, ratio=1)
            
            if matched_df.empty:
                logger.warning("Matching produced no results. Retrying with modified covariates.")
                retry_count += 1
                if retry_count <= max_retries:
                    # Add interaction terms for next retry
                    if len(current_covariates) == len(covariates):
                        # First retry: add pairwise interactions
                        new_covariates = current_covariates.copy()
                        for i in range(len(covariates)):
                            for j in range(i+1, len(covariates)):
                                interaction_name = f"{covariates[i]}_x_{covariates[j]}"
                                new_covariates.append(interaction_name)
                                df_with_scores[interaction_name] = df[covariates[i]] * df[covariates[j]]
                        current_covariates = new_covariates
                    else:
                        # Subsequent retries: add squared terms
                        new_covariates = current_covariates.copy()
                        for cov in covariates:
                            squared_name = f"{cov}_sq"
                            if squared_name not in new_covariates:
                                new_covariates.append(squared_name)
                                df_with_scores[squared_name] = df[cov] ** 2
                        current_covariates = new_covariates
                continue
            
            # Check balance on matched data
            # For simplicity, we'll calculate SMD on the matched treated vs matched control
            treated_matched = df_with_scores[df_with_scores['snippet_id'].isin(matched_df['treated_id'])]
            control_matched = df_with_scores[df_with_scores['snippet_id'].isin(matched_df['control_id'])]
            
            balance_check = {}
            max_smd = 0.0
            
            for cov in current_covariates:
                if cov in treated_matched.columns and cov in control_matched.columns:
                    smd = calculate_smd(treated_matched[cov], control_matched[cov])
                    balance_check[cov] = smd
                    max_smd = max(max_smd, smd)
                    logger.info(f"SMD for {cov}: {smd:.4f}")
            
            smd_values = balance_check
            
            if max_smd <= SMD_THRESHOLD:
                logger.info(f"Balance achieved! Max SMD: {max_smd:.4f}")
                success = True
                break
            else:
                logger.warning(f"Balance not achieved (Max SMD: {max_smd:.4f}). Retrying...")
                retry_count += 1
                if retry_count <= max_retries:
                    # Add interaction terms for next retry
                    if len(current_covariates) == len(covariates):
                        # First retry: add pairwise interactions
                        new_covariates = current_covariates.copy()
                        for i in range(len(covariates)):
                            for j in range(i+1, len(covariates)):
                                interaction_name = f"{covariates[i]}_x_{covariates[j]}"
                                new_covariates.append(interaction_name)
                                df_with_scores[interaction_name] = df[covariates[i]] * df[covariates[j]]
                        current_covariates = new_covariates
                    else:
                        # Subsequent retries: add squared terms
                        new_covariates = current_covariates.copy()
                        for cov in covariates:
                            squared_name = f"{cov}_sq"
                            if squared_name not in new_covariates:
                                new_covariates.append(squared_name)
                                df_with_scores[squared_name] = df[cov] ** 2
                        current_covariates = new_covariates
                continue
                
        except Exception as e:
            logger.error(f"Error during matching attempt {retry_count + 1}: {str(e)}")
            retry_count += 1
            if retry_count <= max_retries:
                continue
            else:
                break
    
    result_details = {
        "success": success,
        "retry_count": retry_count,
        "final_covariates": current_covariates,
        "smd_values": smd_values,
        "max_smd": max(smd_values.values()) if smd_values else float('inf'),
        "threshold": SMD_THRESHOLD
    }
    
    return success, matched_df, result_details

def generate_matching_failure_report(result_details: Dict[str, Any], output_path: str = None) -> None:
    """
    Generate a failure report when matching fails to achieve balance.
    
    Args:
        result_details: Dictionary containing matching results and SMD values
        output_path: Path to write the JSON report
    """
    if output_path is None:
        output_path = MATCHING_FAILURE_REPORT_PATH
        
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    report = {
        "status": "failure",
        "reason": "SMD threshold not met after maximum retries",
        "max_retries": MAX_RETRIES,
        "actual_retries": result_details.get("retry_count", 0),
        "final_covariates": result_details.get("final_covariates", []),
        "smd_values": result_details.get("smd_values", {}),
        "max_smd": result_details.get("max_smd", float('inf')),
        "threshold": SMD_THRESHOLD,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Matching failure report written to {output_path}")

def main():
    """
    Main function to demonstrate matching with failure handling.
    This is a test runner that creates sample data and runs the matching process.
    """
    logger.info("Running matching pipeline with failure handling...")
    
    # Create sample data for testing
    np.random.seed(42)
    n_samples = 200
    
    sample_data = {
        'snippet_id': [f"snippet_{i}" for i in range(n_samples)],
        'file_size': np.random.normal(500, 200, n_samples),
        'complexity_score': np.random.normal(10, 5, n_samples),
        'activity_score': np.random.normal(5, 2, n_samples),
        'treatment': np.random.binomial(1, 0.5, n_samples)  # 50% treated
    }
    
    # Introduce some imbalance to test retry logic
    sample_data['file_size'] = sample_data['file_size'] + 100 * sample_data['treatment']
    sample_data['complexity_score'] = sample_data['complexity_score'] + 3 * sample_data['treatment']
    
    df = pd.DataFrame(sample_data)
    
    # Ensure directories exist
    ensure_directories()
    
    # Run matching
    success, matched_df, result_details = run_propensity_matching(df)
    
    if success:
        logger.info("Matching successful!")
        # Save matched results
        matched_df.to_parquet("data/processed/matched_pairs.parquet", index=False)
    else:
        logger.warning("Matching failed. Generating failure report...")
        generate_matching_failure_report(result_details)
        
        # Return failure flag
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())