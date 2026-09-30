"""
Data Merger Module for Digital Decluttering Study.

This module implements the logic to join baseline and post-intervention records
with compliance scores, producing a unified dataset for analysis.

Input:
    - data/raw/baseline_raw.csv
    - data/processed/compliance_scores.csv
Output:
    - data/processed/merged_data.csv
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Project root resolution (assumes code/pipeline/ is in the project root or parent)
# We use a relative path from the script location to ensure portability
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Input/Output paths as defined in tasks.md
INPUT_BASELINE_PATH = DATA_RAW_DIR / "baseline_raw.csv"
INPUT_COMPLIANCE_PATH = DATA_PROCESSED_DIR / "compliance_scores.csv"
OUTPUT_MERGED_PATH = DATA_PROCESSED_DIR / "merged_data.csv"

def load_csv_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a CSV file into a list of dictionaries.

    Args:
        file_path: Path to the CSV file.

    Returns:
        List of dictionaries representing rows.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no headers.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Required input file not found: {file_path}")

    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV file {file_path} is empty or has no headers.")
        for row in reader:
            data.append(row)

    if not data:
        raise ValueError(f"CSV file {file_path} contains no data rows.")

    return data

def validate_compliance_scores(data: List[Dict[str, Any]]) -> None:
    """
    Validate that the compliance scores data has the expected structure.

    Args:
        data: List of compliance score records.

    Raises:
        ValueError: If required columns are missing.
    """
    required_cols = {'participant_id', 'compliance_score', 'days_compliant'}
    if not data:
        raise ValueError("Compliance scores data is empty.")

    first_row = data[0]
    missing = required_cols - set(first_row.keys())
    if missing:
        raise ValueError(f"Compliance scores data missing required columns: {missing}")

def merge_baseline_post(baseline_data: List[Dict[str, Any]], 
                        post_data: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Merge baseline and post-intervention data on participant_id.
    
    Note: This implementation assumes post-intervention data is already aggregated
    or merged into the baseline_raw.csv by previous steps (T022/T049), or that
    baseline_raw.csv contains both timepoints. If post_data is provided, it joins
    those specific records.
    
    For T031, we primarily focus on joining the baseline/post records (already
    potentially in one file or needing a simple join) with compliance scores.
    If baseline_raw.csv contains both 'baseline' and 'post' rows, we pivot or
    mark them. However, based on typical pipeline flow:
    1. baseline_raw.csv might have all raw measurements.
    2. We need to join with compliance_scores.csv.
    
    This function performs the join on 'participant_id'.
    """
    if not baseline_data:
        return []

    # Index baseline by participant_id
    # We assume multiple rows per participant in raw data (different metrics/times)
    # The merge will duplicate the compliance score for each row of that participant.
    merged = []
    
    for row in baseline_data:
        pid = row.get('participant_id')
        if not pid:
            continue
        
        new_row = dict(row)
        
        # If post_data is provided and we need to merge it specifically here:
        # (This handles cases where post data is separate)
        if post_data:
            for p_row in post_data:
                if p_row.get('participant_id') == pid:
                    new_row['post_metric_value'] = p_row.get('value')
                    new_row['post_timestamp'] = p_row.get('timestamp')
        
        merged.append(new_row)
    
    return merged

def merge_compliance(merged_data: List[Dict[str, Any]], 
                     compliance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Join compliance scores with the merged baseline/post data.

    Args:
        merged_data: List of merged participant records.
        compliance_data: List of compliance score records.

    Returns:
        List of fully merged records.
    """
    # Create a lookup for compliance by participant_id
    compliance_lookup = {}
    for comp in compliance_data:
        pid = comp.get('participant_id')
        if pid:
            compliance_lookup[pid] = comp

    final_data = []
    for row in merged_data:
        pid = row.get('participant_id')
        if pid and pid in compliance_lookup:
            # Merge compliance fields into the row
            comp_record = compliance_lookup[pid]
            for key, value in comp_record.items():
                if key != 'participant_id': # Avoid overwriting ID if redundant
                    row[f'comp_{key}'] = value
        else:
            # If no compliance data found, add nulls or flag
            row['comp_compliance_score'] = None
            row['comp_days_compliant'] = None
            row['comp_status'] = 'missing'
        
        final_data.append(row)

    return final_data

def write_merged_data(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the merged data to a CSV file.

    Args:
        data: List of dictionaries to write.
        output_path: Path to the output file.
    """
    if not data:
        raise ValueError("No data to write.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(data[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def run_merge_pipeline() -> str:
    """
    Execute the full data merge pipeline.

    1. Load baseline_raw.csv
    2. Validate and load compliance_scores.csv
    3. Merge data
    4. Write to merged_data.csv

    Returns:
        Path to the output file as a string.

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If data validation fails.
    """
    # Step 1: Load Baseline Data
    print(f"Loading baseline data from {INPUT_BASELINE_PATH}...")
    baseline_data = load_csv_data(INPUT_BASELINE_PATH)
    print(f"Loaded {len(baseline_data)} rows from baseline.")

    # Step 2: Load and Validate Compliance Scores
    print(f"Loading compliance scores from {INPUT_COMPLIANCE_PATH}...")
    compliance_data = load_csv_data(INPUT_COMPLIANCE_PATH)
    validate_compliance_scores(compliance_data)
    print(f"Loaded {len(compliance_data)} rows from compliance scores.")

    # Step 3: Merge (Baseline + Compliance)
    # Note: If post-intervention data is separate, it should be merged into baseline_data
    # before this call or handled here if a separate file is provided.
    # For this task, we assume baseline_raw.csv contains the necessary pre/post rows
    # or that the "post" data is implicitly part of the baseline_raw structure 
    # (e.g., via a 'timepoint' column). We proceed to join with compliance.
    merged = merge_baseline_post(baseline_data)
    final_data = merge_compliance(merged, compliance_data)

    # Step 4: Write Output
    print(f"Writing merged data to {OUTPUT_MERGED_PATH}...")
    write_merged_data(final_data, OUTPUT_MERGED_PATH)
    print(f"Pipeline complete. Output written to {OUTPUT_MERGED_PATH}")

    return str(OUTPUT_MERGED_PATH)

def main():
    """Entry point for the merge_data script."""
    try:
        output_path = run_merge_pipeline()
        print(f"Success: {output_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        # Fail loudly as per requirements
        raise
    except ValueError as e:
        print(f"Validation Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected Error: {e}")
        raise

if __name__ == "__main__":
    main()