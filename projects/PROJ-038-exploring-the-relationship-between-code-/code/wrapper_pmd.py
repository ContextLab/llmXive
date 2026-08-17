"""
PMD CLI Wrapper Script for Cyclomatic Complexity Calculation.

This script integrates the PMD static analysis tool to calculate the
Cyclomatic Complexity (CC) for every Java file found in the Defects4J
dataset. It acts as the orchestration layer between the raw file list
and the PMD CLI, aggregating results into a JSON file.

Usage:
    python code/wrapper_pmd.py --input <file_list.json> --output <output.json>
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import PMD logic from the source module
try:
    from src.metrics_pmd import calculate_cc_batch, get_pmd_path
except ImportError:
    # Fallback for running as script from root if src is not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from src.metrics_pmd import calculate_cc_batch, get_pmd_path


def load_file_list(input_path: str) -> List[str]:
    """
    Load the list of Java file paths from a JSON file.

    Args:
        input_path: Path to the JSON file containing the list of file paths.

    Returns:
        A list of absolute file paths to Java files.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file list not found: {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'files' in data:
        return data['files']
    else:
        raise ValueError(f"Invalid format in {input_path}. Expected a list or a dict with 'files' key.")


def save_results(output_path: str, results: List[Dict[str, Any]]) -> None:
    """
    Save the calculation results to a JSON file.

    Args:
        output_path: Path to the output JSON file.
        results: List of dictionaries containing file paths and CC values.
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)


def main():
    """
    Main entry point for the PMD wrapper script.

    Reads a list of Java files, calculates Cyclomatic Complexity using PMD,
    and saves the results to a JSON file.
    """
    parser = argparse.ArgumentParser(
        description="Calculate Cyclomatic Complexity for Java files using PMD CLI."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to JSON file containing list of Java file paths."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output JSON file for results."
    )
    parser.add_argument(
        "--pmd-path",
        default=None,
        help="Path to PMD executable. If not provided, uses default from config."
    )

    args = parser.parse_args()

    # Validate input
    file_list = load_file_list(args.input)
    if not file_list:
        print("Warning: Input file list is empty. No processing performed.")
        save_results(args.output, [])
        return

    print(f"Loaded {len(file_list)} files from {args.input}")

    # Validate PMD availability
    pmd_path = args.pmd_path or get_pmd_path()
    if not pmd_path:
        print("ERROR: PMD executable not found. Please install PMD or set PMD_HOME.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pmd_path):
        print(f"ERROR: PMD executable not found at {pmd_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Using PMD executable: {pmd_path}")

    # Process files in batch
    print("Starting Cyclomatic Complexity calculation...")
    try:
        results = calculate_cc_batch(file_list, pmd_path)
    except Exception as e:
        print(f"ERROR: Failed to calculate metrics: {e}", file=sys.stderr)
        sys.exit(1)

    # Save results
    save_results(args.output, results)
    print(f"Results saved to {args.output}")

    # Summary stats
    total_files = len(results)
    processed_files = len([r for r in results if 'cc' in r and r['cc'] is not None])
    failed_files = total_files - processed_files

    print(f"Processed: {processed_files}/{total_files} files successfully.")
    if failed_files > 0:
        print(f"Failed to process: {failed_files} files (check logs for details).")


if __name__ == "__main__":
    main()
