import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import get_path, ensure_directories

# Global logger cache to prevent reconfiguration
_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured
        _loggers[name] = logger
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create handlers
    log_dir = get_path("data", "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger

def get_log_path(filename: str) -> Path:
    """
    Get the full path for a log file.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Path to the log file.
    """
    return get_path("data", "logs", filename)

def get_exclusion_log_path() -> Path:
    """
    Get the path for the exclusion log.
    
    Returns:
        Path to exclusion.log.
    """
    return get_log_path("exclusion.log")

def get_vr_mapping_log_path() -> Path:
    """
    Get the path for the VR mapping log.
    
    Returns:
        Path to vr_mapping.log.
    """
    return get_log_path("vr_mapping.log")

def log_exclusion(participant_id: str, reason_code: str, timestamp: Optional[str] = None) -> None:
    """
    Log an exclusion reason to the exclusion log.
    
    Args:
        participant_id: ID of the excluded participant.
        reason_code: Code for the exclusion reason (MISMATCH_ID, MISSING_DATA).
        timestamp: ISO8601 timestamp (defaults to now).
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    log_path = get_exclusion_log_path()
    file_exists = log_path.exists()
    
    with open(log_path, 'a', newline='') as f:
        if not file_exists:
            f.write("participant_id,reason_code,timestamp\n")
        f.write(f"{participant_id},{reason_code},{timestamp}\n")
    
    logger = get_logger(__name__)
    logger.info(f"Excluded participant {participant_id}: {reason_code}")

def log_vr_mapping(story_id: str, salience_level: str, blend_shape_params: Dict[str, float]) -> None:
    """
    Log a VR mapping entry.
    
    Args:
        story_id: ID of the story.
        salience_level: 'low' or 'high'.
        blend_shape_params: Dictionary of blend shape parameters.
    """
    log_path = get_vr_mapping_log_path()
    file_exists = log_path.exists()
    
    with open(log_path, 'a', newline='') as f:
        if not file_exists:
            f.write("story_id,salience_level,blend_shape_params\n")
        params_json = json.dumps(blend_shape_params)
        f.write(f"{story_id},{salience_level},{params_json}\n")
    
    logger = get_logger(__name__)
    logger.info(f"VR Mapping: {story_id} -> {salience_level}")

def log_pipeline_step(step: str, message: str) -> None:
    """
    Log a pipeline step with timestamp.
    
    Args:
        step: Step name (START, SUCCESS, ERROR, etc.).
        message: Detailed message.
    """
    logger = get_logger(__name__)
    logger.info(f"[{step}] {message}")

def main() -> None:
    """Test the logging infrastructure."""
    ensure_directories()
    logger = get_logger("test")
    logger.info("Test log entry")
    log_pipeline_step("TEST", "Logging infrastructure test")
    print("Logging test completed.")

if __name__ == "__main__":
    main()