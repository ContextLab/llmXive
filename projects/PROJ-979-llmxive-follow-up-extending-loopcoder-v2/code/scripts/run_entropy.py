"""
Script to run the entropy extraction pipeline.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.entropy import main as entropy_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for running entropy extraction.
    """
    # Default paths
    input_path = "data/processed/filtered_splits.json"
    output_path = "data/processed/entropy_results.csv"
    sample_size = None

    # Check for command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run Entropy Extraction')
    parser.add_argument('--input', type=str, default=input_path, help='Input file path')
    parser.add_argument('--output', type=str, default=output_path, help='Output file path')
    parser.add_argument('--sample-size', type=int, default=None, help='Sample size for validation')
    
    args = parser.parse_args()
    
    # Resolve paths relative to project root
    input_path = str(project_root / args.input)
    output_path = str(project_root / args.output)
    
    logger.info(f"Starting entropy extraction...")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    if args.sample_size:
        logger.info(f"Sample size: {args.sample_size}")
    
    try:
        entropy_main(input_path, output_path, args.sample_size)
        logger.info("Entropy extraction completed successfully.")
    except Exception as e:
        logger.error(f"Entropy extraction failed: {e}")
        raise

if __name__ == '__main__':
    main()