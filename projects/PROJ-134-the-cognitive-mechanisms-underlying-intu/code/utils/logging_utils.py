import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

class LogType:
    """Constants for log types."""
    EXCLUSION = "EXCLUSION"
    VR_MAPPING = "VR_MAPPING"
    PIPELINE_STEP = "PIPELINE_STEP"
    ERROR = "ERROR"
    INFO = "INFO"

def get_logger(name: str = "pipeline", log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger that writes to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler (optional)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def get_log_path(log_type: str) -> Path:
    """Get the appropriate log file path based on log type."""
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if log_type == LogType.EXCLUSION:
        return log_dir / f"exclusions_{timestamp}.log"
    elif log_type == LogType.VR_MAPPING:
        return log_dir / f"vr_mapping_{timestamp}.log"
    else:
        return log_dir / f"pipeline_{timestamp}.log"

def log_exclusion(reason: str, log_file: Optional[str] = None):
    """Log an exclusion reason."""
    if not log_file:
        log_file = str(get_log_path(LogType.EXCLUSION))
    
    logger = get_logger("exclusion", log_file)
    logger.log(logging.WARNING, f"[EXCLUSION] {reason}")

def log_vr_mapping(mapping_details: Dict[str, Any], log_file: Optional[str] = None):
    """Log VR scene mapping details."""
    if not log_file:
        log_file = str(get_log_path(LogType.VR_MAPPING))
    
    logger = get_logger("vr_mapping", log_file)
    logger.log(logging.INFO, f"[VR_MAPPING] {mapping_details}")

def log_pipeline_step(step_description: str, log_file: Optional[str] = None):
    """Log a pipeline step."""
    if not log_file:
        log_file = str(get_log_path(LogType.PIPELINE_STEP))
    
    logger = get_logger("pipeline", log_file)
    logger.log(logging.INFO, f"[STEP] {step_description}")

def get_exclusion_log_path() -> Path:
    """Get the path for the exclusion log file."""
    return get_log_path(LogType.EXCLUSION)

def get_vr_mapping_log_path() -> Path:
    """Get the path for the VR mapping log file."""
    return get_log_path(LogType.VR_MAPPING)
