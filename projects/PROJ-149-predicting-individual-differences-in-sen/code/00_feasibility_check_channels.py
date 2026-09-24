"""
T008d: Feasibility Check - Channel Rejection Ratio
----------------------------------------------------
Performs the channel rejection check *after* preprocessing.

Inputs:
  - data/interim/feasibility_filtered.csv (from T008b)
  - data/interim/exclusion_log.csv (from T010, contains channels_rejected_ratio)

Logic:
  1. Load the filtered participant list.
  2. Load the preprocessing exclusion log.
  3. Filter out participants where channels_rejected_ratio > 0.30.
  4. Write the final participant list and update the exclusion log.
  5. Halt with exit code 1 if no participants remain.
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime

# Import shared config utilities
# Note: Using the existing config.py API surface as defined in the project
from config import get_path, ensure_dirs

def load_filtered_participants():
    """Load the participant list from T008b."""
    input_path = get_path("interim", "feasibility_filtered.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    participants = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            participants.append(row)
    return participants

def load_preprocessing_exclusion_log():
    """Load the exclusion log from T010 (preprocessing)."""
    input_path = get_path("interim", "exclusion_log.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Preprocessing exclusion log not found: {input_path}")
    
    log_data = {}
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Assuming 'participant_id' is the key column
            pid = row.get('participant_id')
            if pid:
                log_data[pid] = row
    return log_data

def check_channel_rejection(participants, exclusion_log):
    """
    Filter participants based on channel rejection ratio > 0.30.
    Returns (kept_participants, excluded_entries).
    """
    kept = []
    excluded = []
    threshold = 0.30
    
    for p in participants:
        pid = p.get('participant_id')
        if not pid:
            # If no ID, skip or handle as error
            continue
        
        if pid not in exclusion_log:
            # Participant not in exclusion log? 
            # Depending on strictness, we might exclude or keep.
            # Per safety, if we can't verify ratio, we exclude.
            excluded.append({
                'participant_id': pid,
                'reason': 'high_channel_rejection',
                'channels_rejected_ratio': 'N/A (missing log)'
            })
            continue
        
        ratio_str = exclusion_log[pid].get('channels_rejected_ratio', '0')
        try:
            ratio = float(ratio_str)
        except ValueError:
            ratio = 1.0  # Treat invalid as failure
        
        if ratio > threshold:
            excluded.append({
                'participant_id': pid,
                'reason': 'high_channel_rejection',
                'channels_rejected_ratio': ratio
            })
        else:
            kept.append(p)
    
    return kept, excluded

def write_final_participant_list(participants):
    """Write the final list to data/interim/final_participant_list.csv."""
    output_path = get_path("interim", "final_participant_list.csv")
    ensure_dirs(output_path)
    
    if not participants:
        # Write empty file with header to be safe
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id'])
            writer.writeheader()
        return
    
    fieldnames = list(participants[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(participants)

def update_exclusion_log(existing_excluded, new_excluded):
    """Append new exclusions to the existing log."""
    output_path = get_path("interim", "final_exclusion_log.csv")
    ensure_dirs(output_path)
    
    all_excluded = existing_excluded + new_excluded
    
    if not all_excluded:
        # Write empty file with header
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['participant_id', 'reason', 'channels_rejected_ratio'])
            writer.writeheader()
        return
    
    fieldnames = ['participant_id', 'reason', 'channels_rejected_ratio']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_excluded)

def write_failure_report(reason):
    """Write a failure report if no participants remain."""
    output_path = get_path("processed", "feasibility_report.md")
    ensure_dirs(output_path)
    
    timestamp = datetime.now().isoformat()
    report_content = f"""
# Feasibility Report - Channel Rejection Check
**Status**: FAILED
**Reason**: {reason}
**Timestamp**: {timestamp}

No participants remained after applying the channel rejection filter.
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content.strip())

def main():
    print("Starting T008d: Feasibility Check - Channel Rejection")
    
    try:
        # 1. Load inputs
        print("Loading filtered participants...")
        participants = load_filtered_participants()
        print(f"  Found {len(participants)} participants.")
        
        print("Loading preprocessing exclusion log...")
        exclusion_log = load_preprocessing_exclusion_log()
        print(f"  Found {len(exclusion_log)} entries in exclusion log.")
        
        # 2. Check channel rejection
        print("Checking channel rejection ratios...")
        kept, new_excluded = check_channel_rejection(participants, exclusion_log)
        print(f"  Kept: {len(kept)}, Excluded: {len(new_excluded)}")
        
        # 3. Load existing exclusion log (from T008a/b) to append
        # We need to read the existing log to preserve previous reasons
        existing_log_path = get_path("interim", "feasibility_exclusion_log.csv")
        existing_excluded = []
        if os.path.exists(existing_log_path):
            with open(existing_log_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_excluded.append(row)
        
        # 4. Write outputs
        print("Writing final participant list...")
        write_final_participant_list(kept)
        
        print("Updating exclusion log...")
        update_exclusion_log(existing_excluded, new_excluded)
        
        # 5. Halt condition
        if len(kept) == 0:
            print("ERROR: No participants remain after channel rejection check.")
            write_failure_report("All participants excluded due to high channel rejection ratio (> 0.30).")
            sys.exit(1)
        
        print("T008d completed successfully.")
        print(f"Final participant count: {len(kept)}")
        
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
