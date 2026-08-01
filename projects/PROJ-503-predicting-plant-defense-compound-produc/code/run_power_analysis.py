"""
Runner script for power analysis task T008.

Executes power analysis on the final paired set and enforces abort criteria.
Output: logs/power_analysis_report.json
"""
import json
import logging
import sys
from pathlib import Path
from code.power_analysis import calculate_required_n, run_power_analysis
from code.exceptions import E_POWER

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for T008 power analysis.
    """
    logger.info("Starting power analysis task T008")
    
    try:
        # Run the power analysis via the module's main function
        # This handles loading data, calculating power, and writing output
        from code.power_analysis import main as power_analysis_main
        result = power_analysis_main()
        
        logger.info("Power analysis completed successfully")
        return 0
        
    except E_POWER as e:
        logger.error(f"E-POWER error: {e}")
        print(f"\nABORTED: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\nERROR: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
