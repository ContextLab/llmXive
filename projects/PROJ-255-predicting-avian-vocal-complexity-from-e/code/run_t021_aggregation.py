"""
Runner script for Task T021.

Executes the aggregation of dropped records from T015, T017, and T018
to produce data/interim/dropped_records.csv.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports from src
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data.dropped_records_aggregator import main

if __name__ == "__main__":
    # Configure basic logging for the runner
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()