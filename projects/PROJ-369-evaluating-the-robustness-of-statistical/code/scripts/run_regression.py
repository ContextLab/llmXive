"""
Script to run the regression analysis stage.
This script invokes the regression module and ensures outputs are written.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.regression import main as regression_main
from src.utils.logging import setup_logger, log_info, log_error

def main():
    """Main entry point for the regression script."""
    log_info("Starting regression analysis script...")
    
    try:
        # Run the regression analysis
        regression_main()
        log_info("Regression analysis completed successfully.")
        
    except Exception as e:
        log_error(f"Regression script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()