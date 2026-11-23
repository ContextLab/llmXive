"""
Orchestrate the data cleaning pipeline.

This script implements the cleaning pipeline for the usability study.
It sequentially calls:
1. filter_incomplete() - Removes sessions with status='incomplete'
2. impute_sus() - Handles missing SUS questionnaire items

Constraint: The output file MUST be checksummed and the checksum recorded.
"""
import argparse
import json
import os
import sys
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.data_cleaner import DataCleaner
from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_sessions(input_path: str) -> pd.DataFrame:
    """
    Load raw session data from a JSON file or directory of JSON files.
    
    Args:
        input_path: Path to a single JSON file or directory containing JSON files
        
    Returns:
        DataFrame containing all session records
    """
    logger.info(f"Loading raw sessions from: {input_path}")
    all_sessions = []
    
    input_path = Path(input_path)
    
    if input_path.is_file():
        # Load single file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                all_sessions.extend(data)
            else:
                all_sessions.append(data)
    elif input_path.is_dir():
        # Load all JSON files in directory
        for json_file in input_path.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_sessions.extend(data)
                else:
                    all_sessions.append(data)
    else:
        raise FileNotFoundError(f"Input path does not exist: {input_path}")
    
    if not all_sessions:
        raise ValueError(f"No session data found in {input_path}")
    
    df = pd.DataFrame(all_sessions)
    logger.info(f"Loaded {len(df)} sessions")
    return df

def filter_incomplete(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out sessions where status='incomplete'.
    
    Args:
        df: DataFrame containing session data
        
    Returns:
        DataFrame with only complete sessions
    """
    logger.info("Filtering incomplete sessions...")
    initial_count = len(df)
    
    # Filter for complete sessions only
    df_complete = df[df['status'] == 'complete'].copy()
    
    # Log excluded sessions for verification
    excluded = df[df['status'] != 'complete']
    if not excluded.empty:
        logger.info(f"Excluded {len(excluded)} incomplete sessions")
        for _, row in excluded.iterrows():
            reason = row.get('dropout_reason', 'Unknown')
            logger.info(f"  - Session {row.get('participant_id')}: {reason}")
    
    logger.info(f"Retained {len(df_complete)} complete sessions")
    return df_complete

def impute_sus(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing SUS questionnaire items.
    
    Logic:
    - If <=1 item missing per participant, impute with participant mean
    - If >1 item missing, mark as incomplete (should be handled by filter_incomplete)
    
    Args:
        df: DataFrame containing session data with SUS items
        
    Returns:
        DataFrame with imputed SUS values
    """
    logger.info("Imputing missing SUS items...")
    df = df.copy()
    
    # SUS items are typically Q1, Q3, Q5, Q7, Q9 (odd items) and Q2, Q4, Q6, Q8, Q10 (even items)
    # Standard SUS scoring:
    # Odd items: score = response - 1
    # Even items: score = 5 - response
    # Total SUS = sum of scores * 2.5
    
    # Check for SUS item columns (assuming standard naming: sus_q1, sus_q2, ..., sus_q10)
    sus_cols = [f'sus_q{i}' for i in range(1, 11)]
    available_cols = [col for col in sus_cols if col in df.columns]
    
    if not available_cols:
        logger.warning("No SUS item columns found. Assuming pre-calculated sus_score exists.")
        # If sus_score exists, we're done
        if 'sus_score' not in df.columns:
            logger.error("No SUS data found at all. Cannot proceed.")
            raise ValueError("No SUS data found in input")
        return df
    
    # Group by participant_id to calculate means
    grouped = df.groupby('participant_id')
    
    for participant_id, group in grouped:
        missing_counts = group[available_cols].isnull().sum(axis=1)
        
        for idx in group.index:
            missing_count = missing_counts.loc[idx]
            
            if missing_count == 0:
                continue  # No missing items
            elif missing_count == 1:
                # Impute with participant mean
                participant_data = df.loc[df['participant_id'] == participant_id]
                valid_values = participant_data[available_cols].dropna()
                if not valid_values.empty:
                    mean_val = valid_values.mean()
                    # Find the missing column and impute
                    for col in available_cols:
                        if pd.isna(df.loc[idx, col]):
                            df.loc[idx, col] = mean_val
                            logger.debug(f"Imputed {col} for participant {participant_id} with mean {mean_val:.2f}")
            elif missing_count > 1:
                # Mark as incomplete (should be filtered out)
                logger.warning(f"Participant {participant_id} has {missing_count} missing SUS items. Marking as incomplete.")
                df.loc[idx, 'status'] = 'incomplete'
    
    # Filter out any newly marked incomplete sessions
    df = df[df['status'] == 'complete']
    
    # Recalculate sus_score if we imputed values
    if len(available_cols) == 10:
        # Standard SUS calculation
        sus_scores = []
        for idx, row in df.iterrows():
            scores = []
            for i in range(1, 11):
                col = f'sus_q{i}'
                if i % 2 == 1:  # Odd
                    scores.append(row[col] - 1)
                else:  # Even
                    scores.append(5 - row[col])
            sus_scores.append(sum(scores) * 2.5)
        df['sus_score'] = sus_scores
    
    logger.info(f"Imputation complete. Final count: {len(df)} sessions")
    return df

def compute_checksum(df: pd.DataFrame, output_path: str) -> str:
    """
    Compute SHA-256 checksum of the output file.
    
    Args:
        df: DataFrame to be saved
        output_path: Path where the file will be saved
        
    Returns:
        Hex digest of the checksum
    """
    # Save to CSV first
    df.to_csv(output_path, index=False)
    
    # Compute checksum
    sha256_hash = hashlib.sha256()
    with open(output_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    logger.info(f"Checksum computed: {checksum}")
    return checksum

def main():
    """
    Main entry point for the cleaning pipeline.
    
    Usage:
        python -m code.analysis.clean_data --input data/raw/*.json --output data/processed/cleaned_sessions.csv
    """
    parser = argparse.ArgumentParser(description="Clean session data for analysis")
    parser.add_argument("--input", required=True, help="Input path (JSON file or directory)")
    parser.add_argument("--output", required=True, help="Output path (CSV file)")
    parser.add_argument("--state-file", default="data/processed/state.json", help="Path to state file for checksum recording")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Load raw data
        df = load_raw_sessions(args.input)
        
        # Step 2: Filter incomplete sessions
        df = filter_incomplete(df)
        
        # Step 3: Impute SUS items
        df = impute_sus(df)
        
        # Step 4: Compute checksum and save
        checksum = compute_checksum(df, str(args.output))
        
        # Step 5: Record checksum in state file
        state_path = Path(args.state_file)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {}
        if state_path.exists():
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        
        state['cleaned_sessions'] = {
            'file': str(args.output),
            'checksum': checksum,
            'records': len(df),
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Cleaning pipeline complete. Output: {args.output}")
        logger.info(f"Records: {len(df)}, Checksum: {checksum}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()