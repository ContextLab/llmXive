"""
Script to run sensitivity convergence inference (k=4) for T013b.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference import main as run_inference_main

logger = logging.getLogger(__name__)

def main():
    """Entry point for sensitivity inference."""
    logger.info("Starting sensitivity convergence inference (k=4)...")
    
    # Run the inference with k_max=4 for sensitivity analysis
    # The main function handles argument parsing
    run_inference_main()
    
    logger.info("Sensitivity convergence inference completed.")

if __name__ == "__main__":
    main()
