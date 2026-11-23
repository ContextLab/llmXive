import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging
import sys

# FR-008 Disclaimer Constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def init_exclusion_log(log_path: str = "logs/exclusion.log") -> None:
    """
    Initialize the exclusion log file with a CSV header if it does not exist.
    Header: timestamp,dataset_id,missing_variable_name,reason
    """
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(log_path):
        with open(log_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'dataset_id', 'missing_variable_name', 'reason'])

def log_exclusion(dataset_id: str, missing_variable_name: str, reason: str, log_path: str = "logs/exclusion.log") -> None:
    """
    Log an exclusion event to the CSV log file.
    """
    timestamp = datetime.now().isoformat()
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, dataset_id, missing_variable_name, reason])

def log_warning(message: str, log_path: str = "logs/warning.log") -> None:
    """
    Log a warning message to a separate warning log file.
    Includes FR-008 disclaimer if applicable.
    """
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    full_message = f"[{timestamp}] {message}"
    
    with open(log_path, 'a') as f:
        f.write(full_message + "\n")
    
    # Also print to stderr for visibility
    print(full_message, file=sys.stderr)

def log_disclaimer(message: str = None) -> None:
    """
    Log the FR-008 disclaimer. If a specific message is provided, it is logged
    alongside the disclaimer. This function ensures the disclaimer appears in
    console output and logs.
    """
    disclaimer_line = f"DISCLAIMER: {FR008_DISCLAIMER}"
    
    if message:
        full_line = f"{message} {disclaimer_line}"
    else:
        full_line = disclaimer_line
    
    # Print to stdout
    print(full_line)
    
    # Log to a dedicated disclaimer log if it exists or create it
    log_path = "logs/disclaimer.log"
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    with open(log_path, 'a') as f:
        f.write(f"[{timestamp}] {full_line}\n")

def read_exclusion_log(log_path: str = "logs/exclusion.log") -> list:
    """
    Read the exclusion log and return a list of dictionaries.
    """
    if not os.path.exists(log_path):
        return []
    
    rows = []
    with open(log_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def get_exclusion_count(log_path: str = "logs/exclusion.log") -> int:
    """
    Get the total number of exclusions logged.
    """
    return len(read_exclusion_log(log_path))

def clear_exclusion_log(log_path: str = "logs/exclusion.log") -> None:
    """
    Clear the exclusion log (truncate file).
    """
    with open(log_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'dataset_id', 'missing_variable_name', 'reason'])

def setup_logging_for_pipeline() -> logging.Logger:
    """
    Configure a logger for the pipeline that includes the FR-008 disclaimer
    in its format or initialization messages.
    """
    logger = logging.getLogger('fairness_pipeline')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Log disclaimer on setup
        logger.info(FR008_DISCLAIMER)
        
    return logger
