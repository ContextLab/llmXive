"""
Runner script for T021b: Analyze Monte Carlo results to prepare data for threshold identification.

This script reads the Monte Carlo results CSV, aggregates the data by theta value,
and outputs a JSON file with the aggregated statistics ready for curve fitting.

Output: data/processed/threshold_identification_raw.json
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from analysis.fit_utils import analyze_threshold_identification

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Execute the threshold identification analysis."""
    input_path = 'data/processed/mc_results.csv'
    output_path = 'data/processed/threshold_identification_raw.json'
    
    logger.info(f"Starting T021b: Analyze Monte Carlo results")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run the Monte Carlo sweep first (T021a) to generate mc_results.csv")
        return 1
    
    try:
        result = analyze_threshold_identification(input_path, output_path)
        
        if not result['aggregated_data']['thetas']:
            logger.warning("No data points were processed. Check the input file format.")
            return 1
            
        logger.info(f"Successfully processed {result['metadata']['total_iterations']} iterations")
        logger.info(f"Found {result['metadata']['unique_theta_values']} unique theta values")
        logger.info(f"Output written to: {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed with error: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
