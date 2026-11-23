"""
Script to run CLR transformation on the filtered data and produce the required output artifact.
This script is invoked by the run-book to generate data/processed/clr_transformed_data.parquet.
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from transform import transform_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run CLR transformation on filtered data.")
    parser.add_argument("--input", type=str, default="data/processed/filtered_data.parquet",
                        help="Path to the filtered input data (Parquet)")
    parser.add_argument("--output", type=str, default="data/processed/clr_transformed_data.parquet",
                        help="Path to save the CLR transformed data (Parquet)")
    parser.add_argument("--metadata", type=str, default="data/metadata/compositionality_flag.json",
                        help="Path to compositionality flag file")
    parser.add_argument("--log", type=str, default="data/metadata/method_selection_log.json",
                        help="Path to method selection log file")
    parser.add_argument("--pseudo-count", type=float, default=1e-6, help="Pseudo-count for CLR")
    
    args = parser.parse_args()
    
    # Check if input file exists
    input_file = Path(args.input)
    if not input_file.exists():
        logger.error(f"Input file not found: {args.input}")
        logger.error("Please ensure the pipeline has run up to the filtering stage (T014b) to generate filtered_data.parquet.")
        sys.exit(1)
    
    logger.info(f"Starting CLR transformation pipeline.")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")
    
    try:
        transform_data(
            input_path=args.input,
            output_path=args.output,
            metadata_path=args.metadata,
            method_selection_log_path=args.log,
            pseudo_count=args.pseudo_count
        )
        
        # Verify output
        if Path(args.output).exists():
            logger.info(f"SUCCESS: CLR transformed data written to {args.output}")
            sys.exit(0)
        else:
            logger.error(f"FAILURE: Output file {args.output} was not created.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Transformation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()