import os
import sys
import logging
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from flops_analysis import main as run_flops_baseline

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Static K=2 Baseline Execution")
    
    # Default paths if not provided via CLI args (handled by flops_analysis main)
    # The script expects arguments to be passed through
    run_flops_baseline()

if __name__ == "__main__":
    main()