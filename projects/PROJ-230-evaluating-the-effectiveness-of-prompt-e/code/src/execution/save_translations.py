import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from src.utils.logging import get_logger, log_raw_output

logger = get_logger(__name__)

def ensure_output_dirs(base_path: Path) -> None:
    """
    Ensures that the base output directory and subdirectories for each
    prompt condition exist.
    
    Args:
        base_path: The root directory for saving translations 
                   (e.g., data/evaluation/raw_translations)
    """
    base_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories exist at {base_path}")

def save_translation(
    base_path: Path,
    condition_name: str,
  entry_id: str,
    python_code: str,
    javascript_output: str,
    seed: int,
    prompt_text: str,
    model_version: str,
    timestamp: str
) -> None:
    """
    Saves a single translation result to a JSON file organized by condition.
    
    This implements the storage requirement for T023:
    "Implement output storage to `data/evaluation/raw_translations/` 
    organized by condition directory".
    
    Args:
        base_path: Root directory for raw translations (data/evaluation/raw_translations)
        condition_name: The prompt condition identifier (e.g., 'zero_shot_basic')
        entry_id: Unique identifier for the source code pair
        python_code: The original Python code
        javascript_output: The generated JavaScript translation
        seed: The random seed used for this generation
        prompt_text: The exact prompt sent to the LLM
        model_version: The model version used
        timestamp: ISO timestamp of the generation
    """
    # Create condition-specific directory
    condition_dir = base_path / condition_name
    condition_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize entry_id for filename safety (basic replacement)
    safe_id = entry_id.replace("/", "_").replace("\\", "_")
    filename = f"{safe_id}.json"
    file_path = condition_dir / filename
    
    # Construct the record
    record = {
        "input_id": entry_id,
        "condition": condition_name,
        "python_code": python_code,
        "javascript_output": javascript_output,
        "metadata": {
            "seed": seed,
            "model_version": model_version,
            "timestamp": timestamp,
            "prompt_text": prompt_text
        }
    }
    
    # Write to disk
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved translation to {file_path}")
    except IOError as e:
        logger.error(f"Failed to save translation to {file_path}: {e}")
        raise