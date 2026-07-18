"""
Stimulus Generation and Prompt Recording Module.

Implements Principle VI: Reproducibility by recording the exact generation
prompts and parameters used to create AI-generated stimuli.

This module provides utilities to:
1. Log generation prompts to a structured JSON file.
2. Validate that required metadata fields are present.
3. Load previously recorded generation logs for audit/reproducibility.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from models import StimulusOrigin


# Default path for the generation log relative to project root
DEFAULT_LOG_PATH = "data/stimuli/generation_log.json"


class StimulusGenerationError(Exception):
    """Custom exception for errors during stimulus generation logging."""
    pass


def _ensure_log_file(log_path: Path) -> None:
    """
    Ensure the log file exists. If not, create it with an empty structure.
    """
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        initial_data = {
            "version": "1.0",
            "generated_at": datetime.utcnow().isoformat(),
            "entries": []
        }
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)


def _load_log(log_path: Path) -> Dict[str, Any]:
    """
    Load the generation log from disk.
    """
    if not log_path.exists():
        _ensure_log_file(log_path)
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise StimulusGenerationError(f"Failed to parse generation log: {e}")


def _save_log(log_path: Path, data: Dict[str, Any]) -> None:
    """
    Save the generation log to disk.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_generation_prompt(
    stimulus_id: str,
    prompt_text: str,
    model_name: str,
    parameters: Dict[str, Any],
    origin: str = "AI",
    log_path: Optional[str] = None
) -> str:
    """
    Record the generation prompt and parameters for an AI stimulus.

    This function fulfills Principle VI (Reproducibility) by ensuring that
    every AI-generated image can be traced back to its exact prompt and
    generation parameters.

    Args:
        stimulus_id: Unique identifier for the stimulus (must match ID in data).
        prompt_text: The exact text prompt used for generation.
        model_name: Name/version of the AI model used (e.g., 'stable-diffusion-xl').
        parameters: Dictionary of generation parameters (seed, steps, guidance_scale, etc.).
        origin: Origin type, defaults to 'AI'.
        log_path: Optional custom path for the log file. Defaults to DEFAULT_LOG_PATH.

    Returns:
        The unique record_id generated for this entry.

    Raises:
        StimulusGenerationError: If validation fails or file I/O errors occur.
    """
    if log_path is None:
        log_path = Path(DEFAULT_LOG_PATH)
    else:
        log_path = Path(log_path)

    # Validate inputs
    if not stimulus_id or not isinstance(stimulus_id, str):
        raise StimulusGenerationError("stimulus_id must be a non-empty string.")
    if not prompt_text or not isinstance(prompt_text, str):
        raise StimulusGenerationError("prompt_text must be a non-empty string.")
    if not model_name or not isinstance(model_name, str):
        raise StimulusGenerationError("model_name must be a non-empty string.")
    if not isinstance(parameters, dict):
        raise StimulusGenerationError("parameters must be a dictionary.")
    
    # Validate origin against enum if possible, or standard string
    if origin not in ["AI", "Human"]:
        # If it's not Human, it's assumed AI for this log, but we warn or enforce
        # strictly based on the task requirement. The task is about AI images.
        if origin != "AI":
            raise StimulusGenerationError(f"Invalid origin '{origin}' for generation log. Expected 'AI'.")

    record_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    entry = {
        "record_id": record_id,
        "stimulus_id": stimulus_id,
        "timestamp": timestamp,
        "origin": origin,
        "prompt": prompt_text,
        "model": model_name,
        "parameters": parameters
    }

    log_data = _load_log(log_path)
    
    # Update metadata timestamp
    log_data["generated_at"] = datetime.utcnow().isoformat()
    
    # Append entry
    log_data["entries"].append(entry)

    _save_log(log_path, log_data)

    return record_id


def get_generation_history(
    log_path: Optional[str] = None,
    stimulus_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve generation history, optionally filtered by stimulus_id.

    Args:
        log_path: Optional custom path for the log file.
        stimulus_id: If provided, return only entries matching this ID.

    Returns:
        List of generation entries.
    """
    if log_path is None:
        log_path = Path(DEFAULT_LOG_PATH)
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        return []

    log_data = _load_log(log_path)
    entries = log_data.get("entries", [])

    if stimulus_id:
        return [e for e in entries if e.get("stimulus_id") == stimulus_id]
    
    return entries


def validate_generation_log(log_path: Optional[str] = None) -> bool:
    """
    Validate that the generation log exists and contains required fields.

    Checks:
    1. File exists and is valid JSON.
    2. Contains 'entries' key.
    3. Each entry has 'stimulus_id', 'prompt', 'model', 'parameters'.

    Args:
        log_path: Optional custom path.

    Returns:
        True if valid, False otherwise.
    """
    if log_path is None:
        log_path = Path(DEFAULT_LOG_PATH)
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        return False

    try:
        log_data = _load_log(log_path)
    except StimulusGenerationError:
        return False

    if "entries" not in log_data:
        return False

    required_fields = ["stimulus_id", "prompt", "model", "parameters"]
    
    for entry in log_data["entries"]:
        for field in required_fields:
            if field not in entry:
                return False
            if field == "parameters" and not isinstance(entry[field], dict):
                return False
    
    return True


def main():
    """
    CLI entry point for testing the module.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Stimulus Generation Log Manager")
    parser.add_argument("--record", action="store_true", help="Record a sample entry")
    parser.add_argument("--list", action="store_true", help="List all entries")
    parser.add_argument("--validate", action="store_true", help="Validate log integrity")
    parser.add_argument("--path", type=str, default=DEFAULT_LOG_PATH, help="Path to log file")

    args = parser.parse_args()

    if args.record:
        try:
            record_id = record_generation_prompt(
                stimulus_id="test_stimulus_001",
                prompt="A photorealistic portrait of a young woman, natural lighting, 8k resolution",
                model_name="stable-diffusion-xl-1.0",
                parameters={"seed": 42, "steps": 30, "guidance_scale": 7.5}
            )
            print(f"Recorded entry with ID: {record_id}")
        except StimulusGenerationError as e:
            print(f"Error: {e}")

    if args.list:
        entries = get_generation_history(args.path)
        print(f"Found {len(entries)} entries:")
        for e in entries:
            print(f"  - {e['stimulus_id']}: {e['prompt'][:50]}...")

    if args.validate:
        is_valid = validate_generation_log(args.path)
        print(f"Log validation: {'PASSED' if is_valid else 'FAILED'}")


if __name__ == "__main__":
    main()