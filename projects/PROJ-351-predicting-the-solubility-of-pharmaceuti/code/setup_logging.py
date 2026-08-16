import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Ensure the code directory is in the path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

LOG_DIR = Path("data/logs")
LOG_FILE_NAME = "pipeline_run.log"
METRICS_FILE_NAME = "training_metrics.json"
EXCLUSIONS_FILE_NAME = "exclusion_counts.json"

def setup_logger(name: str, log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger that writes to both console and a file.
    Creates the log directory if it doesn't exist.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if logger is reused
    if logger.handlers:
        return logger

    # Ensure log directory exists
    if log_file is None:
        log_file = LOG_DIR / LOG_FILE_NAME
    else:
        log_file = Path(log_file)
    
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    fh = logging.FileHandler(log_file, mode='a')
    fh.setLevel(level)
    fh.setFormatter(formatter)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_exclusion_counts(logger: logging.Logger, exclusion_data: Dict[str, int], output_file: Optional[Path] = None) -> None:
    """
    Logs exclusion counts to the logger and saves them to a JSON file.
    
    Args:
        logger: The logger instance to use.
        exclusion_data: A dictionary of exclusion reasons and counts (e.g., {"invalid_smiles": 5, "nan_logS": 2}).
        output_file: Path to save the JSON file. Defaults to data/logs/exclusion_counts.json.
    """
    if output_file is None:
        output_file = LOG_DIR / EXCLUSIONS_FILE_NAME
    else:
        output_file = Path(output_file)
    
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Log to logger
    logger.info("Recording exclusion counts:")
    for reason, count in exclusion_data.items():
        logger.info(f"  - {reason}: {count}")
    
    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record = {
        "timestamp": timestamp,
        "exclusions": exclusion_data
    }
    
    # If file exists, we might want to append or overwrite depending on needs.
    # For this task, we overwrite with the latest run's counts to keep it clean,
    # or we could append a list. Given the task says "capture exclusion counts",
    # a single file representing the last run or a log of runs is fine.
    # Let's append to a list in the JSON if it exists to maintain history.
    existing_data = []
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
        except json.JSONDecodeError:
            existing_data = []

    existing_data.append(record)

    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Exclusion counts saved to {output_file}")

def log_training_metrics(logger: logging.Logger, metrics_data: Dict[str, float], output_file: Optional[Path] = None) -> None:
    """
    Logs training metrics to the logger and saves them to a JSON file.
    
    Args:
        logger: The logger instance to use.
        metrics_data: A dictionary of metric names and values (e.g., {"rmse": 0.5, "r2": 0.8}).
        output_file: Path to save the JSON file. Defaults to data/logs/training_metrics.json.
    """
    if output_file is None:
        output_file = LOG_DIR / METRICS_FILE_NAME
    else:
        output_file = Path(output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Log to logger
    logger.info("Recording training metrics:")
    for metric_name, value in metrics_data.items():
        logger.info(f"  - {metric_name}: {value:.6f}")

    # Save to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record = {
        "timestamp": timestamp,
        "metrics": metrics_data
    }

    # Append to list in file to maintain history of runs
    existing_data = []
    if output_file.exists():
        try:
            with open(output_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
        except json.JSONDecodeError:
            existing_data = []

    existing_data.append(record)

    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

    logger.info(f"Training metrics saved to {output_file}")

def main():
    """
    Main function to demonstrate logging infrastructure setup.
    This script can be run to initialize the logging directory structure
    and verify that logging functions work correctly.
    """
    logger = setup_logger("T008_Logging_Demo")
    logger.info("Logging infrastructure initialized.")

    # Demo exclusion counts
    demo_exclusions = {
        "invalid_smiles": 12,
        "nan_logS": 3,
        "molecular_weight_out_of_range": 0
    }
    log_exclusion_counts(logger, demo_exclusions)

    # Demo training metrics
    demo_metrics = {
        "rmse": 0.654321,
        "r2": 0.823456,
        "mae": 0.512345
    }
    log_training_metrics(logger, demo_metrics)

    logger.info("Logging infrastructure demo completed successfully.")

if __name__ == "__main__":
    main()