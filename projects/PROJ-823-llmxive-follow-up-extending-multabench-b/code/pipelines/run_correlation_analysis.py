import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.correlation_analysis import main as correlation_main
from config import ensure_directories
from utils.logging import setup_logging, get_logger, log_info

logger = get_logger(__name__)

def main():
    """
    Orchestrates the T033 correlation analysis pipeline.
    Ensures input files exist and calls the correlation analysis module.
    """
    parser = argparse.ArgumentParser(description="Run T033: Pearson Correlation Analysis Pipeline")
    parser.add_argument("--run-id", type=str, default="baseline", help="Run ID for artifact naming")
    
    args = parser.parse_args()
    setup_logging()
    
    log_info(logger, f"Starting Correlation Analysis Pipeline for Run ID: {args.run_id}")
    
    # Define paths based on previous tasks (T024, T031)
    # These paths are hardcoded as per the requirement to use exact paths from tasks.md
    recovery_ratio_path = "data/artifacts/recovery_ratio_metrics.json"
    metadata_stats_path = "data/processed/metadata_stats_summary.csv"
    output_path = f"data/artifacts/correlation_results_{args.run_id}.json"
    
    # Check for input files
    if not os.path.exists(recovery_ratio_path):
        logger.error(f"Required input file not found: {recovery_ratio_path}")
        logger.error("Please ensure T031 (calculate_recovery_ratio) has been completed.")
        sys.exit(1)
        
    if not os.path.exists(metadata_stats_path):
        logger.error(f"Required input file not found: {metadata_stats_path}")
        logger.error("Please ensure T024 (metadata_stats) has been completed.")
        sys.exit(1)
        
    # Run the analysis
    try:
        sys.argv = [
            "run_correlation_analysis.py",
            "--recovery-ratio-path", recovery_ratio_path,
            "--metadata-stats-path", metadata_stats_path,
            "--output-path", output_path
        ]
        result = correlation_main()
        
        if result == 0:
            log_info(logger, "Correlation analysis pipeline completed successfully.")
        else:
            log_info(logger, "Correlation analysis pipeline completed with warnings.")
            
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()