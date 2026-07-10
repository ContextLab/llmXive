"""
Merge baseline and post-intervention records for analysis.

This module joins participant data from baseline (T017/T019) and post-intervention
sources into a single wide-format dataset suitable for change score calculation
(T035) and statistical analysis (T036+).

Input files:
  - data/processed/baseline_scores.csv (or similar aggregated baseline file)
  - data/processed/post_scores.csv (or similar aggregated post file)
  - data/processed/compliance_summary.csv (optional, from T027)

Output file:
  - data/processed/merged_analysis_data.csv
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Import config for path resolution
from config.env_config import get_path, get_param

# Import scoring utilities if needed for validation
from scoring.sart import score_sart_session
from scoring.ospan import score_ospan_session
from scoring.questionnaires import score_pss10_session, score_panas_session

# Import random seed for reproducibility if needed
from utils.random_seed import get_seed

def load_csv_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        List of row dictionaries.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    data = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to float/int where appropriate
            cleaned_row = {}
            for k, v in row.items():
                if v == '' or v is None:
                    cleaned_row[k] = None
                else:
                    try:
                        # Try int first
                        cleaned_row[k] = int(v)
                    except ValueError:
                        try:
                            # Try float
                            cleaned_row[k] = float(v)
                        except ValueError:
                            # Keep as string
                            cleaned_row[k] = v
            data.append(cleaned_row)
    
    if not data:
        raise ValueError(f"Input file {file_path} is empty or has no data rows.")
        
    return data

def merge_baseline_post(baseline_data: List[Dict], post_data: List[Dict]) -> List[Dict]:
    """
    Merge baseline and post-intervention data by participant_id.
    
    This function performs an inner join on 'participant_id'.
    It renames columns to indicate the timepoint (e.g., 'sart_errors_baseline', 'sart_errors_post').
    
    Args:
        baseline_data: List of dicts from baseline file.
        post_data: List of dicts from post-intervention file.
        
    Returns:
        List of merged dicts.
    """
    # Index baseline by participant_id
    baseline_map = {row['participant_id']: row for row in baseline_data}
    
    merged_rows = []
    for post_row in post_data:
        pid = post_row.get('participant_id')
        if not pid:
            continue
            
        base_row = baseline_map.get(pid)
        
        if base_row:
            # Inner join: both exist
            merged = {'participant_id': pid}
            
            # Add baseline columns
            for k, v in base_row.items():
                if k == 'participant_id':
                    continue
                merged[f"{k}_baseline"] = v
                
            # Add post columns
            for k, v in post_row.items():
                if k == 'participant_id':
                    continue
                merged[f"{k}_post"] = v
                
            merged['timepoint'] = 'both'
            merged['merged_at'] = datetime.now().isoformat()
            merged_rows.append(merged)
        else:
            # Missing baseline, but we have post. 
            # Depending on strictness, we might drop or flag.
            # For this pipeline, we keep them but mark baseline as missing.
            merged = {'participant_id': pid}
            for k, v in post_row.items():
                if k == 'participant_id':
                    continue
                merged[f"{k}_post"] = v
            # Add Nones for baseline
            baseline_keys = [k for k in base_row.keys() if k != 'participant_id']
            for k in baseline_keys:
                merged[f"{k}_baseline"] = None
                
            merged['timepoint'] = 'post_only'
            merged['merged_at'] = datetime.now().isoformat()
            merged_rows.append(merged)
            
    return merged_rows

def merge_compliance(merged_data: List[Dict], compliance_data: List[Dict]) -> List[Dict]:
    """
    Merge compliance summary data into the merged dataset.
    
    Args:
        merged_data: The result from merge_baseline_post.
        compliance_data: List of dicts from compliance summary.
        
    Returns:
        Updated list of merged dicts.
    """
    compliance_map = {row['participant_id']: row for row in compliance_data}
    
    result = []
    for row in merged_data:
        pid = row['participant_id']
        comp_row = compliance_map.get(pid)
        
        if comp_row:
            # Add compliance metrics
            for k, v in comp_row.items():
                if k == 'participant_id':
                    continue
                row[f"compliance_{k}"] = v
        else:
            # No compliance data found for this participant
            row['compliance_status'] = 'missing'
            
        result.append(row)
        
    return result

def write_merged_data(data: List[Dict], output_path: Path) -> None:
    """
    Write the merged data to a CSV file.
    
    Args:
        data: List of merged dictionaries.
        output_path: Path to the output CSV file.
    """
    if not data:
        raise ValueError("No data to write.")
        
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Determine all unique keys across all rows
    all_keys = set()
    for row in data:
        all_keys.update(row.keys())
        
    # Define a standard column order
    standard_order = [
        'participant_id', 
        'timepoint', 
        'merged_at',
        'sart_errors_baseline', 'sart_errors_post',
        'sart_mean_rt_baseline', 'sart_mean_rt_post',
        'ospan_score_baseline', 'ospan_score_post',
        'pss10_score_baseline', 'pss10_score_post',
        'panas_positive_baseline', 'panas_positive_post',
        'panas_negative_baseline', 'panas_negative_post',
        'compliance_rate', 'compliance_days', 'compliance_total_days'
    ]
    
    # Sort keys to ensure deterministic output, but put standard ones first
    sorted_keys = [k for k in standard_order if k in all_keys]
    sorted_keys.extend(sorted([k for k in all_keys if k not in standard_order]))
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted_keys)
        writer.writeheader()
        for row in data:
            # Ensure all keys are present (fill missing with empty string or None)
            clean_row = {k: row.get(k, '') for k in sorted_keys}
            writer.writerow(clean_row)

def run_merge_pipeline() -> Tuple[int, str]:
    """
    Execute the full merge pipeline.
    
    Returns:
        Tuple of (number of records merged, output file path as string).
    """
    # Get paths from config
    baseline_path = get_path('data_processed', 'baseline_scores.csv')
    post_path = get_path('data_processed', 'post_scores.csv')
    compliance_path = get_path('data_processed', 'compliance_summary.csv')
    output_path = get_path('data_processed', 'merged_analysis_data.csv')
    
    print(f"Loading baseline data from: {baseline_path}")
    try:
        baseline_data = load_csv_data(baseline_path)
    except FileNotFoundError:
        print(f"Warning: Baseline file not found at {baseline_path}. Skipping baseline merge.")
        baseline_data = []
        
    print(f"Loading post-intervention data from: {post_path}")
    try:
        post_data = load_csv_data(post_path)
    except FileNotFoundError:
        print(f"Error: Post-intervention file not found at {post_path}. Cannot proceed without post data.")
        raise
      
    print(f"Merging baseline and post data...")
    merged_data = merge_baseline_post(baseline_data, post_data)
    print(f"Merged {len(merged_data)} participant records.")
    
    if compliance_path.exists():
        print(f"Loading compliance data from: {compliance_path}")
        compliance_data = load_csv_data(compliance_path)
        print(f"Merging compliance data...")
        merged_data = merge_compliance(merged_data, compliance_data)
    else:
        print(f"Warning: Compliance file not found at {compliance_path}. Skipping compliance merge.")
        
    print(f"Writing merged data to: {output_path}")
    write_merged_data(merged_data, output_path)
    
    return len(merged_data), str(output_path)

def main():
    """Main entry point for the merge script."""
    try:
        count, path = run_merge_pipeline()
        print(f"SUCCESS: Merged {count} records to {path}")
    except Exception as e:
        print(f"ERROR: Pipeline failed with: {e}")
        raise

if __name__ == "__main__":
    main()