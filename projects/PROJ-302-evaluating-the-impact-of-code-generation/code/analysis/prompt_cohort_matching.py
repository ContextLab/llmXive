import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import matching logic from existing US2 implementation
from analysis.matching import calculate_smd, estimate_propensity_scores, perform_matching, check_balance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
COHORT_SEGMENTS_PATH = Path("data/processed/cohort_segments.parquet")
MATCHING_FAILURE_REPORT_PATH = Path("data/processed/prompt_cohort_matching_failure.json")
MATCHED_PAIRS_PATH = Path("data/processed/prompt_cohort_matched_pairs.parquet")
BALANCE_REPORT_PATH = Path("data/processed/prompt_cohort_balance_report.json")

COVARIATES = ["file_size", "complexity_score", "activity_score"]
MAX_RETRIES = 3
SMD_THRESHOLD = 0.1

def load_prompt_cohort_data() -> pd.DataFrame:
    """
    Load the segmented cohort data containing 'Prompt-Based', 'LLM-like', and 'Human' groups.
    """
    if not COHORT_SEGMENTS_PATH.exists():
        raise FileNotFoundError(
            f"Cohort segments file not found at {COHORT_SEGMENTS_PATH}. "
            "Ensure T033a (cohort_analyzer) has been run successfully."
        )
    
    logger.info(f"Loading cohort segments from {COHORT_SEGMENTS_PATH}")
    df = pd.read_parquet(COHORT_SEGMENTS_PATH)
    
    # Validate required columns
    required_cols = ["cohort_type"] + COVARIATES + ["review_duration"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in cohort data: {missing}")
    
    logger.info(f"Loaded {len(df)} rows. Cohort distribution:\n{df['cohort_type'].value_counts()}")
    return df

def prepare_cohort_for_matching(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Separate the data into Prompt-Based (treatment) and Human (control) groups.
    Filter out 'LLM-like' group as it is not part of this specific matching task.
    """
    logger.info("Preparing cohorts for matching...")
    
    treatment = df[df["cohort_type"] == "Prompt-Based"].copy()
    control = df[df["cohort_type"] == "Human"].copy()
    
    logger.info(f"Treatment (Prompt-Based) size: {len(treatment)}")
    logger.info(f"Control (Human) size: {len(control)}")
    
    if len(treatment) == 0:
        raise ValueError("No 'Prompt-Based' samples found in cohort data. Cannot proceed with matching.")
    if len(control) == 0:
        raise ValueError("No 'Human' samples found in cohort data. Cannot proceed with matching.")
    
    return treatment, control

def run_prompt_cohort_matching(treatment: pd.DataFrame, control: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform propensity score matching between Prompt-Based and Human cohorts.
    Returns matched pairs and a balance report.
    """
    logger.info("Starting propensity score matching for Prompt Cohort...")
    
    # Combine for propensity estimation
    treatment["group"] = 1
    control["group"] = 0
    combined = pd.concat([treatment, control], ignore_index=True)
    
    # Estimate propensity scores
    combined["propensity_score"] = estimate_propensity_scores(combined, COVARIATES, "group")
    
    # Perform matching (1:1 nearest neighbor with replacement)
    logger.info("Performing matching...")
    matched_indices = perform_matching(
        combined, 
        treatment_col="group", 
        covariate_cols=COVARIATES, 
        score_col="propensity_score",
        ratio=1,
        replace=True
    )
    
    matched_df = combined.iloc[matched_indices].copy()
    
    # Calculate balance
    balance_report = check_balance(matched_df, COVARIATES, "group")
    
    # Check if balance is achieved
    smds = [balance_report[c]["smd"] for c in COVARIATES]
    max_smd = max(abs(s) for s in smds)
    
    if max_smd > SMD_THRESHOLD:
        logger.warning(f"Balance not achieved. Max SMD: {max_smd:.4f} > {SMD_THRESHOLD}")
        return matched_df, balance_report, False
    
    logger.info(f"Matching successful. Max SMD: {max_smd:.4f}")
    return matched_df, balance_report, True

def generate_matching_failure_report(report: Dict[str, Any], reason: str) -> None:
    """
    Write a failure report to disk if matching fails.
    """
    failure_data = {
        "timestamp": str(pd.Timestamp.now()),
        "reason": reason,
        "details": report
    }
    with open(MATCHING_FAILURE_REPORT_PATH, "w") as f:
        json.dump(failure_data, f, indent=2)
    logger.error(f"Matching failure report written to {MATCHING_FAILURE_REPORT_PATH}")

def main():
    """
    Main entry point for Prompt Cohort Matching (T034).
    """
    try:
        # 1. Load Data
        df = load_prompt_cohort_data()
        
        # 2. Prepare Cohorts
        treatment, control = prepare_cohort_for_matching(df)
        
        # 3. Run Matching
        matched_df, balance_report, success = run_prompt_cohort_matching(treatment, control)
        
        # 4. Handle Results
        if not success:
            logger.warning("Matching failed to achieve balance. Generating failure report.")
            generate_matching_failure_report(balance_report, "SMD > 0.1 after matching")
            # Note: We still save the matched pairs for diagnostic purposes, but flag failure
        
        # 5. Save Outputs
        # Save matched pairs
        matched_df.to_parquet(MATCHED_PAIRS_PATH, index=False)
        logger.info(f"Saved matched pairs to {MATCHED_PAIRS_PATH}")
        
        # Save balance report
        with open(BALANCE_REPORT_PATH, "w") as f:
            json.dump(balance_report, f, indent=2)
        logger.info(f"Saved balance report to {BALANCE_REPORT_PATH}")
        
        # 6. Return status for pipeline gate
        return success
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        # Attempt to write a generic failure report
        try:
            generate_matching_failure_report({"error": str(e)}, "Unexpected exception")
        except:
            pass
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
