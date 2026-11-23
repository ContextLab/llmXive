import logging
import sys
import time
import tracemalloc
from pathlib import Path
import json
import subprocess
from config import get_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd: list) -> int:
    """Run a shell command and return the exit code."""
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Command failed with exception: {e}")
        return 1

def measure_runtime_and_memory(commands: list) -> Dict[str, Any]:
    """
    Measure total runtime and peak memory for a list of commands.
    Uses tracemalloc for memory profiling.
    """
    tracemalloc.start()
    start_time = time.time()

    for cmd in commands:
        rc = run_command(cmd)
        if rc != 0:
            logger.error(f"Command failed with code {rc}. Stopping.")
            break

    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_seconds = end_time - start_time
    peak_rss_gb = peak / (1024 ** 3)

    return {
        "total_seconds": total_seconds,
        "peak_rss_gb": peak_rss_gb
    }

def save_runtime_metrics(metrics: Dict[str, Any], output_path: str) -> None:
    """Save runtime metrics to a JSON file."""
    from config import ensure_dirs
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Runtime metrics saved to {output_path}")

def main():
    # Define the pipeline commands based on the tasks
    # Note: These paths must match the actual script locations and expected outputs
    commands = [
        [sys.executable, get_path("code/ingestion.py"), "--dataset", "adress", "--output", get_path("data/interim/cleaned_transcripts.csv")],
        [sys.executable, get_path("code/features.py"), "--input", get_path("data/interim/cleaned_transcripts.csv"), "--output", get_path("data/processed/features.csv")],
        [sys.executable, get_path("code/stats.py"), "--input", get_path("data/processed/features.csv"), "--output", get_path("data/processed/stats_results.json")],
        [sys.executable, get_path("code/modeling.py"), "--input", get_path("data/processed/features.csv"), "--output", get_path("data/processed/model_results.json")]
    ]

    metrics = measure_runtime_and_memory(commands)
    save_runtime_metrics(metrics, get_path("data/results/runtime_log.json"))
    logger.info(f"Pipeline execution complete. Metrics: {metrics}")

if __name__ == "__main__":
    main()