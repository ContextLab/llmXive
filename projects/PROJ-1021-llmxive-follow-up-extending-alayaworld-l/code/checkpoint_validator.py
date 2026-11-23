"""
T017b: Checkpoint Validation for User Story 1.

Verifies that data/baseline_scores.json contains exactly 100 entries
and adheres to the required schema:
{"scores": [{"seed": int, "score": float, "timestamp": string}], "total_entries": 100}
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Project root relative to this file (code/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BASELINE_FILE = DATA_DIR / "baseline_scores.json"

REQUIRED_SCHEMA_KEYS = {"scores", "total_entries"}
ENTRY_SCHEMA_KEYS = {"seed", "score", "timestamp"}

def validate_checkpoint() -> bool:
    """
    Validates the baseline scores file.
    Returns True if validation passes, False otherwise.
    Prints detailed error messages to stdout.
    """
    if not BASELINE_FILE.exists():
        print(f"ERROR: File not found: {BASELINE_FILE}")
        print("The baseline run (T017a) has not produced the expected output.")
        return False

    try:
        with open(BASELINE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {BASELINE_FILE}: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Failed to read {BASELINE_FILE}: {e}")
        return False

    # Check top-level keys
    if not isinstance(data, dict):
        print("ERROR: Root element must be a JSON object.")
        return False

    if not REQUIRED_SCHEMA_KEYS.issubset(data.keys()):
        missing = REQUIRED_SCHEMA_KEYS - set(data.keys())
        print(f"ERROR: Missing required top-level keys: {missing}")
        return False

    # Check total_entries
    total_entries = data.get("total_entries")
    if not isinstance(total_entries, int):
        print(f"ERROR: 'total_entries' must be an integer, got {type(total_entries).__name__}")
        return False

    if total_entries != 100:
        print(f"ERROR: 'total_entries' must be exactly 100, got {total_entries}")
        return False

    # Check scores list
    scores = data.get("scores")
    if not isinstance(scores, list):
        print(f"ERROR: 'scores' must be a list, got {type(scores).__name__}")
        return False

    if len(scores) != 100:
        print(f"ERROR: 'scores' list must contain exactly 100 entries, got {len(scores)}")
        return False

    # Validate each entry
    for i, entry in enumerate(scores):
        if not isinstance(entry, dict):
            print(f"ERROR: Entry at index {i} is not an object.")
            return False

        if not ENTRY_SCHEMA_KEYS.issubset(entry.keys()):
            missing_entry = ENTRY_SCHEMA_KEYS - set(entry.keys())
            print(f"ERROR: Entry at index {i} missing keys: {missing_entry}")
            return False

        seed = entry.get("seed")
        if not isinstance(seed, int):
            print(f"ERROR: Entry {i}: 'seed' must be an integer, got {type(seed).__name__}")
            return False

        score = entry.get("score")
        if not isinstance(score, (int, float)):
            print(f"ERROR: Entry {i}: 'score' must be a number, got {type(score).__name__}")
            return False

        timestamp = entry.get("timestamp")
        if not isinstance(timestamp, str):
            print(f"ERROR: Entry {i}: 'timestamp' must be a string, got {type(timestamp).__name__}")
            return False

    # If we reach here, all checks passed
    print(f"SUCCESS: Checkpoint validation passed.")
    print(f"  - File: {BASELINE_FILE}")
    print(f"  - Total entries: {total_entries}")
    print(f"  - Schema: Valid")
    return True

def main():
    success = validate_checkpoint()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
