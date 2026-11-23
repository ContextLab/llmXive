"""
Utility script to check and report on metadata truncation status.
This script can be run to verify that the submissions.csv size is within limits
and to display the current truncation settings.
"""
import os
import sys
from pathlib import Path

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.helpers import (
    get_project_root, 
    get_current_csv_size, 
    MAX_CSV_SIZE_BYTES, 
    TARGET_SAFE_SIZE_BYTES,
    calculate_safe_truncation_length
)

def main():
    root = get_project_root()
    submissions_path = root / "data" / "raw" / "submissions.csv"
    
    print("=== Metadata Truncation Status Report ===")
    print(f"Project Root: {root}")
    print(f"Submissions Path: {submissions_path}")
    
    if not submissions_path.exists():
        print("File does not exist yet. No data to analyze.")
        return
    
    current_size = get_current_csv_size(submissions_path)
    max_size_mb = MAX_CSV_SIZE_BYTES / (1024 * 1024)
    target_size_mb = TARGET_SAFE_SIZE_BYTES / (1024 * 1024)
    
    print(f"\nCurrent File Size: {current_size / (1024 * 1024):.2f} MB")
    print(f"Target Safe Limit: {target_size_mb:.2f} MB")
    print(f"Hard Limit (SC-005): {max_size_mb:.2f} MB")
    
    if current_size > MAX_CSV_SIZE_BYTES:
        print(f"⚠️ WARNING: File size EXCEEDS {max_size_mb:.2f} MB limit!")
    elif current_size > TARGET_SAFE_SIZE_BYTES:
        print(f"⚠️ WARNING: File size exceeds target safe limit ({target_size_mb:.2f} MB).")
    else:
        print(f"✓ File size is within safe limits.")
    
    # Count rows
    row_count = 0
    with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
        next(f) # skip header
        row_count = sum(1 for _ in f)
    
    print(f"Total Rows: {row_count}")
    
    # Calculate current safe truncation length
    safe_len = calculate_safe_truncation_length(submissions_path, row_count)
    print(f"Calculated Safe User-Agent Truncation Length: {safe_len} characters")
    
    # Check actual truncation in file
    max_ua_len = 0
    with open(submissions_path, 'r', newline='', encoding='utf-8') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            ua = row.get('user_agent', '')
            if len(ua) > max_ua_len:
                max_ua_len = len(ua)
    
    print(f"Maximum User-Agent Length in File: {max_ua_len} characters")
    
    if max_ua_len > safe_len:
        print(f"⚠️ WARNING: Some user_agents exceed the calculated safe length ({safe_len}).")
    else:
        print("✓ All user_agents are within safe truncation limits.")

if __name__ == "__main__":
    main()