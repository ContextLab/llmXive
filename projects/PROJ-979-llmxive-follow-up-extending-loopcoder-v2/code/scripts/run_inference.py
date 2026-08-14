"""
Script to run the convergence inference pipeline.
Invokes code/src/inference.py with proper arguments.
"""
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from inference import main as run_inference_main

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting convergence inference pipeline...")
    
    try:
        # Run inference with default arguments
        # Can be overridden via command line if needed
        run_inference_main()
        logger.info("Convergence inference pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
