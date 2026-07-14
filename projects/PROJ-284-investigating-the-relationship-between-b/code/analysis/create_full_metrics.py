"""
Alternative entry point for creating full metrics.
Delegates to correlations module.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.logging_config import get_logger
from code.analysis.correlations import main as correlations_main

logger = get_logger(__name__)

def main():
    """Run correlation analysis which generates full metrics."""
    correlations_main()

if __name__ == "__main__":
    main()