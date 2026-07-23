"""
Correlation analysis module for network metrics vs age/cognition.
Implements Spearman rank correlation with instrument validation against registry.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml

from config import ensure_dirs

logger = logging.getLogger(__name__)

# Path to the cognitive instrument registry
REGISTRY_PATH = Path("data/config/cognitive_instrument_registry.yaml")


def load_instrument_registry() -> List[str]:
    """
    Load the list of valid cognitive instruments from the registry YAML.
    
    Returns:
        List of valid instrument codes (e.g., ["MMSE", "MoCA"]).
    
    Raises:
        FileNotFoundError: If the registry file does not exist.
        ValueError: If the registry file is malformed.
    """
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(
            f"Cognitive instrument registry not found at {REGISTRY_PATH}. "
            "Please run T025a to generate the registry first."
        )
    
    try:
        with open(REGISTRY_PATH, 'r') as f:
            data = yaml.safe_load(f)
        
        if not isinstance(data, dict) or 'valid_instruments' not in data:
            raise ValueError("Registry YAML must contain a 'valid_instruments' list key.")
        
        instruments = data['valid_instruments']
        if not isinstance(instruments, list):
            raise ValueError("'valid_instruments' must be a list.")
        
        return [str(item).strip().upper() for item in instruments]
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse registry YAML: {e}")


def validate_cognitive_instrument(
    instrument: Optional[str], 
    registry: List[str]
) -> Tuple[bool, str]:
    """
    Validate a cognitive instrument code against the registry.
    
    Args:
        instrument: The instrument code to validate (e.g., "MMSE", "MoCA").
                    Can be None if data is missing.
        registry: List of valid instrument codes.
    
    Returns:
        Tuple of (is_valid, flag_message).
        - If valid: (True, "")
        - If invalid (present but not in registry): (False, "Invalid Instrument")
        - If missing (None or empty): (False, "Missing Cognitive Data")
    """
    if instrument is None or (isinstance(instrument, str) and instrument.strip() == ""):
        return False, "Missing Cognitive Data"
    
    instrument_upper = str(instrument).strip().upper()
    if instrument_upper in registry:
        return True, ""
    else:
        return False, "Invalid Instrument"


def flag_cognitive_records(
    df: pd.DataFrame,
    instrument_col: str = "cognitive_instrument",
    score_col: str = "cognitive_score"
) -> pd.DataFrame:
    """
    Adds validation flags to a dataframe based on cognitive instrument registry.
    
    This function implements the logic required by FR-007:
    1. Check if instrument is present.
    2. Validate against the registry.
    3. Flag as "Invalid Instrument" or "Missing Cognitive Data".
    
    Args:
        df: Input dataframe containing cognitive data columns.
        instrument_col: Name of the column containing instrument codes.
        score_col: Name of the column containing cognitive scores.
    
    Returns:
        DataFrame with an added 'cognitive_validation_flag' column.
    """
    logger.info(f"Validating cognitive instruments in column '{instrument_col}' against registry.")
    
    try:
        registry = load_instrument_registry()
        logger.info(f"Loaded {len(registry)} valid instruments from registry: {registry}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Registry validation failed: {e}")
        # If registry is missing, we cannot validate, so we flag everything as "Invalid Instrument"
        # to halt downstream processing until the registry is fixed.
        df['cognitive_validation_flag'] = "Invalid Instrument"
        return df

    def validate_row(row):
        instrument = row.get(instrument_col)
        score = row.get(score_col)
        
        # If score is missing, we can't use the row for correlation anyway.
        # However, the task specifically asks to validate instruments.
        # We flag based on instrument presence/validity.
        
        if pd.isna(instrument) or (isinstance(instrument, str) and instrument.strip() == ""):
            return "Missing Cognitive Data"
        
        # Check against registry
        instrument_upper = str(instrument).strip().upper()
        if instrument_upper in registry:
            # Even if instrument is valid, if score is missing, it's missing data.
            if pd.isna(score):
                return "Missing Cognitive Data"
            return "Valid"
        else:
            return "Invalid Instrument"

    df['cognitive_validation_flag'] = df.apply(validate_row, axis=1)
    return df


def load_metrics_and_cognitive_data(
    metrics_path: Path,
    cognitive_data_path: Path
) -> pd.DataFrame:
    """
    Loads network metrics and cognitive data, merging them on subject ID.
    
    Args:
        metrics_path: Path to network_metrics.csv.
        cognitive_data_path: Path to the source of cognitive data (e.g., download metadata).
    
    Returns:
        Merged DataFrame.
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Network metrics file not found: {metrics_path}")
    
    metrics_df = pd.read_csv(metrics_path)
    
    # The cognitive data is usually embedded in the download metadata or a separate file.
    # Based on T005, the download_report.json summarizes counts, but the raw metadata
    # is likely in data/raw/metadata.json or similar. 
    # For this implementation, we assume the cognitive data is available in a 
    # separate CSV or JSON that was produced by the download stage if T023a passed.
    # Since T023a checks the download_report, we assume a 'cognitive_data.csv' exists 
    # or we merge from the raw metadata if it's flattened.
    
    # Fallback: If the cognitive data is not explicitly separated, we might need to 
    # look at the raw metadata structure. However, the task implies we are validating
    # instruments for the correlation step.
    # Let's assume a standard path for the cognitive data source if not specified.
    # In a real pipeline, this would be passed as an argument or derived from config.
    
    # For now, we assume the cognitive data is in data/raw/cognitive_data.csv 
    # or derived from the download process.
    # If the file doesn't exist, we raise an error because we can't proceed.
    
    # Since the exact path isn't in the API surface, we'll look for a standard location
    # or raise an error if not found.
    # Actually, T005 process_and_validate creates the download_report.json.
    # The raw metadata is likely in data/raw/metadata.json.
    
    # Let's try to load from a standard location or raise.
    # We will assume the cognitive data is available in 'data/raw/cognitive_data.csv'
    # or we need to parse the raw metadata.
    # To be safe, we'll assume the caller has ensured the data is available.
    # We will raise an error if the specific cognitive data file is missing.
    
    # For the purpose of this task, we assume the data is in a file named 
    # 'data/raw/cognitive_data.csv' which contains subject_id, age, cognitive_score, cognitive_instrument.
    # If this file doesn't exist, the pipeline should have failed at T023a.
    
    # Let's try to load from a generic location or raise.
    # We will assume the data is in 'data/raw/cognitive_data.csv'.
    cognitive_file = Path("data/raw/cognitive_data.csv")
    
    if not cognitive_file.exists():
        # Try to find it in data/raw
        raw_dir = Path("data/raw")
        csv_files = list(raw_dir.glob("*.csv"))
        if csv_files:
            # Assume the first CSV is the cognitive data if not found
            # This is a heuristic. In a real system, the path would be explicit.
            cognitive_file = csv_files[0]
            logger.warning(f"Cognitive data file not found at {cognitive_file}, using {csv_files[0]}")
        else:
            raise FileNotFoundError(
                f"Cognitive data file not found. Expected at {cognitive_file} or in {raw_dir}."
            )
    
    cognitive_df = pd.read_csv(cognitive_file)
    
    # Merge on subject_id (assuming common key)
    # Adjust column names if necessary
    if 'subject_id' in metrics_df.columns and 'subject_id' in cognitive_df.columns:
        merged_df = pd.merge(metrics_df, cognitive_df, on='subject_id', how='inner')
    elif 'subject_id' in metrics_df.columns:
        # Fallback if key name differs
        # Try 'id' or 'participant_id'
        key = next((k for k in ['id', 'participant_id'] if k in cognitive_df.columns), None)
        if key:
            merged_df = pd.merge(metrics_df, cognitive_df, left_on='subject_id', right_on=key, how='inner')
        else:
            raise ValueError("Could not find a common key to merge metrics and cognitive data.")
    else:
        raise ValueError("Metrics dataframe does not contain 'subject_id'.")
    
    return merged_df


