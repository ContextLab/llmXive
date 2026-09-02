"""
Main Entry Point.
Orchestrates the full pipeline: Ingestion -> Modeling -> Robustness.
"""

import argparse
import sys
import os
import json
from pathlib import Path

try:
    from config import get_project_root, get_random_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_project_root, get_random_state

from ingestion import run_dgp_pipeline
from modeling import run_full_analysis
from robustness import run_robustness_checks

def main():
    parser = argparse.ArgumentParser(description="Run full analysis pipeline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n", type=int, default=500, help="Number of participants for DGP")
    args = parser.parse_args()

    PROJECT_ROOT = get_project_root()
    DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

    # Ensure output directories exist
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ingestion
    print("--- Phase 1: Ingestion ---")
    try:
        run_dgp_pipeline(args.n, args.seed)
    except SystemExit as e:
        if e.code != 0:
            print("Ingestion failed.")
            sys.exit(e.code)

    # 2. Modeling
    print("--- Phase 2: Modeling ---")
    try:
        run_full_analysis(args.seed)
    except SystemExit as e:
        if e.code != 0:
            print("Modeling failed.")
            sys.exit(e.code)

    # 3. Robustness
    print("--- Phase 3: Robustness ---")
    try:
        run_robustness_checks(args.seed)
    except SystemExit as e:
        if e.code != 0:
            print("Robustness checks failed.")
            sys.exit(e.code)

    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    main()