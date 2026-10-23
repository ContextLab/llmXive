"""
run_pipeline.py
---------------
End‑to‑end driver for a small real‑case run (default 5 subjects).

It sequentially invokes:

  1. ``src.download_data`` – downloads raw time‑series and behavioural data.
  2. ``src.data.qc``          – quality‑control, producing clean_subjects.parquet.
  3. ``src.compute_entropy`` – computes the entropy matrix and covariates.

The script respects the RAM budget by delegating the heavy work to
``compute_entropy`` which batches parcels.

``--dry-run`` can be used by the test suite to avoid any heavy I/O.
"""
import argparse
import sys
from llmxive_toolkit import get_logger
from src.download_data import main as download_main
from src.data.qc import main as qc_main
from src.compute_entropy import main as entropy_main

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the full pipeline for a small cohort."
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=5,
        help="Number of subjects to process (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a dry‑run that skips all heavy processing (used for tests).",
    )
    args = parser.parse_args()
    logger = get_logger(__name__)

    if args.dry_run:
        logger.info("Dry‑run requested – exiting successfully without processing.")
        return

    # ------------------------------------------------------------------
    # Step 1 – Download data
    # ------------------------------------------------------------------
    logger.info("Downloading %d subjects.", args.subjects)
    sys.argv = [
        "download_data",
        "--subject-limit",
        str(args.subjects),
        "--output-dir",
        "data",
    ]
    download_main()

    # ------------------------------------------------------------------
    # Step 2 – Quality control
    # ------------------------------------------------------------------
    logger.info("Running quality control.")
    sys.argv = ["qc"]  # qc.main does not require explicit arguments
    qc_main()

    # ------------------------------------------------------------------
    # Step 3 – Entropy computation
    # ------------------------------------------------------------------
    logger.info("Computing entropy matrix.")
    input_path = "data/derived/clean_subjects.parquet"
    output_path = "results/entropy_matrix.parquet"
    sys.argv = [
        "compute_entropy",
        "--input",
        input_path,
        "--output",
        output_path,
        "--scales",
        "1",
        "2",
        "3",
        "4",
        "5",
        "--r",
        "0.15",
        "--m",
        "2",
    ]
    entropy_main()

    logger.info(
        "Pipeline completed successfully. Results are in the 'results/' folder."
    )

if __name__ == "__main__":
    main()
