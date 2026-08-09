import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import re
from utils.logging import get_logger

logger = get_logger(__name__)

def ensure_directory(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_file_exists(path: Union[str, Path]) -> bool:
    path = Path(path)
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    return True

def validate_file_not_empty(path: Union[str, Path]) -> bool:
    path = Path(path)
    if path.stat().st_size == 0:
        logger.error(f"File is empty: {path}")
        return False
    return True

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\. ]', '_', name)

def validate_json_file(path: Union[str, Path]) -> bool:
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
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML not installed")
        return False
    
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
    if not data:
        return False
    required_keys = ["step", "confidence", "candidate", "selected", "correct"]
    for item in data:
        if not all(k in item for k in required_keys):
            return False
    return True

def validate_run_metadata(data: Dict[str, Any]) -> bool:
    required_keys = ["run_id", "seed", "timestamp", "config"]
    return all(k in data for k in required_keys)

def validate_aggregated_metrics(data: List[Dict[str, Any]]) -> bool:
    if not data:
        return False
    required_keys = ["run_id", "aucc", "final_accuracy", "prompt_length"]
    for item in data:
        if not all(k in item for k in required_keys):
            return False
    return True

def validate_convergence_result(data: Dict[str, Any]) -> bool:
    required_keys = ["converged", "cycles_to_converge", "final_accuracy"]
    return all(k in data for k in required_keys)

def validate_batch(data: List[Dict[str, Any]]) -> bool:
    return len(data) > 0 and all(isinstance(item, dict) for item in data)
