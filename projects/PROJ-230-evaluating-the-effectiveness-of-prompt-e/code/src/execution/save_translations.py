"""
Implementation of T023: Output storage for translation results.

This module handles the storage of generated JavaScript translations into
`data/evaluation/raw_translations/`, organized by prompt condition directory.
It ensures deterministic file naming and logs the storage operation.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Import logging utility from the project's existing API surface
from src.utils.logging import get_logger, log_raw_output

# Ensure the logger is configured
logger = get_logger(__name__)

def ensure_output_dirs(base_path: Path) -> None:
    """
    Ensure the base output directory and condition subdirectories exist.
    
    Args:
        base_path: The base path for evaluation outputs (e.g., data/evaluation/raw_translations)
    """
    base_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {base_path}")

def save_translation(
    condition: str,
    entry_id: str,
    translated_code: str,
    base_path: Path,
    prompt_text: str,
    seed: int,
    timestamp: str
) -> Path:
    """
    Save a single translation result to disk.
    
    The file is saved as a JSON object containing the metadata and the raw output.
    The file path is: {base_path}/{condition}/{entry_id}.json
    
    Args:
        condition: The prompt condition string (e.g., 'zero_shot_basic')
        entry_id: Unique identifier for the source code entry
        translated_code: The generated JavaScript code string
        base_path: The root directory for evaluation outputs
        prompt_text: The exact prompt text used for generation
        seed: The random seed used for generation
        timestamp: The timestamp of the generation
        
    Returns:
        Path: The absolute path to the saved JSON file
        
    Raises:
        IOError: If writing the file fails
    """
    condition_dir = base_path / condition
    condition_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a structured output file
    output_data = {
        "entry_id": entry_id,
        "condition": condition,
        "seed": seed,
        "timestamp": timestamp,
        "prompt": prompt_text,
        "raw_output": translated_code,
        "status": "success"
    }
    
    output_file = condition_dir / f"{entry_id}.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved translation for {entry_id} ({condition}) to {output_file}")
        
        # Log the raw output using the project's logging utility
        log_raw_output(
            artifact_type="translation",
            entry_id=entry_id,
            condition=condition,
            content=translated_code,
            logger=logger
        )
        
        return output_file
    except IOError as e:
        logger.error(f"Failed to save translation for {entry_id}: {e}")
        raise

def main():
    """
    Entry point for the module.
    This script is typically called by run_inference.py after generation,
    but can be run standalone to verify directory structure.
    """
    logger.info("T023: Output storage module loaded successfully.")
    base_path = Path("data/evaluation/raw_translations")
    ensure_output_dirs(base_path)
    logger.info(f"Ready to store translations in: {base_path}")

if __name__ == "__main__":
    main()
