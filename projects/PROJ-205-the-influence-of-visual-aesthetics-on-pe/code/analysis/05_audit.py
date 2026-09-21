"""
Audit script for post-hoc duplicate detection.

This script reads the raw submissions CSV, identifies rows where the
hashed_ip appears more than once, and writes a dedicated audit log
to data/raw/duplicate_audit.csv.

It uses the helper functions from code/utils/helpers.py to ensure
consistent hashing and path resolution.
"""

import os
import sys
import csv
from pathlib import Path
from datetime import datetime

# Add the project root to the path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.helpers import get_submissions_csv_path, get_project_root


def load_submissions_data(csv_path: str) -> list[dict]:
    """
    Load the raw submissions data from the CSV file.

    Args:
        csv_path: Path to the submissions CSV file.

    Returns:
        A list of dictionaries, where each dictionary represents a row.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Submissions file not found: {csv_path}")

    data = []
    with open(csv_path, mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def detect_duplicates(data: list[dict]) -> list[dict]:
    """
    Detect rows with duplicate hashed_ip values.

    Args:
        data: List of submission dictionaries.

    Returns:
        A list of dictionaries representing rows that have a duplicate hashed_ip.
    """
    ip_counts = {}
    duplicate_rows = []

    # First pass: count occurrences of each hashed_ip
    for row in data:
        ip = row.get('hashed_ip', '')
        if ip:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

    # Second pass: collect rows where the ip count > 1
    for row in data:
        ip = row.get('hashed_ip', '')
        if ip and ip_counts[ip] > 1:
            duplicate_rows.append(row)

    return duplicate_rows


def write_audit_log(duplicate_rows: list[dict], output_path: str) -> None:
    """
    Write the duplicate rows to the audit log CSV file.

    Args:
        duplicate_rows: List of dictionaries representing duplicate rows.
        output_path: Path to the output audit log CSV file.
    """
    if not duplicate_rows:
        print("No duplicates found. Audit log will be empty (header only).")

    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fieldnames = [
        'participant_id', 'stimulus_id', 'credibility', 'professionalism',
        'timestamp', 'hashed_ip', 'age', 'education', 'duplicate_flag',
        'session_status', 'submission_status'
    ]

    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in duplicate_rows:
            # Ensure all fields are present, defaulting to empty string if missing
            clean_row = {k: row.get(k, '') for k in fieldnames}
            # Mark the duplicate flag explicitly
            clean_row['duplicate_flag'] = 'TRUE'
            writer.writerow(clean_row)


def main():
    """Main entry point for the duplicate audit script."""
    print("Starting duplicate detection audit...")

    # Resolve paths
    submissions_csv = get_submissions_csv_path()
    audit_csv = str(Path(submissions_csv).parent / "duplicate_audit.csv")

    print(f"Reading submissions from: {submissions_csv}")
    print(f"Audit log will be written to: {audit_csv}")

    try:
        data = load_submissions_data(submissions_csv)
        print(f"Loaded {len(data)} rows from submissions.")

        duplicates = detect_duplicates(data)
        print(f"Found {len(duplicates)} rows with duplicate hashed_ip values.")

        write_audit_log(duplicates, audit_csv)
        print(f"Audit log written to: {audit_csv}")

        if duplicates:
            unique_duplicate_ips = set(row['hashed_ip'] for row in duplicates)
            print(f"Total unique IPs with duplicates: {len(unique_duplicate_ips)}")
            for ip in sorted(unique_duplicate_ips):
                count = sum(1 for r in duplicates if r['hashed_ip'] == ip)
                print(f"  - {ip}: {count} occurrences")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure that data/raw/submissions.csv exists. Run the survey or generate mock data first.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

    print("Audit complete.")


if __name__ == "__main__":
    main()
