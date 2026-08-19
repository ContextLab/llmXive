import os
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure root logger.
    """
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(log_level)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    """
    return logging.getLogger(name)

def log_excluded_record(
    record_id: str, 
    reason_code: str, 
    log_path: Optional[Path] = None
) -> None:
    """
    Log a single excluded record.
    Format: record_id, reason_code
    """
    if log_path is None:
        base_dir = Path(__file__).parent.parent.parent
        log_path = base_dir / "data" / "logs" / "record_exclusions.log"
        
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "a") as f:
        f.write(f"{record_id},{reason_code}\n")
        
    logging.debug(f"Record {record_id} excluded: {reason_code}")

def log_species_exclusion_summary(
    summary_df: pd.DataFrame, 
    log_path: Optional[Path] = None
) -> None:
    """
    Log species exclusion summary to a .log file.
    Columns: species_name, reason, observation_count
    """
    if log_path is None:
        base_dir = Path(__file__).parent.parent.parent
        log_path = base_dir / "data" / "logs" / "species_exclusions.log"
        
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "w") as f:
        f.write("species_name,reason,observation_count\n")
        for _, row in summary_df.iterrows():
            f.write(f"{row['species_name']},{row['reason']},{row['observation_count']}\n")
            
    logging.info(f"Species exclusion summary written to {log_path}")

def log_validation_failure(
    message: str, 
    log_path: Optional[Path] = None
) -> None:
    """
    Log a validation failure to a specific log file.
    """
    if log_path is None:
        base_dir = Path(__file__).parent.parent.parent
        log_path = base_dir / "data" / "logs" / "validation_error.log"
        
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a") as f:
        f.write(f"{timestamp} - ERROR: {message}\n")
        
    logging.error(message)
