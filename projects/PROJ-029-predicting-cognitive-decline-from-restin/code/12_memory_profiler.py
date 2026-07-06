"""
Memory Profiling CI Step (T043)

This script wraps the major pipeline stages to log peak memory usage.
It runs each stage, monitors RAM via psutil, and appends results to
data/artifacts/memory_profile.log.
"""
import os
import sys
import time
import subprocess
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.logger import get_logger
from utils.memory_profiler import MemoryMonitor, get_peak_memory_gb

# Configuration
SCRIPTS_TO_PROFILE = [
    {
        "name": "download_and_filter",
        "module": "01_download_and_filter",
        "func": "main",
        "description": "Download ds000246 and filter subjects"
    },
    {
        "name": "preprocess_and_parcellate",
        "module": "02_preprocess_and_parcellate",
        "func": "main",
        "description": "Preprocess fMRI and extract timeseries"
    },
    {
        "name": "compute_graph_metrics",
        "module": "03_compute_graph_metrics",
        "func": "main",
        "description": "Calculate graph metrics from connectivity matrices"
    },
    {
        "name": "train_model",
        "module": "04_train_model",
        "func": "main",
        "description": "Train Random Forest with nested CV"
    },
    {
        "name": "permutation_test",
        "module": "06_permutation_test",
        "func": "main",
        "description": "Run permutation test for significance"
    }
]

OUTPUT_PATH = project_root / "data" / "artifacts" / "memory_profile.log"

def log_entry(logger, entry: Dict[str, Any]):
    """Append a formatted log entry to the memory profile log file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    log_line = (
        f"[{timestamp}] "
        f"Script: {entry['script_name']} | "
        f"Peak RAM: {entry['peak_ram_gb']:.2f} GB | "
        f"Duration: {entry['duration_s']:.2f}s | "
        f"Status: {entry['status']} | "
        f"Note: {entry['note']}\n"
    )
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        f.write(log_line)
    logger.info(log_line.strip())

def run_script_with_monitoring(script_info: Dict[str, Any], logger) -> Dict[str, Any]:
    """
    Run a specific script module, monitoring memory usage.
    Returns a dictionary with results.
    """
    script_name = script_info["name"]
    module_name = script_info["module"]
    func_name = script_info["func"]

    logger.info(f"Starting profile for: {script_name} ({script_info['description']})")

    monitor = MemoryMonitor()
    monitor.start()

    start_time = time.time()
    status = "success"
    note = "Completed successfully"
    peak_ram_gb = 0.0

    try:
        # Import the module dynamically
        module = __import__(module_name, fromlist=[func_name])
        main_func = getattr(module, func_name)

        # Execute the main function
        # Note: We assume the main functions handle their own arguments or use defaults
        # If they require specific CLI args, we would need to parse sys.argv or mock them.
        # For this CI step, we assume the pipeline has been set up or the script handles
        # missing data gracefully (e.g., skipping if data not present).
        main_func()

    except Exception as e:
        status = "failed"
        note = f"Error: {str(e)}"
        logger.error(f"Script {script_name} failed: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        monitor.stop()
        peak_ram_gb = monitor.get_peak_gb()

    result = {
        "script_name": script_name,
        "description": script_info["description"],
        "peak_ram_gb": peak_ram_gb,
        "duration_s": duration,
        "status": status,
        "note": note
    }

    log_entry(logger, result)
    return result

def main():
    """Main entry point for the memory profiler CI step."""
    logger = get_logger("memory_profiler")
    logger.info("=== Starting Memory Profiling CI Step (T043) ===")

    results = []
    for script_info in SCRIPTS_TO_PROFILE:
        result = run_script_with_monitoring(script_info, logger)
        results.append(result)

    logger.info("=== Memory Profiling Complete ===")
    logger.info(f"Results written to: {OUTPUT_PATH}")

    # Print summary to stdout for CI visibility
    print("\n--- Memory Profile Summary ---")
    for res in results:
        print(f"{res['script_name']}: {res['peak_ram_gb']:.2f} GB ({res['status']})")
    print(f"Log saved to: {OUTPUT_PATH}")

    # Return exit code 0 even if some scripts failed, as long as we logged them
    # The CI system can parse the log for specific failures if needed.
    return 0

if __name__ == "__main__":
    sys.exit(main())