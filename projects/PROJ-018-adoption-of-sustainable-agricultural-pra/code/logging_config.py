"""
Logging infrastructure for the llmXive sustainable agriculture project.
Configures a structured logger that writes to both console and a log file,
and manages the initialization of `modeling_log.yaml`.
"""
import logging
import os
import yaml
from datetime import datetime
from typing import Any, Dict, Optional

# Ensure the data directory exists
DATA_DIR = "data"
LOG_FILE_PATH = os.path.join(DATA_DIR, "modeling_log.yaml")

# Ensure the directory exists before setting up logging
os.makedirs(DATA_DIR, exist_ok=True)


def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Configures and returns a logger instance.
    Creates the log file handler if it doesn't exist.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers if they already exist (prevents duplicate logs)
    if logger.handlers:
        return logger

    # Formatter for console and file
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Text log for human readability)
    log_txt_path = os.path.join(DATA_DIR, "pipeline.log")
    file_handler = logging.FileHandler(log_txt_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def initialize_modeling_log() -> Dict[str, Any]:
    """
    Initializes or loads the `modeling_log.yaml` file.
    Ensures the file exists with a standard structure if it's new.
    Returns the current log dictionary.
    """
    if not os.path.exists(LOG_FILE_PATH):
        initial_structure = {
            "project_id": "PROJ-018-adoption-of-sustainable-agricultural-pra",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "log_entries": [],
            "power_analysis": {},
            "convergent_validity_status": None,
            "model_config": {},
            "data_provenance": {},
            "limitations": []
        }
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(initial_structure, f, default_flow_style=False, sort_keys=False)
        return initial_structure

    with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def append_log_entry(
    key: str,
    value: Any,
    logger: Optional[logging.Logger] = None,
    log_level: str = "INFO"
) -> None:
    """
    Appends an entry to the `modeling_log.yaml` file under a specific key
    or appends to the `log_entries` list if key is None.
    Also logs to the standard logger.
    """
    if logger is None:
        logger = get_logger()

    log_method = getattr(logger, log_level.lower(), logger.info)
    log_method(f"Updating modeling_log.yaml: {key} = {value}")

    log_data = initialize_modeling_log()

    if key is None:
        # Append to general log entries
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": str(value)
        }
        log_data.setdefault("log_entries", []).append(entry)
    else:
        # Update specific key (nested or top-level)
        # For simple top-level keys, we overwrite or append if it's a list
        if key in log_data and isinstance(log_data[key], list):
            log_data[key].append(value)
        else:
            log_data[key] = value

    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)


def update_log_section(section: str, updates: Dict[str, Any]) -> None:
    """
    Updates a specific section of the modeling_log.yaml (e.g., 'power_analysis', 'model_config').
    """
    logger = get_logger()
    logger.info(f"Updating section '{section}' in modeling_log.yaml")

    log_data = initialize_modeling_log()
    current_section = log_data.get(section, {})

    # Deep update logic for nested dictionaries
    for k, v in updates.items():
        if isinstance(v, dict) and k in current_section and isinstance(current_section[k], dict):
            current_section[k].update(v)
        else:
            current_section[k] = v

    log_data[section] = current_section

    with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(log_data, f, default_flow_style=False, sort_keys=False)
