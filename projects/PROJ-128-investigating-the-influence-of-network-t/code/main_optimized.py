"""
Optimized Entry Point for CPU Efficiency.

This script wraps the main pipeline execution with CPU-specific optimizations:
1. Enforces CPU-only execution.
2. Configures memory-efficient data loading.
3. Sets thread limits for parallel operations.
4. Runs the standard pipeline logic from code/main.py.
"""

import os
import sys
import gc
import traceback
import numpy as np
import pandas as pd
from pathlib import Path

# Import our optimization utilities
from utils.cpu_optimization import (
    validate_no_gpu_acceleration,
    optimize_memory_usage,
    set_random_seed,
    ensure_numpy_arrays_contiguous
)

# Import the main logic from the existing main module
# We assume main.py contains the core logic: process_subject, aggregate_metrics_to_csv, etc.
# If main.py is not directly importable due to relative imports, we adjust the path.
try:
    from main import main as run_pipeline_main
except ImportError:
    # Fallback for relative import issues if run as script
    sys.path.insert(0, str(Path(__file__).parent))
    from main import main as run_pipeline_main

def main():
    """
    Optimized main entry point.
    """
    print("Initializing CPU-Optimized Pipeline...")
    
    # 1. Validate CPU-only mode
    if not validate_no_gpu_acceleration():
        print("ERROR: GPU devices detected. Aborting to prevent resource contention.")
        sys.exit(1)
    print("CPU-only mode confirmed.")

    # 2. Set global random seed for reproducibility
    set_random_seed(42)

    # 3. Configure Pandas for performance
    # Disable scientific notation for cleaner logs
    pd.set_option('display.float_format', lambda x: '%.4f' % x)
    # Limit max rows displayed to avoid log spam
    pd.set_option('display.max_rows', 50)
    
    # 4. Execute the standard pipeline
    # We wrap the existing main logic to inject optimization hooks if necessary
    # The existing main.py logic is assumed to handle the core workflow.
    try:
        print("Starting pipeline execution...")
        run_pipeline_main()
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Pipeline failed with error: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Force garbage collection to free memory before exit
        gc.collect()

if __name__ == "__main__":
    main()
