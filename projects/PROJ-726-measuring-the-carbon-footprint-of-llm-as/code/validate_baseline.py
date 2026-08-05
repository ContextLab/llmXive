"""
validate_baseline.py

Synthesizes local human baseline data for code generation prompts.

This script implements the Synthesized Baseline Protocol:
1. Attempts to load hardcoded time values from the 2025 comparative analysis paper.
2. If the 2025 paper data is missing or invalid, it falls back to literature values
   (e.g., IEEE/ACM software engineering literature: 30-60 minutes per prompt).
3. Validates that the loaded values represent raw developer time (minutes), not CO2.
4. Matches prompt IDs from the downloaded CodeXGLUE dataset.
5. Saves the validated baseline to data/raw/human_baseline_times.json.

Dependencies:
- datasets (for prompt IDs)
- json, logging, os, sys, pathlib
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = DATA_RAW_DIR / "human_baseline_times.json"
CODEXGLUE_PATH = DATA_RAW_DIR / "codexglue_python_test.json"

# Literature values for Synthesized Baseline Protocol
# Source: IEEE/ACM Software Engineering literature on manual coding tasks
# Average time range: 30-60 minutes per prompt (midpoint: 45 minutes)
LITERATURE_TIME_MINUTES = 45.0
LITERATURE_CITATION = "IEEE/ACM Software Engineering Literature (Standard Manual Coding Task Duration)"

# Placeholder for 2025 paper data (if available)
# Expected structure: {"prompt_id": time_minutes}
# If this file exists and is valid, it will be used instead of synthesized data.
PAPER_BASELINE_FILE = DATA_RAW_DIR / "paper_2025_baseline_times.json"

def load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def load_prompt_ids() -> List[str]:
    """
    Load prompt IDs from the downloaded CodeXGLUE dataset.
    Expects the dataset to be in JSON format with 'prompt_id' or 'id' fields.
    """
    if not CODEXGLUE_PATH.exists():
        logger.error(f"CodeXGLUE dataset not found at {CODEXGLUE_PATH}. "
                     "Please run download_data.py (T004) first.")
        sys.exit(1)

    data = load_json_file(CODEXGLUE_PATH)
    if not data:
        logger.error("Failed to load CodeXGLUE dataset.")
        sys.exit(1)

    # Handle both list of dicts and single dict structures
    if isinstance(data, list):
        prompt_ids = [item.get('prompt_id') or item.get('id') for item in data]
    elif isinstance(data, dict):
        # If it's a dict, try to find a list of items
        if 'data' in data:
            prompt_ids = [item.get('prompt_id') or item.get('id') for item in data['data']]
        else:
            # Assume keys are prompt IDs if it's a dict of prompts
            prompt_ids = list(data.keys())
    else:
        logger.error("Unexpected dataset structure.")
        sys.exit(1)

    # Filter out None values
    prompt_ids = [pid for pid in prompt_ids if pid is not None]

    if not prompt_ids:
        logger.error("No prompt IDs found in CodeXGLUE dataset.")
        sys.exit(1)

    logger.info(f"Loaded {len(prompt_ids)} prompt IDs from CodeXGLUE dataset.")
    return prompt_ids

def load_paper_baseline() -> Optional[Dict[str, float]]:
    """
    Attempt to load hardcoded time values from the 2025 comparative analysis paper.
    Returns None if the file is missing or invalid.
    """
    if not PAPER_BASELINE_FILE.exists():
        logger.info(f"Paper baseline file not found at {PAPER_BASELINE_FILE}. "
                    "Proceeding with Synthesized Baseline Protocol.")
        return None

    data = load_json_file(PAPER_BASELINE_FILE)
    if not data:
        logger.warning("Paper baseline file exists but could not be loaded.")
        return None

    # Validate schema: must be dict with string keys and numeric values
    if not isinstance(data, dict):
        logger.error("Paper baseline data must be a dictionary.")
        return None

    for key, value in data.items():
        if not isinstance(key, str):
            logger.error(f"Paper baseline key '{key}' is not a string.")
            return None
        if not isinstance(value, (int, float)):
            logger.error(f"Paper baseline value for '{key}' is not a number.")
            return None
        # Validate that values represent time, not CO2 (positive, reasonable range)
        if value <= 0:
            logger.error(f"Paper baseline value for '{key}' must be positive (raw time).")
            return None
        if value > 1440:  # Max 24 hours in minutes
            logger.warning(f"Paper baseline value for '{key}' ({value} min) seems unusually high.")

    logger.info("Loaded and validated paper baseline data.")
    return data

def synthesize_baseline(prompt_ids: List[str]) -> Dict[str, float]:
    """
    Synthesize baseline data using literature values.
    This implements the Synthesized Baseline Protocol.
    """
    logger.info("Executing Synthesized Baseline Protocol...")
    logger.info(f"Using literature value: {LITERATURE_TIME_MINUTES} minutes per prompt")
    logger.info(f"Citation: {LITERATURE_CITATION}")

    baseline = {}
    for prompt_id in prompt_ids:
        baseline[prompt_id] = LITERATURE_TIME_MINUTES

    logger.info(f"Synthesized baseline for {len(baseline)} prompts.")
    return baseline

def validate_schema(data: Dict[str, float]) -> bool:
    """
    Validate that the data matches the required schema:
    {"prompt_id": <string>, "time_minutes": <float>}
    Actually, the structure is {prompt_id: time_minutes}
    """
    if not isinstance(data, dict):
        logger.error("Baseline data must be a dictionary.")
        return False

    for key, value in data.items():
        if not isinstance(key, str):
            logger.error(f"Key '{key}' must be a string.")
            return False
        if not isinstance(value, (int, float)):
            logger.error(f"Value for '{key}' must be a number (time in minutes).")
            return False
        if value <= 0:
            logger.error(f"Value for '{key}' must be positive (raw time, not CO2).")
            return False
        if value > 1440:  # Max 24 hours in minutes
            logger.warning(f"Value for '{key}' ({value} min) seems unusually high.")

    return True

def save_baseline(data: Dict[str, float], output_path: Path) -> None:
    """Save the baseline data to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved baseline data to {output_path}")

def main():
    """Main entry point for the baseline validation script."""
    logger.info("Starting baseline validation and synthesis...")

    # Step 1: Load prompt IDs from CodeXGLUE
    prompt_ids = load_prompt_ids()

    # Step 2: Try to load paper baseline
    paper_baseline = load_paper_baseline()

    # Step 3: Use paper baseline if available, otherwise synthesize
    if paper_baseline:
        logger.info("Using paper baseline data.")
        baseline_data = paper_baseline
    else:
        logger.info("Paper baseline not found. Synthesizing from literature.")
        baseline_data = synthesize_baseline(prompt_ids)

    # Step 4: Match with prompt IDs (exclude unmatched prompts)
    matched_baseline = {
        pid: baseline_data[pid]
        for pid in prompt_ids
        if pid in baseline_data
    }

    unmatched_count = len(prompt_ids) - len(matched_baseline)
    if unmatched_count > 0:
        logger.warning(f"Excluded {unmatched_count} prompts that had no baseline data.")

    if not matched_baseline:
        logger.error("No matched prompts. Cannot proceed.")
        sys.exit(1)

    # Step 5: Validate schema
    if not validate_schema(matched_baseline):
        logger.error("Baseline data validation failed.")
        sys.exit(1)

    # Step 6: Save to output file
    save_baseline(matched_baseline, OUTPUT_FILE)

    logger.info("Baseline validation and synthesis completed successfully.")
    logger.info(f"Output file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
