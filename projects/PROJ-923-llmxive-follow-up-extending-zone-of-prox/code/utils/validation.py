import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import yaml
from utils.logging import get_logger

logger = get_logger(__name__)

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure the directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_file_exists(path: Union[str, Path]) -> bool:
    """Check if a file exists."""
    path = Path(path)
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    return True

def validate_file_not_empty(path: Union[str, Path]) -> bool:
    """Check if a file is not empty."""
    path = Path(path)
    if not path.exists():
        logger.error(f"File not found for size check: {path}")
        return False
    if path.stat().st_size == 0:
        logger.error(f"File is empty: {path}")
        return False
    return True

def sanitize_filename(name: str) -> str:
    """Remove or replace invalid characters in a filename."""
    return re.sub(r'[^\w\-_\. ]', '_', name)

def validate_json_file(path: Union[str, Path]) -> bool:
    """Validate that a file is valid JSON."""
    path = Path(path)
    if not validate_file_exists(path):
        return False
    try:
        with open(path, 'r') as f:
            json.load(f)
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        return False

def validate_yaml_file(path: Union[str, Path]) -> bool:
    """Validate that a file is valid YAML."""
    path = Path(path)
    if not validate_file_exists(path):
        return False
    try:
        with open(path, 'r') as f:
            yaml.safe_load(f)
        return True
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {path}: {e}")
        return False

def validate_rollout_log(data: List[Dict[str, Any]]) -> bool:
    """
    Validate rollout log data against the schema defined in contracts/rollout_log.schema.yaml.
    Checks for required fields: step, confidence, candidate, selected, correct.
    """
    if not data:
        logger.warning("Rollout log data is empty.")
        return False
    
    required_keys = {"step", "confidence", "candidate", "selected", "correct"}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.error(f"Item {i} in rollout log is not a dictionary.")
            return False
        missing_keys = required_keys - set(item.keys())
        if missing_keys:
            logger.error(f"Item {i} missing required keys: {missing_keys}")
            return False
    return True

def validate_run_metadata(data: Dict[str, Any]) -> bool:
    """
    Validate run metadata against the schema defined in contracts/run_metadata.schema.yaml.
    Checks for required fields: run_id, seed, timestamp, config.
    """
    if not isinstance(data, dict):
        logger.error("Run metadata is not a dictionary.")
        return False
        
    required_keys = {"run_id", "seed", "timestamp", "config"}
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        logger.error(f"Run metadata missing required keys: {missing_keys}")
        return False
    return True

def validate_aggregated_metrics(data: List[Dict[str, Any]]) -> bool:
    """
    Validate aggregated metrics against the schema defined in contracts/aggregated_metrics.schema.yaml.
    Checks for required fields: run_id, aucc, final_accuracy, prompt_length.
    """
    if not data:
        logger.warning("Aggregated metrics data is empty.")
        return False
        
    required_keys = {"run_id", "aucc", "final_accuracy", "prompt_length"}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.error(f"Item {i} in aggregated metrics is not a dictionary.")
            return False
        missing_keys = required_keys - set(item.keys())
        if missing_keys:
            logger.error(f"Item {i} missing required keys: {missing_keys}")
            return False
    return True

def validate_convergence_result(data: Dict[str, Any]) -> bool:
    """
    Validate convergence result against the schema defined in contracts/convergence_result.schema.yaml.
    Checks for required fields: converged, cycles_to_converge, final_accuracy.
    """
    if not isinstance(data, dict):
        logger.error("Convergence result is not a dictionary.")
        return False
        
    required_keys = {"converged", "cycles_to_converge", "final_accuracy"}
    missing_keys = required_keys - set(data.keys())
    if missing_keys:
        logger.error(f"Convergence result missing required keys: {missing_keys}")
        return False
    return True

def validate_batch(data: List[Dict[str, Any]]) -> bool:
    """
    Validate batch results data.
    Checks that data is a non-empty list of dictionaries.
    """
    if not isinstance(data, list):
        logger.error("Batch data is not a list.")
        return False
    if not data:
        logger.warning("Batch data is empty.")
        return False
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            logger.error(f"Item {i} in batch data is not a dictionary.")
            return False
    return True