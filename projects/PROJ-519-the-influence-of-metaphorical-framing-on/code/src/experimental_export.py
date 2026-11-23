"""
Experimental Export Module (T016).

Implements data export logic to write raw experimental results to
data/processed/experimental_results.csv with SHA-256 checksums saved to
data/processed/experimental_results.csv.sha256.

Dependencies:
- src/cami_scoring (for loading/processing scores if needed)
- src/data_ingestion (for loading assignments)
"""
import os
import csv
import hashlib
import argparse
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure project root is in path for imports if running as script
# In the actual project structure, this is handled by the runner environment
import sys
if os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) not in sys.path:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.cami_scoring import load_survey_responses, process_responses, save_scores
from src.data_ingestion import load_assignments, load_real_participant_data

def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def export_experimental_results(
    assignments_path: str,
    survey_responses_path: str,
    output_csv_path: str,
    checksum_path: Optional[str] = None
) -> str:
    """
    Merge experimental assignments with survey responses to create the final
    raw experimental results dataset.
    
    Args:
        assignments_path: Path to data/processed/experimental_assignments.csv
        survey_responses_path: Path to data/raw/survey_responses.json
        output_csv_path: Path for the output CSV (data/processed/experimental_results.csv)
        checksum_path: Path for the SHA-256 checksum file (optional, defaults to .sha256)
    
    Returns:
        The computed SHA-256 checksum of the output CSV.
    
    Raises:
        FileNotFoundError: If input files do not exist.
        ValueError: If required columns are missing in input data.
    """
    if not os.path.exists(assignments_path):
        raise FileNotFoundError(f"Assignments file not found: {assignments_path}")
    if not os.path.exists(survey_responses_path):
        raise FileNotFoundError(f"Survey responses file not found: {survey_responses_path}")

    # Load assignments
    assignments = load_assignments(assignments_path)
    if not assignments:
        raise ValueError("No assignments loaded from file.")

    # Load and process survey responses
    # load_survey_responses expects the JSON path
    raw_responses = load_survey_responses(survey_responses_path)
    
    # Process responses to get CAMI scores and help-seeking intent
    # This returns a list of dicts with scores
    processed_scores = process_responses(raw_responses)

    # Merge assignments with scores
    # We assume processed_scores has 'participant_id' to join
    # We also assume assignments has 'participant_id' and 'condition'
    
    # Create a lookup for scores by participant_id
    score_lookup = {s['participant_id']: s for s in processed_scores}

    results = []
    for assignment in assignments:
        pid = assignment.get('participant_id')
        if pid not in score_lookup:
            # Log warning or skip? For now, include with nulls or skip.
            # Let's include with nulls to maintain row count for integrity checks
            row = {
                'participant_id': pid,
                'condition': assignment.get('condition', 'UNKNOWN'),
                'vignette_text': assignment.get('vignette_text', ''),
                'cami_total': None,
                'cami_stigma': None,
                'cami_help_seeking': None,
                'help_seeking_likert': None,
                'attention_check_passed': None,
                'timestamp': assignment.get('timestamp', '')
            }
        else:
            score_data = score_lookup[pid]
            row = {
                'participant_id': pid,
                'condition': assignment.get('condition', 'UNKNOWN'),
                'vignette_text': assignment.get('vignette_text', ''),
                'cami_total': score_data.get('cami_total'),
                'cami_stigma': score_data.get('cami_stigma'),
                'cami_help_seeking': score_data.get('cami_help_seeking'),
                'help_seeking_likert': score_data.get('help_seeking_likert'),
                'attention_check_passed': score_data.get('attention_check_passed'),
                'timestamp': assignment.get('timestamp', '')
            }
        results.append(row)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_csv_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write CSV
    fieldnames = [
        'participant_id', 'condition', 'vignette_text',
        'cami_total', 'cami_stigma', 'cami_help_seeking',
        'help_seeking_likert', 'attention_check_passed', 'timestamp'
    ]

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Compute checksum
    checksum = compute_sha256(output_csv_path)

    # Write checksum file
    if checksum_path is None:
        checksum_path = f"{output_csv_path}.sha256"
    
    checksum_dir = os.path.dirname(checksum_path)
    if checksum_dir and not os.path.exists(checksum_dir):
        os.makedirs(checksum_dir)

    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {os.path.basename(output_csv_path)}\n")

    print(f"Exported {len(results)} results to {output_csv_path}")
    print(f"SHA-256 checksum: {checksum}")
    print(f"Checksum saved to {checksum_path}")

    return checksum

def main():
    parser = argparse.ArgumentParser(description="Export experimental results with checksums")
    parser.add_argument(
        "--assignments",
        type=str,
        default="data/processed/experimental_assignments.csv",
        help="Path to experimental assignments CSV"
    )
    parser.add_argument(
        "--responses",
        type=str,
        default="data/raw/survey_responses.json",
        help="Path to survey responses JSON"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/experimental_results.csv",
        help="Path for output CSV"
    )
    parser.add_argument(
        "--checksum",
        type=str,
        default=None,
        help="Path for checksum file (default: <output>.sha256)"
    )

    args = parser.parse_args()

    try:
        export_experimental_results(
            assignments_path=args.assignments,
            survey_responses_path=args.responses,
            output_csv_path=args.output,
            checksum_path=args.checksum
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
