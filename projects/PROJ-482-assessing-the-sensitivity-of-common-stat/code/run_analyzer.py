"""
Script to run the analysis pipeline.

This script orchestrates the loading, aggregation, and export of simulation results.
Visualization is handled separately by the visualizer module.
"""
import os
import sys
import logging
from analyzer import analyze_and_export

def main():
    """
    Main entry point for the analyzer script.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = 'data/processed/raw_pvalues.csv'
    output_path = 'data/processed/error_rates.csv'
    
    # Check if input exists
    if not os.path.exists(input_path):
        logger = logging.getLogger(__name__)
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the simulation first to generate raw results.")
        sys.exit(1)
    
    logger.info(f"Running analysis pipeline: {input_path} -> {output_path}")
    
    try:
        result_df = analyze_and_export(input_path, output_path)
        logger.info(f"Analysis complete. Aggregated {len(result_df)} scenarios.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
