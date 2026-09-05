import argparse
import sys
import os
import json
from pathlib import Path
from ingestion import run_dgp_pipeline, calculate_reliability_and_halt
from modeling import run_full_analysis
from robustness import run_robustness_checks
from utils.checksum import update_all_artifacts_in_directory

from config import get_project_root, get_config, get_random_state

def main():
    parser = argparse.ArgumentParser(description="Main Pipeline for Temporal Discounting Study")
    parser.add_argument('--seed', type=int, default=42, help="Random seed")
    parser.add_argument('--n', type=int, default=500, help="Number of participants")
    args = parser.parse_args()

    project_root = get_project_root()
    os.makedirs(project_root / 'logs', exist_ok=True)

    # Step 1: Data Generation (T013/T014)
    # Assuming real data check is skipped for this run or handled in ingestion
    # We force DGP for the pipeline run to ensure artifacts exist
    print("Step 1: Generating Data...")
    run_dgp_pipeline(args.n, args.seed)

    # Step 2: Reliability Check (T014b)
    print("Step 2: Running Reliability Check (T014b)...")
    try:
        calculate_reliability_and_halt()
    except SystemExit as e:
        if e.code != 0:
            print("Pipeline halted due to reliability failure.")
            sys.exit(1)

    # Step 3: Harmonization and Validation (T015a, T015b)
    # This is handled inside run_full_analysis or we call specific ingestion functions
    # For simplicity, we assume run_full_analysis handles the rest of the pipeline
    print("Step 3: Running Analysis...")
    run_full_analysis()

    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
