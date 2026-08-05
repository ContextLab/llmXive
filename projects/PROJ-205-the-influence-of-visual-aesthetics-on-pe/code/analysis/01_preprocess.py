import os
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import random
import numpy as np

# Seed pinning for reproducibility (Task T031)
# Ensure preprocessing steps involving random sampling (if any) are reproducible
_SEED = 42
random.seed(_SEED)
np.random.seed(_SEED)

def get_project_root():
    """Returns the root path of the project."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent

def load_raw_data(csv_path: str) -> List[Dict[str, Any]]:
    """
    Loads the raw submissions CSV file.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = list(reader)
    
    return data

def validate_and_filter(data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filters data based on validity criteria:
    - submission_status must be 'complete'
    - session_timeout must be False
    - rating_count must be >= 8
    
    Returns:
        Tuple of (valid_data, excluded_data)
    """
    valid_data = []
    excluded_data = []
    
    for row in data:
        is_valid = True
        
        # Check submission status
        status = row.get('submission_status', '').lower()
        if status != 'complete':
            is_valid = False
        
        # Check session timeout
        timeout = row.get('session_timeout', 'false').lower()
        if timeout == 'true':
            is_valid = False
        
        # Check rating count
        try:
            rating_count = int(row.get('rating_count', 0))
            if rating_count < 8:
                is_valid = False
        except ValueError:
            is_valid = False
        
        if is_valid:
            valid_data.append(row)
        else:
            excluded_data.append(row)
            
    return valid_data, excluded_data

def reshape_to_wide(valid_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Reshapes the long-format valid data into wide format for ANOVA.
    Each row represents a participant.
    Columns: participant_id, condition_professional_credibility, condition_minimalist_credibility, ...
    """
    # Group by participant_id
    participants = {}
    
    for row in valid_data:
        pid = row.get('participant_id')
        if not pid:
            continue
        
        if pid not in participants:
            participants[pid] = {
                'participant_id': pid,
                'age': row.get('age'),
                'education': row.get('education')
            }
        
        # Extract condition and ratings
        condition = row.get('stimulus_condition', '').lower()
        credibility = row.get('credibility_rating')
        professionalism = row.get('professionalism_rating')
        
        if condition and credibility is not None:
            # Store in wide format keys
            participants[pid][f'condition_{condition}_credibility'] = credibility
            participants[pid][f'condition_{condition}_professionalism'] = professionalism
    
    # Convert to list
    wide_data = list(participants.values())
    return wide_data

def write_outputs(valid_data: List[Dict[str, Any]], excluded_data: List[Dict[str, Any]], wide_data: List[Dict[str, Any]], output_dir: str):
    """
    Writes the filtered, excluded, and wide data to CSV files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write wide data
    wide_csv = output_path / 'wide_submissions.csv'
    if wide_data:
        fieldnames = wide_data[0].keys()
        with open(wide_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(wide_data)
    
    # Write excluded audit log
    excluded_csv = output_path / 'excluded_audit.csv'
    if excluded_data:
        fieldnames = excluded_data[0].keys() if excluded_data else []
        with open(excluded_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(excluded_data)

def main():
    """
    Main entry point for the preprocessing script.
    """
    project_root = get_project_root()
    raw_csv = project_root / 'data' / 'raw' / 'submissions.csv'
    processed_dir = project_root / 'data' / 'processed'
    
    if not raw_csv.exists():
        print(f"Error: Raw data file not found at {raw_csv}", file=sys.stderr)
        sys.exit(1)
    
    # Load
    raw_data = load_raw_data(str(raw_csv))
    print(f"Loaded {len(raw_data)} raw submissions.")
    
    # Filter
    valid_data, excluded_data = validate_and_filter(raw_data)
    print(f"Valid submissions: {len(valid_data)}, Excluded: {len(excluded_data)}")
    
    # Reshape
    wide_data = reshape_to_wide(valid_data)
    print(f"Wide data participants: {len(wide_data)}")
    
    # Write
    write_outputs(valid_data, excluded_data, wide_data, str(processed_dir))
    print(f"Preprocessing complete. Output written to {processed_dir}")

if __name__ == '__main__':
    main()
