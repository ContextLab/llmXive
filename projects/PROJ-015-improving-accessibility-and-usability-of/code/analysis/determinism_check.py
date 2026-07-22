"""
T030: Ensure the notebook is fully deterministic.

This script:
1. Pins random seeds for Python, NumPy, and any relevant libraries.
2. Defines exact file paths for inputs and outputs to ensure reproducibility.
3. Re-runs the analysis pipeline (cleaning -> stats -> viz) using the pinned seeds.
4. Computes SHA-256 checksums for all generated figures and the metrics CSV.
5. Compares these checksums against a stored baseline (if exists) or creates a new baseline.
6. Exits with code 0 if deterministic (checksums match) or 1 if not.
"""

import os
import sys
import hashlib
import json
import random
import argparse
from pathlib import Path

# Import numpy and set seed immediately
import numpy as np

# Import project modules
# We assume the analysis pipeline functions are available via the existing API surface
# Specifically: clean_data, stat_utils, visualizer
# Since we cannot import the full pipeline directly as a single function, we will
# re-implement the critical deterministic steps here or call the main functions
# of the existing scripts in a controlled way.

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.seed import set_seed
from analysis.clean_data import main as clean_main
from analysis.stat_utils import main as stat_main
from analysis.visualizer import main as viz_main
from utils.checksum import compute_file_checksum

# Constants for paths
DATA_RAW_DIR = project_root / "data" / "raw"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
FIGURES_DIR = project_root / "figures"
BASELINE_CHECKSUMS_FILE = DATA_PROCESSED_DIR / "determinism_baseline.json"

# Output files to verify
OUTPUT_FILES = [
    DATA_PROCESSED_DIR / "cleaned_sessions.csv",
    DATA_PROCESSED_DIR / "metrics_summary.csv",
    FIGURES_DIR / "completion_time.png",
    FIGURES_DIR / "error_count.png",
    FIGURES_DIR / "sus_score.png",
]

# Fixed seed for reproducibility
FIXED_SEED = 42

def set_all_seeds(seed: int):
    """Pin random seeds for all relevant libraries."""
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    # If we were using torch, we would set torch.manual_seed(seed) here
    # But the project relies on scipy/pandas/numpy

def compute_checksums(files: list) -> dict:
    """Compute SHA-256 checksums for a list of files."""
    checksums = {}
    for f in files:
        if not f.exists():
            checksums[str(f)] = "MISSING"
        else:
            checksums[str(f)] = compute_file_checksum(f)
    return checksums

def load_baseline() -> dict:
    """Load existing baseline checksums if they exist."""
    if BASELINE_CHECKSUMS_FILE.exists():
        with open(BASELINE_CHECKSUMS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_baseline(checksums: dict):
    """Save current checksums as the new baseline."""
    BASELINE_CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_CHECKSUMS_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)

def run_pipeline():
    """
    Execute the analysis pipeline steps in order.
    This mimics the notebook execution but with explicit seed control.
    """
    # 1. Cleaning
    # We need to call the cleaning script. It expects --input and --output.
    # The default input is usually data/raw and output is data/processed/cleaned_sessions.csv
    # We will call the main function directly if possible, or simulate the CLI args.
    # Since the API surface says 'main' exists, we can try to call it with args.
    # However, 'main' usually parses sys.argv. We will patch sys.argv or call internal functions.
    # To be safe and adhere to the "run real code" constraint, we will invoke the logic
    # by calling the internal functions of clean_data.py if exposed, or re-run the script.
    # Given the API surface: `from analysis.clean_data import load_raw_sessions, filter_incomplete, impute_sus, main`
    # We can try to call main with modified argv.
    
    # We'll use a simpler approach: call the main functions of the existing scripts
    # by manipulating sys.argv temporarily.
    
    import sys
    original_argv = sys.argv
    
    # Step 1: Clean Data
    sys.argv = ['clean_data', '--input', str(DATA_RAW_DIR), '--output', str(DATA_PROCESSED_DIR / "cleaned_sessions.csv")]
    try:
        clean_main()
    except SystemExit:
        pass # Expected from argparse
    finally:
        sys.argv = original_argv
    
    # Step 2: Statistical Analysis
    # The run_analysis.py script is the main orchestrator for stats.
    # It loads cleaned_sessions.csv and produces metrics_summary.csv.
    sys.argv = ['run_analysis', '--input', str(DATA_PROCESSED_DIR / "cleaned_sessions.csv"), '--output', str(DATA_PROCESSED_DIR)]
    try:
        from analysis.run_analysis import main as run_analysis_main
        run_analysis_main()
    except SystemExit:
        pass
    finally:
        sys.argv = original_argv
        
    # Step 3: Visualizations
    # The visualizer.py script generates the plots.
    sys.argv = ['run_visualizations', '--input', str(DATA_PROCESSED_DIR / "cleaned_sessions.csv")]
    try:
        from analysis.run_visualizations import main as viz_main
        viz_main()
    except SystemExit:
        pass
    finally:
        sys.argv = original_argv

def main():
    parser = argparse.ArgumentParser(description="Check determinism of the analysis pipeline.")
    parser.add_argument("--update-baseline", action="store_true", help="Update the baseline checksums.")
    args = parser.parse_args()

    print(f"Setting random seed to {FIXED_SEED}...")
    set_all_seeds(FIXED_SEED)

    print("Running analysis pipeline...")
    # Ensure output directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        run_pipeline()
    except Exception as e:
        print(f"Pipeline execution failed: {e}")
        sys.exit(1)

    print("Computing checksums...")
    current_checksums = compute_checksums(OUTPUT_FILES)

    # Check for missing files
    missing = [k for k, v in current_checksums.items() if v == "MISSING"]
    if missing:
        print(f"ERROR: The following files are missing: {missing}")
        print("The pipeline did not produce the expected outputs.")
        sys.exit(1)

    print("Checksums computed successfully.")
    for k, v in current_checksums.items():
        print(f"  {Path(k).name}: {v[:16]}...")

    if args.update_baseline:
        print(f"Updating baseline at {BASELINE_CHECKSUMS_FILE}...")
        save_baseline(current_checksums)
        print("Baseline updated.")
        sys.exit(0)

    baseline = load_baseline()
    if not baseline:
        print("No baseline found. Creating one for future runs.")
        save_baseline(current_checksums)
        print("Baseline created. Run again to verify determinism.")
        sys.exit(0)

    # Compare
    mismatches = []
    for path, checksum in current_checksums.items():
        if baseline.get(path) != checksum:
            mismatches.append(path)

    if mismatches:
        print("DETERMINISM CHECK FAILED: Outputs differ from baseline.")
        for m in mismatches:
            print(f"  Mismatch: {Path(m).name}")
            print(f"    Expected: {baseline.get(m)}")
            print(f"    Got:      {checksum}")
        sys.exit(1)
    else:
        print("DETERMINISM CHECK PASSED: All outputs match the baseline.")
        sys.exit(0)

if __name__ == "__main__":
    main()