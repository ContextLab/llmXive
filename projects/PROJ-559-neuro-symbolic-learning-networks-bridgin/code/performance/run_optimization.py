import os
import sys
import argparse
import logging
from performance.resource_optimization import run_optimization_validation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main_entry():
    """
    Main entry point for running the full optimization pipeline.
    Executes validation checks and reports results.
    """
    logger.info("Starting optimization validation pipeline")
    
    try:
        results = run_optimization_validation()
        
        if results.get("status") == "PASS":
            logger.info("Optimization validation PASSED")
            print("Optimization validation PASSED")
            print(f"Max memory usage: {results.get('max_memory_mb', 0):.2f} MB")
            print(f"Limit: {results.get('limit_mb', 0):.2f} MB")
            sys.exit(0)
        else:
            logger.error("Optimization validation FAILED")
            print("Optimization validation FAILED")
            print(f"Reason: {results.get('reason', 'Unknown')}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
