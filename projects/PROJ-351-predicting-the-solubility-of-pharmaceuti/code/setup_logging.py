import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure the data/logs directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Define log file paths
RUN_LOG_FILE = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
METRICS_LOG_FILE = LOG_DIR / "metrics.jsonl"

def setup_logger(name: str = "llmXive") -> logging.Logger:
    """
    Configures and returns a logger that writes to both console and a rotating file.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler
    file_handler = logging.FileHandler(RUN_LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def log_exclusion_counts(
    total_count: int,
    invalid_smiles: int,
    missing_logS: int,
    source: str = "preprocess"
) -> None:
    """
    Logs the counts of excluded molecules during data processing.
    """
    logger = setup_logger()
    logger.info(f"Exclusion counts for {source}: Total={total_count}, Invalid SMILES={invalid_smiles}, Missing logS={missing_logS}")
    
    # Also append to a summary file for easy retrieval
    summary_file = LOG_DIR / "exclusion_summary.json"
    summary_data = []
    if summary_file.exists():
        try:
            with open(summary_file, 'r') as f:
                summary_data = json.load(f)
        except json.JSONDecodeError:
            summary_data = []

    summary_data.append({
        "timestamp": datetime.now().isoformat(),
        "source": source,
        "total": total_count,
        "invalid_smiles": invalid_smiles,
        "missing_logs": missing_logS,
        "excluded": invalid_smiles + missing_logS
    })

    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)

def log_training_metrics(
    model_name: str,
    metrics: Dict[str, float],
    split: str = "test"
) -> None:
    """
    Logs training or evaluation metrics to a JSONL file for aggregation.
    """
    logger = setup_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_name,
        "split": split,
        **metrics
    }
    
    logger.info(f"Metrics for {model_name} ({split}): {json.dumps(metrics)}")
    
    with open(METRICS_LOG_FILE, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    """
    Entry point for testing the logging configuration.
    """
    logger = setup_logger()
    logger.info("Logging infrastructure initialized.")
    
    # Simulate exclusion counts
    log_exclusion_counts(
        total_count=1128,
        invalid_smiles=5,
        missing_logS=2,
        source="test_preprocess"
    )
    
    # Simulate training metrics
    log_training_metrics(
        model_name="RandomForestBaseline",
        metrics={"rmse": 0.85, "r_squared": 0.68},
        split="test"
    )
    
    logger.info("Logging test completed successfully.")

if __name__ == "__main__":
    main()