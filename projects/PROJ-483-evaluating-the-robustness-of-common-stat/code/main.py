"""
Main entry point for the Monte Carlo simulation pipeline.
Orchestrates data loading, dependency injection, simulation sweeps,
aggregation, and reporting.

Added minimal argument handling to support quickstart actions:
- download: only performs dataset fetching and validation (including power verification).
- simulate / plot / verify: placeholder for future extensions (currently no‑op).
"""
import os
import sys
import json
import time
import traceback
import pandas as pd
from pathlib import Path

# Local imports
from config import load_config
from data_loader import load_datasets, CriticalValidationError

# Constants
RESULTS_DIR = Path("results")
DATA_DIR = Path("data")
MANIFESTS_DIR = DATA_DIR / "manifests"

def setup_directories():
    """Ensure all required output directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main entry point for the pipeline.

    Supports a very small subset of actions required by the quickstart:
    - download: fetch and validate datasets (includes power verification).
    - simulate, plot, verify: not implemented in this minimal version.
    """
    start_time = time.time()
    perf_log = {"start_time": start_time, "steps": []}

    # Simple action parsing
    action = None
    if "--action" in sys.argv:
        try:
            idx = sys.argv.index("--action")
            action = sys.argv[idx + 1]
        except (ValueError, IndexError):
            print("Usage error: '--action' requires a following argument.")
            sys.exit(1)

    try:
        setup_directories()
        perf_log["steps"].append({"step": "setup_directories", "status": "success"})

        # Load configuration (even if not used for download)
        print("Loading configuration...")
        config = load_config()
        perf_log["steps"].append({"step": "load_config", "status": "success"})

        if action == "download" or action is None:
            # Perform only the data loading / validation step
            print("Loading and validating datasets (download action)...")
            checksums = load_datasets()
            perf_log["steps"].append({"step": "load_datasets", "status": "success"})
            # No further actions in this minimal mode
        else:
            print(f"Action '{action}' is not implemented in this minimal version.")
            perf_log["steps"].append({"step": f"action_{action}", "status": "skipped"})

        end_time = time.time()
        perf_log["end_time"] = end_time
        perf_log["duration_seconds"] = end_time - start_time
        perf_log["status"] = "success"

        # Save performance log
        with open(RESULTS_DIR / "perf_log.json", 'w') as f:
            json.dump(perf_log, f, indent=2)

        print("Pipeline completed successfully.")

    except CriticalValidationError as e:
        print(f"Critical Validation Error: {e}")
        perf_log["status"] = "failed_validation"
        perf_log["error"] = str(e)
        with open(RESULTS_DIR / "perf_log.json", 'w') as f:
            json.dump(perf_log, f, indent=2)
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        traceback.print_exc()
        perf_log["status"] = "failed"
        perf_log["error"] = str(e)
        with open(RESULTS_DIR / "perf_log.json", 'w') as f:
            json.dump(perf_log, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()