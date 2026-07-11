import os
import sys
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info, log_error
from analysis.fdr_correction import main as fdr_main

logger = get_logger(__name__)

def main():
    """
    Orchestrate the FDR correction pipeline.
    This script loads p-values from correlation and t-test analyses,
    applies Benjamini-Hochberg correction, and saves the results.
    """
    parser = argparse.ArgumentParser(description="Run FDR correction on analysis p-values")
    parser.add_argument(
        "--input",
        type=str,
        required=False,
        help="Path to JSON file containing p-values (default: data/artifacts/correlation_pvalues.json)"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=False,
        help="Path to output JSON file (default: data/artifacts/fdr_corrected_results.json)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for FDR correction (default: 0.05)"
    )

    args = parser.parse_args()

    # Set up logging
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=log_dir / "fdr_correction.log")

    log_info("Starting FDR correction pipeline")

    # Ensure directories exist
    ensure_directories()

    # Set default paths if not provided
    if args.input is None:
        args.input = str(Path("data/artifacts/correlation_pvalues.json"))
    if args.output is None:
        args.output = str(Path("data/artifacts/fdr_corrected_results.json"))

    # Run FDR correction
    exit_code = fdr_main(args)

    if exit_code == 0:
        log_info("FDR correction pipeline completed successfully")
    else:
        log_error("FDR correction pipeline failed")

    return exit_code

if __name__ == "__main__":
    sys.exit(main())