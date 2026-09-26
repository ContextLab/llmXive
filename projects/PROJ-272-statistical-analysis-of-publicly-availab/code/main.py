"""
Main orchestration script for the statistical analysis pipeline.
Executes the full run-book sequence.
"""
import logging
import sys
import time
import tracemalloc
from pathlib import Path
import json
import subprocess

from config import get_path, ensure_dirs

def run_command(cmd: list) -> int:
    """Run a shell command and return the exit code."""
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {cmd}. Error: {e}")
        return e.returncode
    except FileNotFoundError:
        logging.error(f"Command not found: {cmd[0]}")
        return 127

def measure_runtime_and_memory(commands: list) -> dict:
    """
    Wraps the execution of commands to measure total time and peak memory.
    """
    tracemalloc.start()
    start_time = time.time()
    
    exit_codes = []
    for cmd in commands:
        logging.info(f"Running: {' '.join(cmd)}")
        rc = run_command(cmd)
        exit_codes.append(rc)
        if rc != 0:
            logging.error(f"Command failed with code {rc}. Stopping.")
            break
      
    end_time = time.time()
    current, peak = tracemalloc.get_memory_usage()
    tracemalloc.stop()
    
    total_seconds = end_time - start_time
    peak_rss_gb = peak / (1024 ** 3)
    
    return {
        "total_seconds": total_seconds,
        "peak_rss_gb": peak_rss_gb,
        "exit_codes": exit_codes
    }

def save_runtime_metrics(metrics: dict, output_path: Path):
    """Save runtime metrics to a JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    logging.info(f"Runtime metrics saved to {output_path}")

def main():
    """
    Main entry point. Executes the pipeline steps in order.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    project_root = Path(__file__).resolve().parent.parent
    ensure_dirs(project_root)
    
    # Define the run-book commands
    # Note: We assume virtualenv is activated or python is in PATH.
    # If running in a container/CI, 'python' usually resolves to the correct interpreter.
    python = sys.executable
    
    commands = [
        [python, str(project_root / "code" / "verify_plan.py")],
        [python, str(project_root / "code" / "ingestion.py"), "--dataset", "adress", "--output", str(project_root / "data" / "interim" / "cleaned_transcripts.csv")],
        [python, str(project_root / "code" / "t012b_raw_record_count.py")], # Counts raw records
        [python, str(project_root / "code" / "t012e_low_power_warning.py")], # Low power check
        [python, str(project_root / "code" / "t012f_checksum_record.py")],   # Raw checksum
        [python, str(project_root / "code" / "t016_create_cleaned_dataset.py")], # Create final CSV
        [python, str(project_root / "code" / "t012h_success_criterion.py")], # Success criterion
        [python, str(project_root / "code" / "t012g_metadata_aggregation.py")], # Merge metadata
        [python, str(project_root / "code" / "features.py"), "--input", str(project_root / "data" / "interim" / "cleaned_adress.csv"), "--output", str(project_root / "data" / "processed" / "features.csv")],
        [python, str(project_root / "code" / "t024c_checksum.py")],         # Embeddings checksum
        [python, str(project_root / "code" / "stats.py"), "--input", str(project_root / "data" / "processed" / "features.csv"), "--output", str(project_root / "data" / "processed" / "stats_results.json")],
        [python, str(project_root / "code" / "modeling.py"), "--input", str(project_root / "data" / "processed" / "features.csv"), "--output", str(project_root / "data" / "processed" / "model_results.json")],
        [python, str(project_root / "code" / "t046_measure_runtime.py")],    # Measure runtime
    ]
    
    logging.info("Starting pipeline execution...")
    metrics = measure_runtime_and_memory(commands)
    
    output_path = project_root / "data" / "results" / "runtime_log.json"
    save_runtime_metrics(metrics, output_path)
    
    if metrics["exit_codes"] and any(rc != 0 for rc in metrics["exit_codes"]):
        logging.error("Pipeline execution failed.")
        sys.exit(1)
    else:
        logging.info("Pipeline execution completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
