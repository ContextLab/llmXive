"""
Task T012c: Generate Exclusion Log
Reads exclusion counts from data/processed/exclusion_counts.json and writes
a consolidated exclusion log to data/processed/exclusion_log.json.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging using the project's standard utility
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp

def load_exclusion_counts(file_path: Path) -> Dict[str, int]:
    """
    Load the exclusion counts dictionary from a JSON file.
    If the file does not exist or is empty, return a default structure with zeros.
    """
    if not file_path.exists():
        log_warning(f"Exclusion counts file not found: {file_path}. Starting with empty counts.")
        return {
            "ERR_MISSING_AGE_FIELD": 0,
            "ERR_MISSING_SCORE": 0,
            "ERR_MMSE_IMPAIRED": 0,
            "SIMULATION_FALLBACK": 0
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                log_error(f"Exclusion counts file {file_path} is not a valid JSON object.")
                return {}
            return data
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse exclusion counts JSON: {e}")
        return {}
    except Exception as e:
        log_error(f"Unexpected error reading exclusion counts: {e}")
        return {}

def generate_exclusion_log(counts: Dict[str, int], output_path: Path) -> None:
    """
    Ensure all required keys are present in the counts dictionary,
    defaulting missing ones to 0, then write the final log.
    """
    required_keys = [
        "ERR_MISSING_AGE_FIELD",
        "ERR_MISSING_SCORE",
        "ERR_MMSE_IMPAIRED",
        "SIMULATION_FALLBACK"
    ]
    
    final_log = {}
    for key in required_keys:
        final_log[key] = counts.get(key, 0)
    
    # Add metadata for traceability
    final_log["_generated_at"] = get_timestamp()
    final_log["_source_file"] = str(output_path.parent / "exclusion_counts.json")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_log, f, indent=2)
        log_info(f"Exclusion log successfully written to: {output_path}")
    except Exception as e:
        log_error(f"Failed to write exclusion log: {e}")
        raise

def main():
    setup_logging()
    log_info("Starting T012c: Generate Exclusion Log")
    
    # Define paths relative to project root
    # Assuming this script is run from the project root or code directory
    # We use relative paths as per project convention
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    exclusion_counts_path = project_root / "data" / "processed" / "exclusion_counts.json"
    exclusion_log_path = project_root / "data" / "processed" / "exclusion_log.json"
    
    # Ensure output directory exists
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing counts
    counts = load_exclusion_counts(exclusion_counts_path)
    
    # Generate and save the log
    generate_exclusion_log(counts, exclusion_log_path)
    
    log_info("T012c completed successfully.")

if __name__ == "__main__":
    main()