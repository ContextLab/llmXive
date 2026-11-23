import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Project logger
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_pipeline_summary() -> Dict[str, Any]:
    """
    Load the pipeline summary log to retrieve initial query counts.
    """
    log_path = Path(__file__).resolve().parents[3] / "logs" / "pipeline.log"
    logger.info(f"Loading pipeline summary from {log_path}")
    if not log_path.exists():
        raise FileNotFoundError(f"Pipeline log not found at {log_path}")

    initial_count = None
    with open(log_path, 'r') as f:
        for line in f:
            if "Initial dataset query count:" in line:
                try:
                    initial_count = int(line.strip().split(":")[-1])
                except ValueError:
                    pass
    if initial_count is None:
        logger.warning("Initial dataset count not found in log; defaulting to 0.")
        initial_count = 0

    return {"initial_count": initial_count, "log_path": str(log_path)}

def calculate_completeness(initial_count: int, retained_count: int) -> Dict[str, Any]:
    """
    Calculate the Data Completeness percentage.
    """
    if initial_count == 0:
        completeness = 0.0
    else:
        completeness = (retained_count / initial_count) * 100.0
    logger.info(f"Data completeness calculated: {completeness:.2f}%")
    return {
        "initial_count": initial_count,
        "retained_count": retained_count,
        "completeness_percent": completeness,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def write_completeness_report(metrics: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Write the completeness metrics to a JSON file.
    """
    if output_path is None:
        output_path = Path(__file__).resolve().parents[3] / "results" / "data_completeness.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Data completeness report written to {output_path}")
    return output_path

def run_completeness_check() -> Dict[str, Any]:
    """
    Execute the full completeness check workflow.
    """
    logger.info("Running data completeness check...")
    summary = load_pipeline_summary()
    initial = summary["initial_count"]

    # Determine retained count from processed data directory
    processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
    retained_files = list(processed_dir.glob("*.csv"))
    retained_count = sum(p.stat().st_size for p in retained_files if p.is_file())
    logger.info(f"Retained processed data size (bytes): {retained_count}")

    metrics = calculate_completeness(initial, retained_count)
    write_completeness_report(metrics)
    return metrics

def main() -> int:
    """
    Main entry point for the completeness check script.
    """
    try:
        metrics = run_completeness_check()
        print(json.dumps(metrics, indent=2))
        return 0
    except Exception as e:
        logger.error(f"Completeness check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
