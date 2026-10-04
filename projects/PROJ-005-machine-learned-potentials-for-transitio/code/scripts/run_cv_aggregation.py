"""
Script to run cross-validation metric aggregation (T029b).

This script serves as the entry point for aggregating cross-validation
metrics from individual fold results.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.aggregate_cv_metrics import main

if __name__ == '__main__':
    main()
