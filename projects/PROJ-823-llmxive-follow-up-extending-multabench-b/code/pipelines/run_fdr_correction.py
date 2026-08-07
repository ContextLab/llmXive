import os
import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info, log_error
from analysis.fdr_correction import main as fdr_main

def main():
    """
    Orchestrator for T034: Run FDR correction on correlation p-values.
    This script ensures the required input artifacts exist and invokes the analysis module.
    """
    parser = argparse.ArgumentParser(description="Run FDR correction pipeline (T034)")
    parser.add_argument("--correlation-input", type=str, 
                        default="data/artifacts/correlation_report_run_id.json",
                        help="Path to the correlation report from T033/T036")
    parser.add_argument("--gap-report", type=str,
                        default="data/artifacts/data_availability_gap_report.json",
                        help="Path to the gap report from T032a")
    parser.add_argument("--integrity-report", type=str,
                        default="data/artifacts/data_integrity_report.json",
                        help="Path to the integrity report from T045")
    parser.add_argument("--output", type=str,
                        default="data/artifacts/fdr_adjusted_pvalues.json",
                        help="Path for the output JSON file")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    ensure_directories()
    
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting FDR Correction Pipeline (T034)...")
    
    # Validate inputs
    input_paths = [args.correlation_input, args.gap_report, args.integrity_report]
    for path in input_paths:
        if not os.path.exists(path):
            logger.error(f"Required input file missing: {path}")
            sys.exit(1)
    
    logger.info(f"Input files validated. Running FDR correction...")
    
    # Run the core logic
    try:
        # We call the main function from the analysis module directly to reuse logic
        # The analysis.fdr_correction.main() expects CLI args, so we simulate them
        sys.argv = [
            "run_fdr_correction.py",
            "--correlation-input", args.correlation_input,
            "--gap-report", args.gap_report,
            "--integrity-report", args.integrity_report,
            "--output", args.output,
            "--alpha", str(args.alpha)
        ]
        fdr_main()
        logger.info("FDR Correction completed successfully.")
    except Exception as e:
        logger.error(f"FDR Correction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()