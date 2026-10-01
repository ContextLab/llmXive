import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from existing project modules
from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Derive dilemma complexity scores from filtered Moral Machine data."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the filtered Moral Machine dataset (parquet or csv).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the derived complexity scores (CSV).",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory for log files. If None, uses config default.",
    )
    return parser.parse_args()

def ensure_directories(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

def calculate_complexity_score(row: pd.Series) -> float:
    """
    Calculate a static complexity score based on lives at stake and dilemma type.
    
    Complexity heuristic:
    1. Base score = total lives involved in the dilemma (sum of lives on both sides).
    2. Complexity modifier:
       - If the dilemma involves a "pedestrian" vs "passengers" trade-off (common in MM),
         add 0.5.
       - If the dilemma involves a large disparity in numbers (e.g., 1 vs 5),
         add 0.2.
       - If the dilemma involves a "save few" vs "save many" where the 'few' are
         a specific protected group (e.g., children, though MM doesn't strictly label
         them as such in raw columns, we infer from 'number_of_people' columns if available),
         add 0.3.
    
    Since the raw Moral Machine dataset columns vary, we use a robust approach:
    - Sum the number of people on the 'left' and 'right' sides if those columns exist.
    - If specific 'lives' columns exist (e.g., 'lives_left', 'lives_right'), use them.
    - Fallback: If the dataset has been pre-processed to include a 'total_lives' column, use it.
    
    This function is designed to work with the filtered dataset from T017-run,
    which should have standard column names or be adaptable.
    """
    # Attempt to identify total lives involved
    total_lives = 0
    
    # Common column names in Moral Machine dataset for lives
    left_lives_cols = ['number_of_people_left', 'lives_left', 'n_left']
    right_lives_cols = ['number_of_people_right', 'lives_right', 'n_right']
    
    # Check for left lives
    for col in left_lives_cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                total_lives += int(val)
            break
    
    # Check for right lives
    for col in right_lives_cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                total_lives += int(val)
            break
    
    # Fallback: if no specific columns found, try to infer from other numeric columns
    # This is a heuristic and might need adjustment based on the exact schema of the input
    if total_lives == 0:
        # Look for any column that looks like a count of people
        for col in row.index:
            if 'people' in col.lower() or 'lives' in col.lower() or col.startswith('n_'):
                val = row[col]
                if pd.notna(val) and isinstance(val, (int, float)):
                    total_lives += int(val)
    
    # Base complexity is the total number of lives
    complexity = float(total_lives)
    
    # Add modifiers based on dilemma characteristics
    # Modifier 1: Disparity check (e.g., 1 vs 5 is more complex than 2 vs 2)
    # We need to find the individual sides to check disparity
    left_val = 0
    right_val = 0
    
    for col in left_lives_cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                left_val = int(val)
            break
    
    for col in right_lives_cols:
        if col in row.index:
            val = row[col]
            if pd.notna(val):
                right_val = int(val)
            break
    
    if left_val > 0 and right_val > 0:
        # Calculate disparity ratio
        max_lives = max(left_val, right_val)
        min_lives = min(left_val, right_val)
        if max_lives > 0:
            disparity_ratio = min_lives / max_lives
            # If the ratio is low (high disparity), add complexity
            if disparity_ratio < 0.3:
                complexity += 0.2
    
    # Modifier 2: Specific dilemma types (if identifiable)
    # The Moral Machine dataset often has a 'dilemma_type' or similar, but it's not standard.
    # We can look for columns like 'pedestrians_left', 'pedestrians_right', etc.
    # If such columns exist and are non-zero, it might indicate a more complex ethical scenario.
    pedestrian_cols = ['pedestrians_left', 'pedestrians_right', 'ped_left', 'ped_right']
    has_pedestrians = False
    for col in pedestrian_cols:
        if col in row.index and pd.notna(row[col]) and int(row[col]) > 0:
            has_pedestrians = True
            break
    
    if has_pedestrians:
        complexity += 0.5
    
    return complexity

def derive_complexity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the complexity calculation to each row of the dataframe.
    """
    # Ensure we don't modify the original dataframe
    df_derived = df.copy()
    
    # Apply the complexity calculation
    df_derived['dilemma_complexity'] = df_derived.apply(calculate_complexity_score, axis=1)
    
    return df_derived

def main() -> None:
    args = parse_args()
    
    # Setup logging
    logger = setup_logging(log_dir=args.log_dir)
    quality_logger = get_data_quality_logger()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    ensure_directories(output_path)
    
    logger.info(f"Loading input data from {input_path}")
    quality_logger.info(f"Starting dilemma complexity derivation for {input_path}")
    
    try:
        # Load the dataset (supports both parquet and csv)
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv':
            df = pd.read_csv(input_path)
        else:
            # Try to guess based on content or default to parquet
            try:
                df = pd.read_parquet(input_path)
            except Exception:
                df = pd.read_csv(input_path)
        
        logger.info(f"Loaded {len(df)} records")
        
        # Derive complexity
        df_complexity = derive_complexity(df)
        
        # Select only the necessary columns for the output
        # We need participant_id to link back, and the new complexity score
        # Also keep dilemma_id if available for reference
        output_columns = ['participant_id', 'dilemma_id', 'dilemma_complexity']
        # Filter to only existing columns
        existing_output_columns = [col for col in output_columns if col in df_complexity.columns]
        
        df_output = df_complexity[existing_output_columns]
        
        # Save to CSV
        df_output.to_csv(output_path, index=False)
        
        logger.info(f"Saved derived complexity scores to {output_path}")
        quality_logger.info(f"Dilemma complexity derivation completed successfully. Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Error during complexity derivation: {e}", exc_info=True)
        quality_logger.error(f"Dilemma complexity derivation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
