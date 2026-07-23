"""
Data Cleaning Pipeline for Usability Study.

This module orchestrates the cleaning of raw session data:
1. Loads raw JSON sessions.
2. Filters out incomplete sessions (status='incomplete').
3. Imputes missing SUS scores (if <= 1 item missing).
4. Validates dropout reasons for excluded sessions.
5. Outputs a cleaned CSV and records a SHA-256 checksum.
"""

import argparse
import json
import os
import sys
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger

logger = get_logger(__name__)


def load_raw_sessions(input_dir: str) -> List[Dict[str, Any]]:
    """
    Load all JSON session files from the input directory.
    """
    sessions = []
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    json_files = list(input_path.glob("*.json"))
    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return sessions

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure it's a dict, sometimes loaded as list of dicts
                if isinstance(data, dict):
                    sessions.append(data)
                elif isinstance(data, list):
                    sessions.extend(data)
            logger.debug(f"Loaded session from {file_path.name}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Error reading {file_path.name}: {e}")

    return sessions


def filter_incomplete(sessions: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter sessions into complete and incomplete lists based on 'status' field.
    Returns (complete_sessions, incomplete_sessions).
    """
    complete = []
    incomplete = []

    for session in sessions:
        status = session.get('status', 'unknown')
        if status == 'incomplete':
            # Verify dropout_reason exists for incomplete sessions
            reason = session.get('dropout_reason')
            if not reason:
                logger.warning(f"Session {session.get('participant_id')} is incomplete but missing dropout_reason.")
            incomplete.append(session)
        else:
            complete.append(session)

    logger.info(f"Filtered sessions: {len(complete)} complete, {len(incomplete)} incomplete.")
    return complete, incomplete


def impute_sus(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Impute SUS scores for sessions with <= 1 missing item.
    Logic:
    - SUS items are typically keys like 'sus_q1' ... 'sus_q10' or similar.
    - Based on the schema in T019b, the raw data might store the raw answers or the calculated score.
    - If the raw answers exist, we calculate the score.
    - If the score exists but is missing/NaN, we impute based on participant mean if possible.
    - For this implementation, we assume the session contains 'sus_score' (calculated) or raw items.
    - We will look for a 'sus_responses' list or individual 'sus_q*' keys.
    
    Simplified Strategy for this task:
    If 'sus_score' is missing or None:
      1. Check if we have raw responses (e.g., 'sus_q1' to 'sus_q10').
      2. If we have >= 9 responses, calculate the score.
      3. If we have < 9 responses, mark as incomplete (should have been filtered, but safety check).
    
    If 'sus_score' exists but is invalid (e.g., negative), we might impute from participant mean if multiple sessions exist.
    For this specific task (T021b), we focus on the case where the score is missing but data allows calculation.
    """
    imputed_count = 0
    
    for session in sessions:
        sus_score = session.get('sus_score')
        
        # If score is present and valid, skip
        if sus_score is not None and isinstance(sus_score, (int, float)) and 0 <= sus_score <= 100:
            continue

        # Attempt to calculate from raw responses if available
        # Assuming keys like 'sus_q1' ... 'sus_q10' exist in the session dict
        q_keys = [f'sus_q{i}' for i in range(1, 11)]
        responses = []
        for key in q_keys:
            if key in session:
                val = session[key]
                if val is not None:
                    responses.append(val)
        
        if len(responses) >= 9:
            # Calculate SUS score
            # Standard SUS formula: 
            # (Sum of (Odd items - 1) + Sum of (5 - Even items)) * 2.5
            # Assuming 1-5 scale
            sum_odd = 0
            sum_even = 0
            for i, val in enumerate(responses):
                # i=0 is q1 (odd), i=1 is q2 (even)
                if i % 2 == 0: # Odd item (1, 3, 5...)
                    sum_odd += (val - 1)
                else: # Even item (2, 4, 6...)
                    sum_even += (5 - val)
            
            calculated_score = (sum_odd + sum_even) * 2.5
            session['sus_score'] = calculated_score
            session['sus_imputed'] = True
            logger.debug(f"Calculated SUS score {calculated_score} for session {session.get('participant_id')} from {len(responses)} responses.")
            imputed_count += 1
        elif len(responses) > 0 and len(responses) < 9:
            # Partial data, cannot impute reliably without participant mean across sessions
            # We leave it as None/NaN, which will be handled by downstream exclusion if strict
            logger.warning(f"Session {session.get('participant_id')} has {len(responses)} SUS responses, cannot calculate score.")
        else:
            # No responses found
            pass

    logger.info(f"Imputed SUS scores for {imputed_count} sessions.")
    return sessions


def compute_checksum(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Clean raw session data.")
    parser.add_argument("--input", type=str, required=True, help="Path to directory containing raw JSON sessions.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file.")
    parser.add_argument("--checksum-file", type=str, default="data/processed/checksums.json", help="Path to store checksum record.")
    
    args = parser.parse_args()
    
    logger.info(f"Starting data cleaning pipeline.")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    # 1. Load
    try:
        sessions = load_raw_sessions(args.input)
        if not sessions:
            logger.error("No valid sessions found. Exiting.")
            sys.exit(1)
        logger.info(f"Loaded {len(sessions)} sessions.")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # 2. Filter
    complete_sessions, incomplete_sessions = filter_incomplete(sessions)

    # 3. Impute
    cleaned_sessions = impute_sus(complete_sessions)

    # 4. Convert to DataFrame and Write
    if not cleaned_sessions:
        logger.warning("No complete sessions remained after filtering. Creating empty CSV.")
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(cleaned_sessions)
        # Ensure standard columns exist
        required_cols = ['participant_id', 'interface_type', 'completion_time_seconds', 'error_count', 'sus_score', 'explanation_engagement_time_seconds', 'status']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None

    # Create output directory if needed
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Wrote cleaned data to {args.output}")

    # 5. Compute Checksum and Record
    checksum = compute_checksum(str(output_path))
    checksum_record = {
        "file": str(output_path),
        "sha256": checksum,
        "rows": len(df),
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    checksum_path = Path(args.checksum_file)
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums if any
    all_checksums = []
    if checksum_path.exists():
        try:
            with open(checksum_path, 'r') as f:
                all_checksums = json.load(f)
        except json.JSONDecodeError:
            all_checksums = []
    
    # Append new record
    all_checksums.append(checksum_record)
    
    with open(checksum_path, 'w') as f:
        json.dump(all_checksums, f, indent=2)
    
    logger.info(f"Checksum recorded: {checksum}")
    logger.info("Data cleaning pipeline completed successfully.")


if __name__ == "__main__":
    main()