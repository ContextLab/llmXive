"""
T019: Inject trace_id into data/results/network_metrics.csv.

This script generates a SHA-256 trace_id based on the source code hashes
(using the existing state.version_map utilities) and injects it as a new
column into the network_metrics.csv file.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_dirs
from state.version_map import compute_directory_hash, get_timestamp

def get_source_hash():
    """Compute SHA-256 hash of the code directory to identify the source version."""
    code_dir = project_root / "code"
    if not code_dir.exists():
        raise FileNotFoundError(f"Code directory not found: {code_dir}")
    
    # Compute hash of the entire code directory
    return compute_directory_hash(code_dir)

def generate_trace_id():
    """Generate a unique trace_id combining source hash and timestamp."""
    source_hash = get_source_hash()
    timestamp = get_timestamp()
    
    # Combine source hash and timestamp, then hash again for a clean 64-char hex string
    combined = f"{source_hash}:{timestamp}"
    trace_id = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    return trace_id

def inject_trace_id(input_path, output_path=None):
    """
    Load the network metrics CSV, add a trace_id column, and save.
    
    Args:
        input_path: Path to the existing network_metrics.csv
        output_path: Path to save the updated CSV (defaults to overwriting input)
    """
    if not output_path:
        output_path = input_path

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Load the existing data
    print(f"Loading metrics from {input_file}...")
    df = pd.read_csv(input_file)

    # Generate the trace_id
    trace_id = generate_trace_id()
    print(f"Generated trace_id: {trace_id}")

    # Inject the trace_id column
    df['trace_id'] = trace_id

    # Save the updated dataframe
    print(f"Saving updated metrics to {output_file}...")
    df.to_csv(output_file, index=False)
    
    print(f"Successfully injected trace_id into {output_file}")
    return output_file

def main():
    """Main entry point for the script."""
    # Define paths based on project structure
    results_dir = project_root / "data" / "results"
    input_file = results_dir / "network_metrics.csv"
    output_file = results_dir / "network_metrics.csv"  # Overwrite in place

    # Ensure directories exist
    ensure_dirs()

    try:
        inject_trace_id(input_file, output_file)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