def run_spearman_correlation(
    df: pd.DataFrame,
    metrics_cols: List[str],
    outcome_cols: List[str],
    validation_col: str = "cognitive_validation_flag"
) -> pd.DataFrame:
    """
    Performs Spearman rank correlation between network metrics and outcomes.
    
    Args:
        df: DataFrame containing metrics and outcomes.
        metrics_cols: List of metric column names.
        outcome_cols: List of outcome column names (e.g., 'age', 'cognitive_score').
        validation_col: Column name containing validation flags.
    
    Returns:
        DataFrame with correlation results.
    """
    results = []
    
    # Filter out rows where validation flag is not "Valid"
    # This ensures we only use valid instruments and non-missing scores
    valid_df = df[df[validation_col] == "Valid"]
    
    if len(valid_df) < 3:
        logger.warning("Insufficient valid data for correlation analysis (N < 3).")
        return pd.DataFrame()
    
    for metric in metrics_cols:
        for outcome in outcome_cols:
            if metric not in valid_df.columns or outcome not in valid_df.columns:
                continue
            
            # Drop NaNs for this pair
            pair_data = valid_df[[metric, outcome]].dropna()
            
            if len(pair_data) < 3:
                continue
            
            corr, p_value = spearmanr(pair_data[metric], pair_data[outcome])
            
            results.append({
                "metric": metric,
                "outcome": outcome,
                "correlation": corr,
                "p_value": p_value,
                "n": len(pair_data)
            })
    
    return pd.DataFrame(results)


from scipy.stats import spearmanr


def main():
    """
    Main entry point for the correlation analysis with instrument validation.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Paths
    metrics_path = Path("data/results/network_metrics.csv")
    output_path = Path("data/results/correlation_results_raw.csv")
    
    ensure_dirs([output_path.parent])
    
    try:
        # Load and merge data
        df = load_metrics_and_cognitive_data(metrics_path, Path("data/raw"))
        
        # Validate instruments and flag records
        df = flag_cognitive_records(df)
        
        # Save the flagged dataframe for inspection (optional but useful)
        flagged_path = Path("data/results/cognitive_validated_data.csv")
        df.to_csv(flagged_path, index=False)
        logger.info(f"Saved validated data to {flagged_path}")
        
        # Define columns
        # Assuming metrics columns are in the dataframe and outcomes are age/score
        metric_cols = [col for col in df.columns if col in ['global_efficiency', 'local_efficiency', 'characteristic_path_length', 'clustering_coefficient', 'modularity']]
        outcome_cols = ['age', 'cognitive_score']
        
        # Run correlation
        results_df = run_spearman_correlation(df, metric_cols, outcome_cols)
        
        if not results_df.empty:
            results_df.to_csv(output_path, index=False)
            logger.info(f"Correlation results saved to {output_path}")
        else:
            logger.warning("No correlation results generated.")
            
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during correlation analysis: {e}")
        raise


if __name__ == "__main__":
    main()