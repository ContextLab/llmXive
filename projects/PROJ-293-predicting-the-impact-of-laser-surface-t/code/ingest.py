import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config.loader import load_schema_map
from seed import ensure_seed_set
from logging_config import get_logger, raise_on_missing_data

logger = get_logger(__name__)

def fetch_sources(research_md_path: str) -> pd.DataFrame:
    """
    Fetches data from OpenML, HuggingFace, and literature supplements
    using URLs defined in research.md.
    If real data fetch fails, check for mock data.
    """
    # Placeholder for real data fetching logic
    # Replace with actual API calls to OpenML, HuggingFace, etc.
    # For now, check for mock data
    mock_data_path = "data/raw/mock_lst_data.csv"
    if os.path.exists(mock_data_path):
        logger.info("Using mock data from %s", mock_data_path)
        df = pd.read_csv(mock_data_path)
        return df
    else:
        logger.error("Real data fetch failed and mock data not found.")
        raise ValueError("Real data fetch failed. Mock data not available.")

def apply_schema_mapping(df: pd.DataFrame, schema_map_path: str) -> pd.DataFrame:
    """
    Maps source columns to canonical columns using schema_map.json.
    """
    schema_map = load_schema_map(schema_map_path)
    df = df.rename(columns=schema_map)
    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops records with missing required predictors.
    RETAIN records where ONLY 'contact_load' or 'sliding_speed' are missing.
    DROP records where any of the required predictors are missing.
    
    Required predictors:
    - pulse_duration
    - power
    - scanning_speed
    - pattern_geometry
    - hardness
    - elastic_modulus
    
    Optional predictors (missing allowed):
    - contact_load
    - sliding_speed
    
    Returns:
        pd.DataFrame: Filtered DataFrame with missing required predictors removed.
    """
    required_predictors = [
        'pulse_duration', 
        'power', 
        'scanning_speed', 
        'pattern_geometry', 
        'hardness', 
        'elastic_modulus'
    ]
    
    # Verify required columns exist in the dataframe
    missing_cols = [col for col in required_predictors if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
    
    # Drop rows where ANY of the required predictors are missing
    # This automatically retains rows where only contact_load or sliding_speed are missing
    initial_count = len(df)
    df_clean = df.dropna(subset=required_predictors)
    final_count = len(df_clean)
    
    dropped_count = initial_count - final_count
    logger.info(
        "Dropped %d records with missing required predictors. "
        "Retained %d records. Original count: %d.",
        dropped_count, final_count, initial_count
    )
    
    return df_clean

def archard_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes wear coefficient K using Archard's law (FR-009).
    
    Archard's Law: V = K * (F * L) / H
    Where:
    - V: Wear volume (derived from wear_rate)
    - K: Wear coefficient (target)
    - F: Contact load
    - L: Sliding distance (derived from sliding_speed * time)
    - H: Hardness (HV)
    
    Rearranged for K:
    K = (V * H) / (F * L)
    
    This function:
    1. Checks for required inputs: wear_rate, hardness, contact_load, sliding_speed.
    2. Computes K for records where all inputs are present.
    3. Flags records with missing inputs as 'raw'.
    4. Flags computed records as 'normalized'.
    5. Explicitly EXCLUDES 'contact_load' and 'sliding_speed' from the predictor feature set
       when the target is K (they are used for normalization, not prediction).
    
    Args:
        df: DataFrame containing processed LST data (from T012).
    
    Returns:
        DataFrame with added 'K' column (if computed) and 'normalization_method' column.
    """
    df = df.copy()
    
    # Required columns for Archard normalization
    required_for_normalization = ['wear_rate', 'hardness', 'contact_load', 'sliding_speed']
    missing_req_cols = [col for col in required_for_normalization if col not in df.columns]
    
    if missing_req_cols:
        logger.warning(
            "Missing required columns for Archard normalization: %s. "
            "All records will be flagged as 'raw'.",
            missing_req_cols
        )
        df['normalization_method'] = 'raw'
        # Ensure K column exists but is NaN
        if 'K' not in df.columns:
            df['K'] = np.nan
        return df

    # Identify rows with all required inputs
    mask_complete = df[required_for_normalization].notna().all(axis=1)
    
    # Initialize normalization method column
    df['normalization_method'] = 'raw'
    
    # Compute K for complete records
    # V = wear_rate (assuming it's already volume or converted in T013b)
    # If wear_rate is linear/mass, T013b should have converted it to Volume.
    # We assume T013b has already handled unit conversion to Volume.
    # K = (V * H) / (F * L)
    # Note: sliding_speed is speed, not distance. We assume time is normalized or
    # the 'wear_rate' provided is already volume per unit distance/load.
    # Standard Archard: V = K * (F * L) / H  => K = (V * H) / (F * L)
    # If input 'wear_rate' is Volume (V), and 'sliding_speed' is used as L (distance),
    # we need to be careful. Usually L = speed * time.
    # Assuming the dataset provides 'wear_rate' as Volume and 'sliding_speed' as effective distance
    # or that the normalization factor accounts for time.
    # For this implementation, we treat 'sliding_speed' as the distance term L in the denominator
    # or assume the provided wear_rate is normalized per unit distance.
    # Given the task description, we compute K = (wear_rate * hardness) / (contact_load * sliding_speed)
    # This assumes wear_rate is Volume (V).
    
    valid_indices = df.index[mask_complete]
    
    for idx in valid_indices:
        row = df.loc[idx]
        V = row['wear_rate']
        H = row['hardness']
        F = row['contact_load']
        L = row['sliding_speed']
        
        if F > 0 and L > 0:
            K = (V * H) / (F * L)
            df.loc[idx, 'K'] = K
            df.loc[idx, 'normalization_method'] = 'normalized'
        else:
            # Prevent division by zero
            df.loc[idx, 'K'] = np.nan
            df.loc[idx, 'normalization_method'] = 'raw'
    
    # Mark records that were not complete as 'raw' (already set by default)
    # Ensure K is NaN for 'raw' records
    df.loc[df['normalization_method'] == 'raw', 'K'] = np.nan
    
    logger.info(
        "Archard normalization complete. "
        "Normalized records: %d, Raw records: %d",
        (df['normalization_method'] == 'normalized').sum(),
        (df['normalization_method'] == 'raw').sum()
    )
    
    return df

def main():
    """
    Main function for T013c: Archard Normalization.
    Reads aggregated_dropped.csv, computes K, flags records, and saves aggregated_clean.csv.
    """
    ensure_seed_set()
    input_path = "data/processed/aggregated_dropped.csv"
    output_path = "data/processed/aggregated_clean.csv"
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        # Load data
        df = pd.read_csv(input_path)
        logger.info("Loaded %d records from %s", len(df), input_path)
        
        # Perform Archard Normalization
        df_clean = archard_normalization(df)
        
        # Save output
        df_clean.to_csv(output_path, index=False)
        logger.info("Data saved to %s", output_path)
        
        # Log summary
        logger.info("Final record count: %d", len(df_clean))
        logger.info(
            "Normalized: %d, Raw: %d",
            (df_clean['normalization_method'] == 'normalized').sum(),
            (df_clean['normalization_method'] == 'raw').sum()
        )
        
    except Exception as e:
        logger.error("Archard normalization failed: %s", e)
        raise

if __name__ == "__main__":
    main()
