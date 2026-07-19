"""
Script to execute the Shapiro-Wilk normality audit and write the log file.

This script is invoked by the analysis pipeline to generate the required
normality audit log at data/processed/normality_log.txt.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
from utils.logger import get_logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analysis.stat_utils import log_normality_test
from code.analysis.data_cleaner import DataCleaner

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Shapiro-Wilk normality audit")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/cleaned_sessions.csv",
        help="Path to cleaned session data CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/normality_log.txt",
        help="Path to write normality audit log"
    )
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Running Shapiro-Wilk normality test on {len(df)} records")
    results = log_normality_test(df, str(output_path))
    
    logger.info(f"Normality audit complete. Results written to {output_path}")
    logger.info(f"Test results summary: {results}")
    
    # Return success
    sys.exit(0)

if __name__ == "__main__":
    main()