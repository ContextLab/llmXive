"""
CI Memory Profiler for llmXive Project PROJ-029.

This script implements a CI step that logs peak memory usage for each major
research script (download, preprocessing, modeling, permutation) to
data/artifacts/memory_profile.log.

It runs the target scripts with a memory monitoring wrapper, captures peak
RAM usage, and appends a structured log entry.
"""
import os
import sys
import time
import json
import subprocess
import threading
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.memory_profiler import get_peak_memory_gb, MemoryMonitor
from utils.logger import get_logger

# Configuration
MAJOR_SCRIPTS = [
    "00_data_gate.py",
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
    "05_evaluate_model.py",
    "06_permutation_test.py",
    "07_sensitivity_analysis.py",
]

OUTPUT_LOG_PATH = PROJECT_ROOT / "data" / "artifacts" / "memory_profile.log"
LOG_INTERVAL = 0.5  # seconds

logger = get_logger("ci_memory_profiler")


def get_memory_usage_gb() -> float:
    """Get current memory usage of the current process in GB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 ** 3)


def run_script_with_monitoring(script_name: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Run a specific script and monitor its peak memory usage.

    Args:
        script_name: Name of the script in code/ directory
        timeout: Optional timeout in seconds

    Returns:
        Dictionary with script name, status, peak memory, runtime, and error info
    """
    script_path = PROJECT_ROOT / "code" / script_name
    result = {
        "script": script_name,
        "status": "unknown",
        "peak_memory_gb": None,
        "runtime_seconds": None,
        "timestamp": datetime.utcnow().isoformat(),
        "error": None
    }

    if not script_path.exists():
        result["status"] = "file_not_found"
        result["error"] = f"Script not found: {script_path}"
        logger.warning(result["error"])
        return result

    logger.info(f"Starting memory profiling for: {script_name}")

    start_time = time.time()
    peak_memory = [0.0]
    process = None

    try:
        # Start the subprocess
        cmd = [sys.executable, str(script_path)]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(PROJECT_ROOT / "code")
        )

        # Monitor memory in a separate thread
        def monitor_memory():
            while True:
                try:
                    if process.poll() is not None:
                        break
                    current_mem = get_memory_usage_gb()
                    if current_mem > peak_memory[0]:
                        peak_memory[0] = current_mem
                except psutil.NoSuchProcess:
                    break
                time.sleep(LOG_INTERVAL)

        monitor_thread = threading.Thread(target=monitor_memory, daemon=True)
        monitor_thread.start()

        # Wait for process to complete or timeout
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            exit_code = process.returncode
            result["stdout"] = stdout.decode('utf-8', errors='replace')[:1000]
            result["stderr"] = stderr.decode('utf-8', errors='replace')[:1000]
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            result["status"] = "timeout"
            result["error"] = f"Script timed out after {timeout} seconds"
            logger.error(result["error"])
            return result

        runtime = time.time() - start_time
        result["runtime_seconds"] = runtime
        result["peak_memory_gb"] = peak_memory[0]

        if exit_code == 0:
            result["status"] = "success"
            logger.info(f"Completed {script_name}: {peak_memory[0]:.2f} GB peak, {runtime:.2f}s")
        else:
            result["status"] = "failed"
            result["error"] = f"Script exited with code {exit_code}"
            logger.warning(f"{script_name} failed with exit code {exit_code}")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        logger.error(f"Error profiling {script_name}: {e}")

    return result


def log_entry(entry: Dict[str, Any]) -> None:
    """Append a log entry to the memory profile log file."""
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_LOG_PATH, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    logger.info(f"Logged entry for {entry['script']}")


def main() -> int:
    """Main entry point for CI memory profiler."""
    logger.info("Starting CI Memory Profiler")
    logger.info(f"Output log path: {OUTPUT_LOG_PATH}")

    # Ensure output directory exists
    OUTPUT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write header if file is new
    if not OUTPUT_LOG_PATH.exists():
        with open(OUTPUT_LOG_PATH, 'w') as f:
            f.write(f"# Memory Profile Log - Generated {datetime.utcnow().isoformat()}\n")
            f.write(f"# Format: JSON lines with script, status, peak_memory_gb, runtime_seconds, timestamp\n\n")

    results = []
    for script in MAJOR_SCRIPTS:
        logger.info(f"Processing: {script}")
        result = run_script_with_monitoring(script, timeout=3600)  # 1 hour timeout per script
        results.append(result)
        log_entry(result)

    # Summary
    total_peak = sum(r['peak_memory_gb'] or 0 for r in results)
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] in ['failed', 'error', 'timeout'])

    summary = {
        "summary": True,
        "timestamp": datetime.utcnow().isoformat(),
        "total_scripts": len(MAJOR_SCRIPTS),
        "successful": successful,
        "failed": failed,
        "total_peak_memory_gb": total_peak,
        "scripts_profiled": [r['script'] for r in results]
    }

    log_entry(summary)
    logger.info(f"CI Memory Profiler completed. {successful}/{len(MAJOR_SCRIPTS)} scripts succeeded.")
    logger.info(f"Peak memory log written to: {OUTPUT_LOG_PATH}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())