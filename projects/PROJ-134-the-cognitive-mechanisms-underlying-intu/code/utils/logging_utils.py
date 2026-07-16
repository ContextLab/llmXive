"""
Base logging infrastructure for the cognitive mechanisms project.
Captures exclusion reasons, VR mapping logs, and general pipeline steps.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
import json

from code.config import ensure_directories


class LogType:
    """Constants for log categories."""
    EXCLUSION = "exclusion"
    VR_MAPPING = "vr_mapping"
    PIPELINE_STEP = "pipeline_step"
    ERROR = "error"


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with standard configuration.

    Args:
        name: The name of the logger (typically __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    log_dir = Path("data/logs")
    ensure_directories([log_dir])

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # File handler (general)
    log_file = log_dir / f"{name}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_log_path(log_type: str, category: Optional[str] = None) -> Path:
    """
    Generate the file path for a specific log type.

    Args:
        log_type: Type of log (exclusion, vr_mapping, pipeline_step).
        category: Optional sub-category for organization.

    Returns:
        Path object for the log file.
    """
    ensure_directories([Path("data/logs")])
    log_dir = Path("data/logs")

    if category:
        filename = f"{log_type}_{category}.log"
    else:
        filename = f"{log_type}.log"

    return log_dir / filename


def log_exclusion(record_id: str, reason: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exclusion reason for a specific record.

    Args:
        record_id: Unique identifier of the excluded record.
        reason: Human-readable reason for exclusion.
        context: Optional dictionary of additional context (e.g., validation errors).
    """
    logger = get_logger("exclusions")
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "record_id": record_id,
        "reason": reason,
        "context": context or {}
    }

    logger.warning(json.dumps(entry))

    # Also append to structured exclusion log file
    log_path = get_log_path("exclusion")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_vr_mapping(
    story_id: str,
    vr_scene_id: str,
    salience_level: str,
    blend_shapes: Dict[str, float],
    mapping_confidence: float
) -> None:
    """
    Log the mapping of a story to a VR scene with salience details.

    Args:
        story_id: Identifier of the source story.
        vr_scene_id: Identifier of the mapped VR scene.
        salience_level: Assigned salience level (e.g., 'low', 'high').
        blend_shapes: Dictionary of blend-shape parameters used.
        mapping_confidence: Confidence score of the mapping (0.0 to 1.0).
    """
    logger = get_logger("vr_mapping")
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "story_id": story_id,
        "vr_scene_id": vr_scene_id,
        "salience_level": salience_level,
        "blend_shapes": blend_shapes,
        "mapping_confidence": mapping_confidence
    }

    logger.info(json.dumps(entry))

    # Append to structured VR mapping log
    log_path = get_log_path("vr_mapping")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_pipeline_step(
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a general pipeline execution step.

    Args:
        step_name: Name of the pipeline step.
        status: Status of the step (STARTED, COMPLETED, FAILED).
        details: Optional dictionary of step-specific details (duration, counts, etc.).
    """
    logger = get_logger("pipeline")
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "step_name": step_name,
        "status": status,
        "details": details or {}
    }

    level = logging.INFO if status == "COMPLETED" else (
        logging.WARNING if status == "FAILED" else logging.DEBUG
    )
    logger.log(level, json.dumps(entry))


def get_exclusion_log_path() -> Path:
    """Return the path to the exclusion log file."""
    return get_log_path("exclusion")


def get_vr_mapping_log_path() -> Path:
    """Return the path to the VR mapping log file."""
    return get_log_path("vr_mapping")
