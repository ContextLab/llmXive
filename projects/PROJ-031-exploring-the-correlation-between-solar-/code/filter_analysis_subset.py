"""
Filter non-recurrent storms from the primary aligned dataset to create
a derived analysis subset for correlation analysis (US2).

This task implements T016b: creating data/processed/analysis_subset.csv
by filtering out events where is_recurrent is True, while preserving
the primary aligned_events.csv unchanged.
"""
import os
import sys
import argparse
from pathlib import Path

import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from align import main as align_main, align_events


def filter_non_recurrent_storms(
    input_path: str,
    output_path: str,
    recurrent_column: str = "is_recurrent"
) -> int:
    """
    Filter the aligned events dataset to exclude recurrent storms.

    This creates a derived subset for analysis while preserving the
    primary dataset (which must retain all events per US1 requirements).

    Args:
        input_path: Path to the primary aligned_events.csv
        output_path: Path where the filtered analysis_subset.csv will be written
        recurrent_column: Name of the column containing recurrent flags

    Returns:
        Number of rows written to the output file
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Primary aligned events file not found: {input_path}. "
            "Ensure T017 has completed and written aligned_events.csv."
        )

    # Load the primary dataset
    df = pd.read_csv(input_path)

    if recurrent_column not in df.columns:
        raise ValueError(
            f"Required column '{recurrent_column}' not found in {input_path}. "
            "Ensure T016 has completed and added the recurrent flag."
        )

    # Filter out recurrent storms (keep only non-recurrent where is_recurrent is False or NaN)
    # Per US1: primary dataset retains all events; analysis subset excludes recurrent
    non_recurrent_mask = (df[recurrent_column] == False) | (df[recurrent_column].isna())
    analysis_df = df[non_recurrent_mask].copy()

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Write the filtered subset
    analysis_df.to_csv(output_path, index=False)

    return len(analysis_df)


def main():
    """
    Entry point for the analysis subset filtering script.

    Usage:
        python code/filter_analysis_subset.py
        python code/filter_analysis_subset.py --input data/processed/aligned_events.csv --output data/processed/analysis_subset.csv
    """
    parser = argparse.ArgumentParser(
        description="Filter non-recurrent storms to create analysis subset for US2."
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/aligned_events.csv",
        help="Path to primary aligned_events.csv (default: data/processed/aligned_events.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/analysis_subset.csv",
        help="Path for filtered analysis_subset.csv (default: data/processed/analysis_subset.csv)"
    )

    args = parser.parse_args()

    print(f"Filtering analysis subset from: {args.input}")
    print(f"Output will be written to: {args.output}")

    try:
        count = filter_non_recurrent_storms(args.input, args.output)
        print(f"Successfully wrote {count} non-recurrent events to {args.output}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during filtering: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
