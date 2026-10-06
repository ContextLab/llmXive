import os
import sys
import logging
import argparse
from analyzer import analyze_and_export

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Run Stability Analysis (T026c)')
    parser.add_argument('--input', type=str, required=True, help='Path to aggregated_results.csv')
    parser.add_argument('--output', type=str, required=True, help='Output directory for results and plots')
    
    args = parser.parse_args()
    
    logger.info(f"Starting stability analysis with input: {args.input}")
    logger.info(f"Output directory: {args.output}")
    
    try:
        analyze_and_export(args.input, args.output)
        logger.info("Stability analysis completed successfully.")
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
