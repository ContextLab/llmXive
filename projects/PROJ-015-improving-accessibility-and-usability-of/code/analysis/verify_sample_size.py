"""
Sample Size Verification Script (Task T043).

Verifies that the number of completed sessions (N) from
`data/processed/cleaned_sessions.csv` meets the minimum requirement
of 30 as per Constitution Principle VI.

If N < 30, the pipeline halts (exit code 1) and prevents the generation
of final research claims.

Output: `data/sample_size_verification.json`
"""

import argparse
import json
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, Any

# Constants
MIN_SAMPLE_SIZE = 30
INPUT_FILE = "data/processed/cleaned_sessions.csv"
OUTPUT_FILE = "data/sample_size_verification.json"

def load_cleaned_data(input_path: str) -> pd.DataFrame:
    """Load the cleaned sessions CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def verify_sample_size(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Count completed participants and verify against minimum.

    Returns a dict with:
      - total_participants: int
      - meets_minimum: bool
      - status: str ("PASS" or "FAIL")
    """
    # Count unique participants assuming 'participant_id' column exists
    # The cleaned data should only contain 'status='complete' rows per T021a
    if 'participant_id' not in df.columns:
        raise ValueError("Input CSV must contain 'participant_id' column")

    total_participants = df['participant_id'].nunique()
    meets_minimum = total_participants >= MIN_SAMPLE_SIZE

    if meets_minimum:
        status = "PASS"
    else:
        status = "FAIL"

    return {
        "total_participants": int(total_participants),
        "meets_minimum": meets_minimum,
        "status": status,
        "minimum_required": MIN_SAMPLE_SIZE
    }

def write_verification_report(result: Dict[str, Any], output_path: str) -> None:
    """Write the verification result to a JSON file."""
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify sample size meets minimum requirements."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=INPUT_FILE,
        help=f"Path to cleaned sessions CSV (default: {INPUT_FILE})"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=OUTPUT_FILE,
        help=f"Path to output verification JSON (default: {OUTPUT_FILE})"
    )

    args = parser.parse_args()

    try:
        # Load data
        print(f"Loading data from {args.input}...")
        df = load_cleaned_data(args.input)

        # Verify sample size
        print(f"Verifying sample size (N={len(df)} rows)...")
        result = verify_sample_size(df)

        # Write report
        print(f"Writing report to {args.output}...")
        write_verification_report(result, args.output)

        # Print summary
        print(f"\n--- Sample Size Verification ---")
        print(f"Total Participants: {result['total_participants']}")
        print(f"Minimum Required: {result['minimum_required']}")
        print(f"Meets Minimum: {result['meets_minimum']}")
        print(f"Status: {result['status']}")
        print(f"Report saved to: {args.output}")

        # Exit with error code if sample size is insufficient
        if not result['meets_minimum']:
            print("\nERROR: Sample size is insufficient. Pipeline halted.")
            return 1

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: Data validation failed - {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error - {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
