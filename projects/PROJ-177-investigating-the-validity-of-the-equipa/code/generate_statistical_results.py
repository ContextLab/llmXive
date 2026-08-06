"""
Wrapper to generate statistical results (if needed separately).
Currently, stats.py main handles this.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
from stats import run_statistical_analysis, StatsError
import logging
from config import load_config

logger = logging.getLogger(__name__)

def main():
    # This script is a wrapper to ensure stats.py runs if called directly
    # It delegates to stats.py main logic
    try:
        # Re-implement main logic here or call stats.main()
        # To avoid circular imports or re-execution issues, we just call stats.main()
        # But since stats.main() writes the file, we just ensure it runs.
        from stats import main as stats_main
        stats_main()
    except Exception as e:
        logger.error(f"Failed to generate statistical results: {e}")
        sys.exit(1)