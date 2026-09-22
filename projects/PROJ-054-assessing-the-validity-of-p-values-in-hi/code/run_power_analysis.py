import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import the function from the utils module
from utils.simulation import run_power_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for running the power analysis.
    Reads configuration (if any) and writes the result to data/sweep/power_analysis_result.json.
    """
    output_path = "data/sweep/power_analysis_result.json"
    
    logger.info(f"Starting power analysis to determine minimum iterations.")
    logger.info("Target power: 0.8, Threshold: 0.05, Alpha: 0.05")
    
    try:
        result = run_power_analysis(
            target_power=0.8,
            threshold=0.05,
            alpha=0.05,
            max_iterations=10000,
            output_path=output_path
        )
        logger.info(f"Power analysis completed successfully.")
        logger.info(f"Result: {result}")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()