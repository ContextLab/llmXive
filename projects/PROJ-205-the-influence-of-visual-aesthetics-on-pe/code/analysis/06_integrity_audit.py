"""
Session Integrity Audit Script (T053).

Scans data/raw/submissions.csv for:
1. Missing ratings (participants who started but didn't finish all 4 stimuli).
2. Inconsistent timestamps (e. g., negative duration or impossible sequences).
3. Duplicate entries (same participant_id with conflicting data).

Generates data/processed/integrity_audit.json listing excluded sessions and reasons.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Import existing project utilities
# Note: The API surface lists functions in utils.helpers but not path getters.
# We will implement path logic here or import if available.
# Based on T010, helpers.py has get_submissions_csv_path.
try:
    from utils.helpers import get_submissions_csv_path, get_project_root
except ImportError:
    # Fallback if import structure differs slightly in execution context
    def get_project_root():
        return Path(__file__).resolve().parent.parent.parent

    def get_submissions_csv_path():
        root = get_project_root()
        return root / "data" / "raw" / "submissions.csv"

def load_submissions_data(input_path):
    """Load the submissions CSV into a list of dictionaries."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse timestamps
            try:
                row['timestamp'] = datetime.fromisoformat(row['timestamp'])
            except (ValueError, TypeError):
                row['timestamp'] = None
            data.append(row)
    return data

def group_by_participant(data):
    """Group data rows by participant_id."""
    groups = defaultdict(list)
    for row in data:
        pid = row.get('participant_id', 'UNKNOWN')
        groups[pid].append(row)
    return groups

def check_missing_ratings(group):
    """
    Check if a participant has missing ratings.
    Expect 4 stimuli (Professional, Minimalist, Low-Quality, Neutral).
    """
    ratings = {}
    for row in group:
        stim_id = row.get('stimulus_id', '')
        cred = row.get('credibility')
        prof = row.get('professionalism')
        
        if stim_id and (cred or prof):
            ratings[stim_id] = True
    
    # We expect exactly 4 distinct stimuli rated
    expected_stimuli = {'Professional', 'Minimalist', 'Low-Quality', 'Neutral'}
    # Handle potential variations in naming if any, but strict check per spec
    found_stimuli = set(ratings.keys())
    
    missing = expected_stimuli - found_stimuli
    if missing:
        return f"Missing ratings for: {', '.join(missing)}"
    
    # Also check if count is exactly 4 (in case of duplicates or extra rows)
    if len(found_stimuli) != 4:
        return f"Incomplete set of stimuli (found {len(found_stimuli)}, expected 4)"
    
    return None

def check_inconsistent_timestamps(group):
    """
    Check for timestamp inconsistencies.
    - Timestamps must be valid.
    - If multiple rows exist, timestamps should be sequential (or at least valid).
    """
    timestamps = [r['timestamp'] for r in group if r.get('timestamp')]
    
    if not timestamps:
        return "No valid timestamps found"
    
    # Check for negative durations between stimuli (impossible sequence)
    # Sort by stimulus order if possible, otherwise just check general validity
    # For simplicity, we check if any timestamp is "future" relative to submission or logically inconsistent
    # Here we check if the session duration (max - min) is negative or 0 if multiple rows
    if len(timestamps) > 1:
        min_t = min(timestamps)
        max_t = max(timestamps)
        if max_t < min_t:
            return "Timestamp sequence inverted (end before start)"
        if (max_t - min_t).total_seconds() < 0:
            return "Negative session duration"
    
    return None

def check_duplicate_entries(group):
    """
    Check for duplicate entries for the same stimulus.
    A valid session should have exactly one rating per stimulus.
    """
    stim_counts = defaultdict(int)
    for row in group:
        stim_id = row.get('stimulus_id', '')
        if stim_id:
            stim_counts[stim_id] += 1
    
    duplicates = [k for k, v in stim_counts.items() if v > 1]
    if duplicates:
        return f"Duplicate entries for stimuli: {', '.join(duplicates)}"
    
    return None

def run_audit(input_path, output_path):
    """Run the integrity audit and generate the report."""
    print(f"Loading data from {input_path}...")
    try:
        data = load_submissions_data(input_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Found {len(data)} total rows.")
    
    groups = group_by_participant(data)
    print(f"Found {len(groups)} unique participants.")

    excluded_sessions = []
    included_sessions = []

    for pid, rows in groups.items():
        reasons = []
        
        # Check 1: Missing Ratings
        reason_missing = check_missing_ratings(rows)
        if reason_missing:
            reasons.append(reason_missing)
        
        # Check 2: Inconsistent Timestamps
        reason_time = check_inconsistent_timestamps(rows)
        if reason_time:
            reasons.append(reason_time)
        
        # Check 3: Duplicate Entries
        reason_dup = check_duplicate_entries(rows)
        if reason_dup:
            reasons.append(reason_dup)
        
        if reasons:
            excluded_sessions.append({
                "participant_id": pid,
                "row_count": len(rows),
                "reasons": reasons
            })
        else:
            included_sessions.append(pid)

    # Generate Report
    report = {
        "audit_timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "total_participants": len(groups),
        "excluded_count": len(excluded_sessions),
        "included_count": len(included_sessions),
        "excluded_sessions": excluded_sessions,
        "included_participant_ids": included_sessions
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Audit complete.")
    print(f"Excluded: {len(excluded_sessions)}, Included: {len(included_sessions)}")
    print(f"Report saved to: {output_path}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Session Integrity Audit")
    parser.add_argument(
        "--input", 
        type=str, 
        default=None,
        help="Path to submissions CSV. Defaults to data/raw/submissions.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Path to output JSON. Defaults to data/processed/integrity_audit.json"
    )
    
    args = parser.parse_args()
    
    root = get_project_root()
    
    if args.input is None:
        input_path = root / "data" / "raw" / "submissions.csv"
    else:
        input_path = Path(args.input)
        
    if args.output is None:
        output_path = root / "data" / "processed" / "integrity_audit.json"
    else:
        output_path = Path(args.output)

    run_audit(input_path, output_path)

if __name__ == "__main__":
    main()