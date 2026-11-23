import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Project root relative to this file (code/ is one level down)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists for logging
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger = None

def get_logger(name: str = "neural_correlates") -> logging.Logger:
    """
    Returns a configured logger instance.
    If not initialized, sets up logging to console and file.
    """
    global _logger
    if _logger is None:
        _logger = initialize_logging(name)
    else:
        # Ensure the logger has the correct name if requested differently
        # but reusing the global instance logic for simplicity in this module
        if _logger.name != name:
            _logger = initialize_logging(name)
    return _logger

def initialize_logging(name: str = "neural_correlates", level: int = logging.INFO) -> logging.Logger:
    """
    Initializes the logging infrastructure.
    - Console: INFO level and above
    - File (data/preprocessing.log): DEBUG level and above
    - YAML Log (data/preprocessing.yaml): Appends structured parameter logs
    """
    global _logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)

    # File Handler (for detailed logs)
    log_file_path = DATA_DIR / "preprocessing.log"
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    # Initialize the YAML log file if it doesn't exist
    yaml_log_path = DATA_DIR / "preprocessing.yaml"
    if not yaml_log_path.exists():
        # Create a basic header structure for the YAML log
        # We will use a custom handler or manual writing for YAML to ensure valid structure
        with open(yaml_log_path, 'w') as f:
            f.write("# Preprocessing Log - Initialized\n")
            f.write(f"# Created: {datetime.now().isoformat()}\n")
            f.write("parameters: []\n")
            f.write("steps: []\n")

    _logger = logger
    return logger

def log_step(step_name: str, details: Optional[dict] = None) -> None:
    """
    Logs a processing step to the console/file logger and appends to the YAML log.
    """
    logger = get_logger()
    logger.info(f"--- START STEP: {step_name} ---")
    if details:
        for k, v in details.items():
            logger.info(f"  {k}: {v}")

    # Append to YAML file
    yaml_path = DATA_DIR / "preprocessing.yaml"
    timestamp = datetime.now().isoformat()
    
    # Simple YAML append logic to avoid complex parsing of existing file
    # We assume the file structure is:
    # steps:
    #   - name: ...
    #     timestamp: ...
    #     details: ...
    
    # To ensure valid YAML, we read, parse (if possible), append, and write back
    # Since we can't import yaml here to avoid circular dependencies if not installed yet,
    # we will use a simple text append strategy that maintains the list structure
    # OR better: use the yaml library if available (it is in requirements)
    try:
        import yaml
        with open(yaml_path, 'r') as f:
            try:
                data = yaml.safe_load(f) or {"steps": [], "parameters": []}
            except yaml.YAMLError:
                data = {"steps": [], "parameters": []}
        
        if "steps" not in data:
            data["steps"] = []
        
        step_entry = {
            "name": step_name,
            "timestamp": timestamp,
            "details": details or {}
        }
        data["steps"].append(step_entry)
        
        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        # Fallback if yaml is not installed (should not happen based on requirements)
        logger.warning("PyYAML not found. Skipping YAML log update.")
    except Exception as e:
        logger.error(f"Failed to update YAML log: {e}")

def log_preprocessing_parameter(key: str, value: any, description: Optional[str] = None) -> None:
    """
    Logs a specific preprocessing parameter to the YAML log.
    """
    logger = get_logger()
    logger.debug(f"Parameter: {key} = {value}")

    yaml_path = DATA_DIR / "preprocessing.yaml"
    timestamp = datetime.now().isoformat()

    try:
        import yaml
        with open(yaml_path, 'r') as f:
            try:
                data = yaml.safe_load(f) or {"parameters": []}
            except yaml.YAMLError:
                data = {"parameters": []}

        if "parameters" not in data:
            data["parameters"] = []

        param_entry = {
            "key": key,
            "value": value,
            "timestamp": timestamp,
            "description": description
        }
        data["parameters"].append(param_entry)

        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        logger.warning("PyYAML not found. Skipping YAML parameter log.")
    except Exception as e:
        logger.error(f"Failed to update YAML parameter log: {e}")

def log_artifact(artifact_name: str, path: str, artifact_type: str = "file") -> None:
    """
    Logs the creation of an artifact to the YAML log.
    """
    logger = get_logger()
    logger.info(f"Artifact Created: {artifact_name} ({path})")

    yaml_path = DATA_DIR / "preprocessing.yaml"
    timestamp = datetime.now().isoformat()

    try:
        import yaml
        with open(yaml_path, 'r') as f:
            try:
                data = yaml.safe_load(f) or {"artifacts": []}
            except yaml.YAMLError:
                data = {"artifacts": []}

        if "artifacts" not in data:
            data["artifacts"] = []

        artifact_entry = {
            "name": artifact_name,
            "path": path,
            "type": artifact_type,
            "timestamp": timestamp
        }
        data["artifacts"].append(artifact_entry)

        with open(yaml_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except ImportError:
        logger.warning("PyYAML not found. Skipping YAML artifact log.")
    except Exception as e:
        logger.error(f"Failed to update YAML artifact log: {e}")
