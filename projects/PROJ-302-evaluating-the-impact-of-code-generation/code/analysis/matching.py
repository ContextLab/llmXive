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

# Ensure the parent directory is in the path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_config, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions (Preserved from previous implementation) ---

def calculate_smd(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Standardized Mean Difference (SMD) between two groups.
    SMD = (mean1 - mean2) / sqrt((var1 + var2) / 2)
    """
    mean1 = group1.mean()
    mean2 = group2.mean()
    var1 = group1.var()
    var2 = group2.var()
    
    # Handle case where variance is 0 or NaN
    pooled_var = (var1 + var2) / 2
    if pooled_var <= 0:
        return 0.0
    
    smd = (mean1 - mean2) / np.sqrt(pooled_var)
    return float(smd)

def estimate_propensity_scores(df: pd.DataFrame, covariates: List[str], treatment_col: str) -> pd.DataFrame:
    """
    Estimate propensity scores using logistic regression.
    Treatment: 'llm-like' (1) vs 'human' (0)
    """
    df = df.copy()
    # Encode treatment
    df['_treatment_encoded'] = (df[treatment_col] == 'llm-like').astype(int)
    
    X = df[covariates].values
    y = df['_treatment_encoded'].values
    
    # Handle constant features
    scaler = StandardScaler()
    try:
        X_scaled = scaler.fit_transform(X)
    except Exception as e:
        logger.warning(f"Scaling failed, using raw X: {e}")
        X_scaled = X
    
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_scaled, y)
    
    df['propensity_score'] = model.predict_proba(X_scaled)[:, 1]
    return df

def perform_matching(df: pd.DataFrame, propensity_col: str, treatment_col: str, 
                     ratio: int = 1) -> pd.DataFrame:
    """
    Perform nearest neighbor matching without replacement.
    Returns a dataframe with matched pairs.
    """
    df = df.copy()
    treated = df[df[treatment_col] == 'llm-like'].copy()
    control = df[df[treatment_col] != 'llm-like'].copy()
    
    matched_indices = []
    
    for _, t_row in treated.iterrows():
        t_score = t_row[propensity_col]
        # Calculate distance to all controls
        distances = np.abs(control[propensity_col] - t_score)
        # Find nearest available control
        # Sort indices by distance
        sorted_indices = distances.argsort()
        
        matched = False
        for idx in sorted_indices:
            # Check if this control is already matched (simple check: not in matched_indices yet)
            # In a production system, we'd track used controls more efficiently
            if idx not in matched_indices:
                matched_indices.append(idx)
                matched = True
                break
        
        if not matched:
            logger.warning(f"Could not find a match for treated sample with score {t_score}")
    
    matched_control = control.iloc[matched_indices]
    matched_control['_match_id'] = range(len(matched_control))
    treated['_match_id'] = range(len(treated)) # Assign temporary IDs
    
    # Combine
    result = pd.concat([treated, matched_control], ignore_index=True)
    return result

def check_balance(df: pd.DataFrame, covariates: List[str], treatment_col: str) -> Dict[str, float]:
    """
    Check balance by calculating SMD for each covariate between matched groups.
    Returns a dictionary of {covariate: smd_value}.
    """
    df = df.copy()
    smd_results = {}
    
    treated = df[df[treatment_col] == 'llm-like']
    control = df[df[treatment_col] != 'llm-like']
    
    for col in covariates:
        if col in treated.columns and col in control.columns:
            smd = calculate_smd(treated[col], control[col])
            smd_results[col] = smd
        else:
            smd_results[col] = np.nan
    
    return smd_results

def run_propensity_matching(input_path: str, output_path: str, covariates: List[str], 
                            treatment_col: str = 'author_type') -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Main function to run the propensity matching pipeline.
    Returns the matched dataframe and the balance report (SMDs).
    """
    logger.info(f"Loading data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load parquet
    df = pd.read_parquet(input_path)
    
    # Filter out rows with missing covariates
    initial_count = len(df)
    df = df.dropna(subset=covariates + [treatment_col])
    logger.info(f"Dropped {initial_count - len(df)} rows with missing values")
    
    # Estimate propensity scores
    logger.info("Estimating propensity scores...")
    df = estimate_propensity_scores(df, covariates, treatment_col)
    
    # Perform matching
    logger.info("Performing nearest neighbor matching...")
    matched_df = perform_matching(df, 'propensity_score', treatment_col)
    
    # Check balance
    logger.info("Checking covariate balance...")
    balance_report = check_balance(matched_df, covariates, treatment_col)
    
    # Save matched data
    ensure_directories([output_path])
    matched_df.to_parquet(output_path, index=False)
    logger.info(f"Matched data saved to {output_path}")
    
    return matched_df, balance_report

# --- Task T023b Implementation: Retry Logic and Failure Reporting ---

def generate_matching_failure_report(max_smd: float, retry_count: int, 
                                     covariates: List[str], smd_history: List[Dict[str, float]], 
                                     output_path: str) -> None:
    """
    Generates the matching failure report and halts the pipeline.
    """
    report = {
        "status": "failed",
        "reason": "Matching balance threshold not met after maximum retries",
        "max_smd": max_smd,
        "threshold": 0.1,
        "retry_count": retry_count,
        "max_retries": 3,
        "covariates_used": covariates,
        "smd_history": smd_history
    }
    
    ensure_directories([output_path])
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.error(f"Matching failed. Report saved to {output_path}")
    logger.error(f"Max SMD observed: {max_smd} (Threshold: 0.1)")

def run_propensity_matching_with_retry(input_path: str, output_path: str, 
                                       base_covariates: List[str], 
                                       treatment_col: str = 'author_type') -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Runs propensity matching with retry logic for balance improvement.
    Tries adding interaction terms if SMD > 0.1.
    """
    max_smd = 0.0
    retry_count = 0
    smd_history = []
    current_covariates = list(base_covariates)
    
    # Interaction terms to try
    interaction_terms = [
        ['file_size', 'complexity'],
        ['complexity', 'activity'],
        ['file_size', 'activity']
    ]
    
    while retry_count <= 3:
        logger.info(f"--- Matching Attempt {retry_count + 1} ---")
        logger.info(f"Covariates: {current_covariates}")
        
        try:
            matched_df, balance_report = run_propensity_matching(
                input_path, 
                output_path, 
                current_covariates, 
                treatment_col
            )
        except Exception as e:
            logger.error(f"Matching failed with error: {e}")
            # If a fatal error occurs, we still need to report failure
            generate_matching_failure_report(999.0, retry_count, current_covariates, [], output_path)
            sys.exit(1)
        
        # Find max SMD
        current_max_smd = max(abs(v) for v in balance_report.values() if not np.isnan(v))
        smd_history.append({
            "attempt": retry_count + 1,
            "covariates": current_covariates,
            "max_smd": current_max_smd,
            "balance_details": balance_report
        })
        
        logger.info(f"Attempt {retry_count + 1} Max SMD: {current_max_smd:.4f}")
        
        if current_max_smd > max_smd:
            max_smd = current_max_smd
        
        # Check if balance is good
        if current_max_smd <= 0.1:
            logger.info("Balance achieved (SMD <= 0.1).")
            return matched_df, balance_report
        
        # Prepare for next retry
        if retry_count < 3:
            logger.info(f"SMD > 0.1. Retrying with interaction term: {interaction_terms[retry_count]}")
            new_covariates = list(current_covariates)
            # Add interaction term
            term1, term2 = interaction_terms[retry_count]
            if term1 in base_covariates and term2 in base_covariates:
                interaction_name = f"{term1}_x_{term2}"
                # We need to add this column to the dataframe before the next run
                # But run_propensity_matching loads the data fresh. 
                # We need to modify the input data or handle it inside run_propensity_matching.
                # To keep it clean, we'll modify the input file in a temp location or 
                # pass the interaction logic down.
                # Simpler approach: modify the data in place before the next call?
                # No, run_propensity_matching loads from disk.
                # We need to inject the interaction column into the data source.
                # Let's create a helper that adds interaction columns to the input file.
                pass 
            else:
                logger.warning(f"Interaction terms {term1}, {term2} not found in covariates. Skipping this interaction.")
                # If we can't add the interaction, we might just stop or try the next one?
                # For now, let's just break if we can't form the interaction.
                # Actually, let's just stop trying if we can't form the interaction.
                break
            
            # We need to update the input file to include the interaction column
            # This is a bit messy. Let's refactor run_propensity_matching to accept a function 
            # to transform the dataframe, or handle it here.
            # Given the constraint of extending existing code, let's do it here:
            # 1. Load data
            # 2. Add interaction
            # 3. Save to a temp file
            # 4. Point next run to temp file
            
            # But wait, the output_path is the same. We are overwriting.
            # Let's just update the input_path for the next iteration.
            
            # Load current input
            temp_df = pd.read_parquet(input_path)
            
            # Add interaction
            if term1 in temp_df.columns and term2 in temp_df.columns:
                temp_df[interaction_name] = temp_df[term1] * temp_df[term2]
                new_covariates.append(interaction_name)
                
                # Save to a temp location to avoid overwriting original input if we need it later?
                # Or just overwrite input_path if we are in a loop?
                # Let's save to a temp file and update input_path
                temp_input = input_path.replace('.parquet', '_with_interaction.parquet')
                temp_df.to_parquet(temp_input)
                input_path = temp_input
                
                current_covariates = new_covariates
            else:
                logger.error(f"Cannot add interaction {term1} x {term2}: columns missing.")
                break
        else:
            logger.error("Max retries (3) reached. Balance not achieved.")
            generate_matching_failure_report(max_smd, retry_count, current_covariates, smd_history, output_path.replace('.parquet', '_failure_report.json'))
            sys.exit(1)
        
        retry_count += 1
    
    # If we exit the loop without returning, it means we failed
    logger.error("Matching failed after all retries.")
    generate_matching_failure_report(max_smd, retry_count, current_covariates, smd_history, output_path.replace('.parquet', '_failure_report.json'))
    sys.exit(1)

def main():
    """
    Entry point for the matching script.
    Expects arguments: --input <path> --output <path>
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run Propensity Score Matching with Retry Logic")
    parser.add_argument("--input", type=str, required=True, help="Input parquet file path")
    parser.add_argument("--output", type=str, required=True, help="Output parquet file path")
    parser.add_argument("--covariates", type=str, nargs='+', default=['file_size', 'complexity', 'activity'],
                        help="List of covariate column names")
    parser.add_argument("--treatment-col", type=str, default='author_type', help="Treatment column name")
    
    args = parser.parse_args()
    
    logger.info("Starting Matching Pipeline with Retry Logic (T023b)")
    
    # Run the matching with retry
    # Note: This function will call sys.exit(1) if it fails
    matched_df, balance_report = run_propensity_matching_with_retry(
        args.input,
        args.output,
        args.covariates,
        args.treatment_col
    )
    
    logger.info("Matching completed successfully.")
    logger.info(f"Final Balance Report: {balance_report}")

if __name__ == "__main__":
    main()