"""
T008b: Enforce the "continuous 5-minute epoch" constraint.

This script filters the joined metadata to retain ONLY participants who have
at least ONE single continuous segment >= 5 minutes. It does NOT sum segments.
Participants with max_continuous_duration < 5 minutes are excluded.

Outputs:
  - data/interim/feasibility_filtered.csv
  - data/interim/feasibility_exclusion_log.csv (appended)

If no participants remain, it generates a failure report and exits with code 1.
"""
import os
import sys
import csv
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports if needed, though we use stdlib mostly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'code'))

from config import get_path, ensure_dirs

# Constants
MIN_DURATION_SECONDS = 5 * 60  # 5 minutes in seconds
INPUT_FILE = "interim/joined_metadata.csv"
OUTPUT_FILTERED = "interim/feasibility_filtered.csv"
OUTPUT_EXCLUSION_LOG = "interim/feasibility_exclusion_log.csv"
REPORT_PATH = "processed/feasibility_report.md"

def load_joined_metadata(input_path):
    """Load the joined metadata CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    participants = {}
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['participant_id']
            if pid not in participants:
                participants[pid] = []
            try:
                duration = float(row['segment_duration'])
                participants[pid].append(duration)
            except ValueError:
                # If duration is missing or invalid, treat as 0
                participants[pid].append(0.0)
    return participants

def filter_segments(participants_data):
    """
    Filter participants based on continuous segment duration.
    Returns:
      kept: list of (participant_id, max_duration)
      excluded: list of (participant_id, max_duration)
    """
    kept = []
    excluded = []

    for pid, durations in participants_data.items():
        max_dur = max(durations) if durations else 0.0
        if max_dur >= MIN_DURATION_SECONDS:
            kept.append((pid, max_dur))
        else:
            excluded.append((pid, max_dur))
    
    return kept, excluded

def write_filtered_csv(kept, output_path):
    """Write the filtered participant list."""
    ensure_dirs(output_path)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['participant_id', 'max_continuous_duration'])
        for pid, max_dur in sorted(kept):
            writer.writerow([pid, max_dur])

def update_exclusion_log(excluded, output_path):
    """
    Append to the exclusion log.
    If the file doesn't exist, create it with headers.
    """
    file_exists = os.path.exists(output_path)
    mode = 'a' if file_exists else 'w'
    
    with open(output_path, mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['participant_id', 'reason', 'max_continuous_duration'])
        
        for pid, max_dur in excluded:
            writer.writerow([pid, 'no_continuous_segment', max_dur])

def write_failure_report(kept_count, output_path):
    """Write a failure report if no participants remain."""
    ensure_dirs(output_path)
    report_content = f"""# Feasibility Report

**Status**: FAILED
**Reason**: No participants met the continuous 5-minute epoch constraint.
**Matched Count**: {kept_count}

The pipeline cannot proceed without valid participants.
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

def main():
    print("Starting T008b: Feasibility Filter Segments...")
    
    input_path = get_path("interim", "joined_metadata.csv")
    output_filtered = get_path("interim", "feasibility_filtered.csv")
    output_exclusion = get_path("interim", "feasibility_exclusion_log.csv")
    report_path = get_path("processed", "feasibility_report.md")

    try:
        # Load data
        print(f"Loading joined metadata from {input_path}...")
        participants = load_joined_metadata(input_path)
        print(f"Found {len(participants)} unique participants.")

        if len(participants) == 0:
            print("ERROR: No participants found in joined metadata.")
            write_failure_report(0, report_path)
            sys.exit(1)

        # Filter
        print("Filtering segments (min 5 min continuous)...")
        kept, excluded = filter_segments(participants)
        print(f"Kept: {len(kept)}, Excluded: {len(excluded)}")

        # Write outputs
        print(f"Writing filtered list to {output_filtered}...")
        write_filtered_csv(kept, output_filtered)

        print(f"Updating exclusion log at {output_exclusion}...")
        update_exclusion_log(excluded, output_exclusion)

        # Check halt condition
        if len(kept) == 0:
            print("CRITICAL: No participants remain after filtering.")
            write_failure_report(0, report_path)
            sys.exit(1)

        print("T008b completed successfully.")
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()