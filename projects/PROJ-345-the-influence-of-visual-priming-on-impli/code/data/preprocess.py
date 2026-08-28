import os
import csv
import logging
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

from config import get_path, set_seed, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_human_rated_ambiguity(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Load human-rated ambiguity scores from an external verified source.
    
    Args:
        input_path: Path to the human ratings CSV file.
        output_path: Path to write aggregated ratings if needed.
        
    Returns:
        DataFrame with stimulus_id and ambiguity_score columns.
    """
    if input_path is None:
        input_path = get_path("data/raw/human_ratings.csv")
    
    path_obj = Path(input_path)
    if not path_obj.exists():
        logger.warning(f"Human rated ambiguity file not found at {input_path}. "
                       "Proceeding with synthetic derivation pipeline.")
        return pd.DataFrame()
    
    df = pd.read_csv(path_obj)
    required_cols = ['stimulus_id', 'ambiguity_score']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Human ratings file missing required columns: {required_cols}")
    
    return df[['stimulus_id', 'ambiguity_score']]

def aggregate_human_ratings(
    df: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    """
    Aggregate human ratings if multiple raters exist per stimulus.
    """
    if df.empty:
        return pd.DataFrame()
    
    agg_df = df.groupby('stimulus_id')['ambiguity_score'].mean().reset_index()
    agg_df.columns = ['stimulus_id', 'mean_ambiguity']
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    agg_df.to_csv(output, index=False)
    logger.info(f"Aggregated human ratings saved to {output_path}")
    
    return agg_df

def derive_synthetic_ambiguity(
    linked_trials_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Derive synthetic ambiguity scores if human ratings are unavailable.
    
    This implementation uses a heuristic based on response time variance
    and consistency as a proxy for ambiguity (higher variance = higher ambiguity).
    
    Args:
        linked_trials_path: Path to linked_trials.csv.
        output_path: Path to write derived ambiguity scores.
        
    Returns:
        DataFrame with stimulus_id and derived_ambiguity columns.
    """
    if linked_trials_path is None:
        linked_trials_path = get_path("data/processed/linked_trials.csv")
        
    path_obj = Path(linked_trials_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Linked trials file not found at {linked_trials_path}")
    
    logger.info(f"Loading linked trials from {linked_trials_path}")
    df = pd.read_csv(path_obj)
    
    if 'stimulus_id' not in df.columns or 'response_time' not in df.columns:
        raise ValueError("Linked trials must contain 'stimulus_id' and 'response_time' columns")
    
    # Calculate variance of response times per stimulus as a proxy for ambiguity
    # Rationale: Ambiguous stimuli often lead to more variable response times
    # due to cognitive conflict or hesitation.
    stimulus_stats = df.groupby('stimulus_id')['response_time'].agg(['mean', 'var', 'count']).reset_index()
    stimulus_stats.columns = ['stimulus_id', 'mean_rt', 'var_rt', 'trial_count']
    
    # Filter out stimuli with insufficient trials
    valid_stimuli = stimulus_stats[stimulus_stats['trial_count'] >= 2].copy()
    
    if valid_stimuli.empty:
        raise ValueError("No stimuli with sufficient trials to derive ambiguity scores.")
    
    # Normalize variance to 0-1 scale for ambiguity score
    # Using Min-Max scaling, handling edge cases
    if valid_stimuli['var_rt'].max() > valid_stimuli['var_rt'].min():
        valid_stimuli['derived_ambiguity'] = (
            (valid_stimuli['var_rt'] - valid_stimuli['var_rt'].min()) / 
            (valid_stimuli['var_rt'].max() - valid_stimuli['var_rt'].min())
        )
    else:
        valid_stimuli['derived_ambiguity'] = 0.5  # Default if no variance
    
    # Output
    if output_path is None:
        output_path = get_path("data/processed/stimulus_metadata.csv")
        
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    # Only save necessary columns
    result_df = valid_stimuli[['stimulus_id', 'derived_ambiguity']].copy()
    result_df.to_csv(output, index=False)
    logger.info(f"Synthetic ambiguity scores derived and saved to {output_path}")
    
    return result_df

def check_confounding(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check for confounding between prime condition and trial order/block structure.
    
    This function verifies that the 'prime_condition' is not systematically 
    correlated with 'trial_order' or 'block_id', which could invalidate 
    causal interpretations.
    
    Args:
        input_path: Path to linked_trials.csv.
        output_path: Path to write confounding_report.json.
        
    Returns:
        Dictionary containing correlation matrix and check results.
        
    Raises:
        ValueError: If significant confounding is detected (|r| > 0.3).
    """
    if input_path is None:
        input_path = get_path("data/processed/linked_trials.csv")
        
    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Linked trials file not found at {input_path}")
    
    logger.info(f"Loading data for confounding check from {input_path}")
    df = pd.read_csv(path_obj)
    
    required_cols = ['prime_condition', 'trial_id', 'response_time']
    if not all(col in df.columns for col in required_cols):
        # Try to infer trial order if not present
        if 'trial_order' not in df.columns:
            # Create a simple trial order based on trial_id if possible, 
            # or assume sequential order in the file
            df['trial_order'] = range(len(df))
            logger.warning("No 'trial_order' column found; assuming sequential order.")
        
        # Map prime_condition to numeric for correlation if it's categorical
        # We assume binary or ordinal prime conditions for this check
        if 'prime_condition' in df.columns and df['prime_condition'].dtype == 'object':
            # One-hot encode or label encode
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            df['prime_condition_numeric'] = le.fit_transform(df['prime_condition'])
            prime_col = 'prime_condition_numeric'
        else:
            prime_col = 'prime_condition'
    else:
        if 'trial_order' not in df.columns:
            df['trial_order'] = range(len(df))
        if df['prime_condition'].dtype == 'object':
            from sklearn.preprocessing import LabelEncoder
            le = LabelEncoder()
            df['prime_condition_numeric'] = le.fit_transform(df['prime_condition'])
            prime_col = 'prime_condition_numeric'
        else:
            prime_col = 'prime_condition'
    
    # Calculate correlations
    # We check correlation between prime condition and trial order
    # Also check between prime condition and block (if available)
    
    results = {
        "check_timestamp": str(pd.Timestamp.now()),
        "input_file": str(path_obj),
        "checks_performed": [],
        "correlation_matrix": {},
        "confounding_detected": False,
        "details": {}
    }
    
    # 1. Prime vs Trial Order
    if prime_col in df.columns and 'trial_order' in df.columns:
        corr_order = df[prime_col].corr(df['trial_order'])
        results["checks_performed"].append("prime_vs_trial_order")
        results["correlation_matrix"]["prime_vs_trial_order"] = float(corr_order)
        
        threshold = 0.3
        if abs(corr_order) > threshold:
            results["confounding_detected"] = True
            results["details"]["prime_vs_trial_order"] = {
                "correlation": float(corr_order),
                "threshold": threshold,
                "status": "FAIL",
                "message": f"Significant correlation ({corr_order:.4f}) between prime condition and trial order detected. "
                           "This may indicate a systematic confound."
            }
        else:
            results["details"]["prime_vs_trial_order"] = {
                "correlation": float(corr_order),
                "threshold": threshold,
                "status": "PASS",
                "message": "No significant correlation between prime condition and trial order."
            }
    
    # 2. Prime vs Block (if block_id exists)
    if 'block_id' in df.columns and prime_col in df.columns:
        # Convert block_id to numeric if needed
        block_numeric = pd.Categorical(df['block_id']).codes
        corr_block = df[prime_col].corr(block_numeric)
        results["checks_performed"].append("prime_vs_block_id")
        results["correlation_matrix"]["prime_vs_block_id"] = float(corr_block)
        
        threshold = 0.3
        if abs(corr_block) > threshold:
            results["confounding_detected"] = True
            results["details"]["prime_vs_block_id"] = {
                "correlation": float(corr_block),
                "threshold": threshold,
                "status": "FAIL",
                "message": f"Significant correlation ({corr_block:.4f}) between prime condition and block ID detected."
            }
        else:
            results["details"]["prime_vs_block_id"] = {
                "correlation": float(corr_block),
                "threshold": threshold,
                "status": "PASS",
                "message": "No significant correlation between prime condition and block ID."
            }
    
    # 3. Check for perfect balance (ideal case)
    if 'prime_condition' in df.columns and 'trial_order' in df.columns:
        # Count trials per prime per block/order bin (simplified)
        # This is a more robust check
        prime_counts = df.groupby('prime_condition').size()
        total_trials = len(df)
        balance_ratio = prime_counts.min() / prime_counts.max()
        results["details"]["balance_check"] = {
            "min_prime_count": int(prime_counts.min()),
            "max_prime_count": int(prime_counts.max()),
            "balance_ratio": float(balance_ratio),
            "status": "PASS" if balance_ratio > 0.8 else "WARNING"
        }
    
    # Write output
    if output_path is None:
        output_path = get_path("data/processed/confounding_report.json")
        
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Confounding report saved to {output_path}")
    
    if results["confounding_detected"]:
        logger.error("CONFOUNDING DETECTED: The experiment design may be compromised.")
        raise ValueError("Confounding detected between prime condition and trial order/block structure.")
    
    logger.info("Confounding check passed. No significant confounding detected.")
    return results

def run_preprocessing(
    linked_trials_path: Optional[str] = None,
    human_ratings_path: Optional[str] = None,
    output_metadata_path: Optional[str] = None,
    confounding_report_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline:
    1. Load or derive ambiguity scores.
    2. Check for confounding.
    3. Merge metadata with trial data.
    
    Args:
        linked_trials_path: Path to linked_trials.csv.
        human_ratings_path: Path to human ratings CSV (optional).
        output_metadata_path: Path to write stimulus metadata CSV.
        confounding_report_path: Path to write confounding report JSON.
        
    Returns:
        Dictionary with pipeline results.
    """
    set_seed(42)
    ensure_directories()
    
    results = {
        "ambiguity_source": "unknown",
        "confounding_status": "unknown",
        "metadata_rows": 0
    }
    
    # Step 1: Handle Ambiguity Scores
    logger.info("Step 1: Checking for human-rated ambiguity...")
    human_df = load_human_rated_ambiguity(input_path=human_ratings_path)
    
    if not human_df.empty:
        logger.info("Human ratings found. Aggregating...")
        agg_df = aggregate_human_ratings(human_df, output_metadata_path or get_path("data/processed/stimulus_metadata.csv"))
        results["ambiguity_source"] = "human_rated"
        results["metadata_rows"] = len(agg_df)
    else:
        logger.info("No human ratings found. Deriving synthetic ambiguity...")
        try:
            synth_df = derive_synthetic_ambiguity(
                linked_trials_path=linked_trials_path,
                output_path=output_metadata_path or get_path("data/processed/stimulus_metadata.csv")
            )
            results["ambiguity_source"] = "synthetic"
            results["metadata_rows"] = len(synth_df)
        except Exception as e:
            logger.error(f"Ambiguity derivation failed: {e}")
            raise ValueError("Data Gap: Ambiguity derivation failed.") from e
    
    # Step 2: Confounding Check
    logger.info("Step 2: Running confounding check...")
    try:
        conf_results = check_confounding(
            input_path=linked_trials_path,
            output_path=confounding_report_path or get_path("data/processed/confounding_report.json")
        )
        results["confounding_status"] = "passed"
    except ValueError as e:
        logger.error(f"Confounding check failed: {e}")
        results["confounding_status"] = "failed"
        raise
    
    logger.info("Preprocessing pipeline completed successfully.")
    return results

def main():
    """
    Entry point for the preprocessing script.
    """
    logger.info("Starting preprocessing pipeline...")
    
    try:
        run_preprocessing()
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
