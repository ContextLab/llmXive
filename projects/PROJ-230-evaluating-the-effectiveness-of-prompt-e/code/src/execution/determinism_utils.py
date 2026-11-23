import os
import sys
import json
import random
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

def set_deterministic_seed(seed: int = 42) -> int:
    """
    Sets the random seed for Python's random module to ensure reproducibility.
    
    Args:
        seed: The integer seed value to use.
    
    Returns:
        The seed value that was set.
    """
    random.seed(seed)
    logger.info(f"Deterministic seed set to: {seed}")
    return seed

def log_determinism_metadata(
    prompt_condition: str,
    model_version: str,
    seed: int,
    input_id: str,
    prompt_text: str,
    output_path: Path
) -> None:
    """
    Logs the exact metadata required for deterministic execution tracking.
    
    Args:
        prompt_condition: The name of the prompt condition used (e.g., 'zero_shot_basic').
        model_version: The specific model version identifier.
        seed: The random seed used for this request.
        input_id: Unique identifier for the input data entry.
        prompt_text: The exact prompt text sent to the model.
        output_path: Path to the output file where the translation is stored.
    """
    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt_condition": prompt_condition,
        "model_version": model_version,
        "seed": seed,
        "input_id": input_id,
        "prompt_text": prompt_text,
        "output_file": str(output_path)
    }
    
    # Log as a structured JSON line for easy parsing
    logger.info(f"DETERMINISM_METADATA: {json.dumps(metadata)}")
    
    # Also write to a dedicated log file for this run if needed
    # This ensures we have a persistent record even if stdout is lost
    log_file = output_path.parent / "determinism_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata) + "\n")

def save_determinism_log(log_entries: list, output_path: Path) -> None:
    """
    Saves a batch of determinism log entries to a JSON file.
    
    Args:
        log_entries: List of dictionaries containing metadata for each request.
        output_path: Path to the output JSON file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(log_entries, f, indent=2)
    logger.info(f"Saved determinism log to {output_path}")

def generate_determinism_report(log_file_path: Path, output_report_path: Path) -> None:
    """
    Generates a summary report of determinism metadata from a log file.
    
    Args:
        log_file_path: Path to the JSONL log file containing metadata.
        output_report_path: Path where the summary report will be saved.
    """
    if not log_file_path.exists():
        logger.warning(f"Determinism log file not found: {log_file_path}")
        return

    entries = []
    with open(log_file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    summary = {
        "total_requests": len(entries),
        "unique_seeds": list(set(e["seed"] for e in entries)),
        "unique_conditions": list(set(e["prompt_condition"] for e in entries)),
        "model_versions": list(set(e["model_version"] for e in entries)),
        "first_request": entries[0]["timestamp"] if entries else None,
        "last_request": entries[-1]["timestamp"] if entries else None
    }

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Generated determinism report at {output_report_path}")

def main():
    """
    Main entry point for testing the determinism utilities.
    """
    # Example usage
    seed = set_deterministic_seed(12345)
    
    # Simulate a log entry
    log_determinism_metadata(
        prompt_condition="zero_shot_basic",
        model_version="CodeLlama-7B-v1",
        seed=seed,
        input_id="entry_001",
        prompt_text="Translate the following Python code to JavaScript: ...",
        output_path=Path("data/evaluation/raw_translations/zero_shot_basic/entry_001.js")
    )
    
    # Generate a report
    log_file = Path("data/evaluation/raw_translations/determinism_log.jsonl")
    report_path = Path("data/evaluation/determinism_report.json")
    generate_determinism_report(log_file, report_path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()