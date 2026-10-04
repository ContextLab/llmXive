"""
Runner script for T033c: Baseline Reaction Time Task Integration.
Invokes fetch_baseline_reaction_time.py.
"""
import sys
import logging
from pathlib import Path

# Setup logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    logger.info("Starting Baseline Reaction Time Task Integration (T033c)...")
    
    try:
        # Import and run the main logic
        from fetch_baseline_reaction_time import main as fetch_main
        fetch_main()
        logger.info("Baseline Reaction Time Task Integration completed successfully.")
    except Exception as e:
        logger.error(f"Baseline Reaction Time Task Integration failed: {e}")
        # Re-raise to ensure the pipeline fails loudly if data is missing
        raise

if __name__ == "__main__":
    main()