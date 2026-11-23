import os
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import yaml
from utils.logging import get_logger

def ensure_directory(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def validate_file_exists(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

def validate_file_not_empty(path: str):
    if os.path.getsize(path) == 0:
        raise ValueError(f"File is empty: {path}")

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^\w\-_\.]', '_', name)

def validate_json_file(path: str):
    with open(path, 'r') as f:
        try:
            json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")

def validate_yaml_file(path: str):
    with open(path, 'r') as f:
        try:
            yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")

def validate_rollout_log(data: Dict[str, Any]) -> bool:
    required = ['task_id', 'cycle', 'student_confidence', 'expert_confidence', 'prompt_length', 'correct']
    return all(k in data for k in required)

def validate_run_metadata(data: Dict[str, Any]) -> bool:
    required = ['seed', 'timestamp', 'config_hash', 'mode']
    return all(k in data for k in required)

def validate_aggregated_metrics(data: Dict[str, Any]) -> bool:
    required = ['task_id', 'seed', 'aucc', 'final_accuracy', 'prompt_length_avg', 'run_mode']
    return all(k in data for k in required)

def validate_convergence_result(data: Dict[str, Any]) -> bool:
    required = ['cycle', 'accuracy', 'prompt_content']
    return all(k in data for k in required)

def validate_batch(data: List[Dict[str, Any]]) -> bool:
    if not data:
        return False
    return all(validate_aggregated_metrics(item) for item in data)
