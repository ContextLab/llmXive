"""
Entry point script to execute the metrics calculation batch process.
This script loads graphs from data/processed/graphs/, calculates metrics,
and writes the result to data/processed/metrics.csv.
"""
import sys
from pathlib import Path
from metrics import main

if __name__ == "__main__":
    main()
