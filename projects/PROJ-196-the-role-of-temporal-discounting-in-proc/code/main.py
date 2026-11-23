import argparse
import sys
import logging
from pathlib import Path

from ingestion import verify_urls, load_and_harmonize
from modeling import run_full_analysis
from robustness import run_robustness_checks
from utils.checksum import update_all_artifacts_in_directory

def main():
    """
    Orchestrator for the Temporal Discounting study pipeline.

    Steps:
    1. Verify that the three required data source URLs are reachable.
    2. Load (or generate) and harmonise the dataset.
    3. Run the full modelling analysis.
    4. Execute robustness checks (bootstrap + sensitivity).
    5. Update artifact hashes for reproducibility.
    """
    parser = argparse.ArgumentParser(description="Main Pipeline for Temporal Discounting Study")
    parser.add_argument('--seed', type=int, default=42,
                        help="Random seed for any stochastic steps")
    parser.add_argument('--n', type=int, default=500,
                        help="Number of participants (used when generating synthetic data)")
    parser.add_argument('--url', action='append', dest='urls', default=[],
                        help="Data source URL – specify three times, once per required source")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # ------------------------------------------------------------------
    # Step 1 – URL verification
    # ------------------------------------------------------------------
    try:
        # ``verify_urls`` will raise RuntimeError on any failure.
        # An empty list is a no‑op, which keeps the script usable in test
        # environments where the real URLs are not needed.
        verify_urls(args.urls)
    except RuntimeError as e:
        logging.error(f"URL verification failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2 – Data loading / generation and harmonisation
    # ------------------------------------------------------------------
    try:
        # ``load_and_harmonize`` returns the final harmonised DataFrame.
        # It encapsulates the DGP pipeline (synthetic generation) and
        # the merging / cleaning logic.
        df = load_and_harmonize(n=args.n, seed=args.seed)
    except Exception as e:
        logging.error(f"Data loading / harmonisation failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 3 – Modelling
    # ------------------------------------------------------------------
    try:
        run_full_analysis()
    except Exception as e:
        logging.error(f"Modelling step failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 4 – Robustness checks
    # ------------------------------------------------------------------
    try:
        run_robustness_checks()
    except Exception as e:
        logging.error(f"Robustness checks failed: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 5 – Record artifact hashes for reproducibility
    # ------------------------------------------------------------------
    try:
        update_all_artifacts_in_directory('data/processed')
    except Exception as e:
        logging.error(f"Failed to update artifact hashes: {e}")
        # Non‑fatal – the core analysis succeeded

    logging.info("Pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
