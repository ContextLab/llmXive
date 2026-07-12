"""
Wrapper script to generate synthetic data for the audit pipeline.
Calls the main generator from src/audit/synthetic.py.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path if running from scripts
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.src.audit.synthetic import main as generate_synthetic_main
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def main():
    """Entry point for the synthetic data generation wrapper."""
    logger.info("Starting synthetic data generation via wrapper script.")
    try:
        generate_synthetic_main()
        logger.info("Synthetic data generation completed successfully.")
    except Exception as e:
        logger.error(f"Synthetic data generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()