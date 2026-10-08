"""
Counterbalancing Module (T014)

Assigns every stimulus to both relationship contexts ("friend" and "acquaintance")
for every participant.

Output: data/processed/counterbalanced_trials.csv
"""
import csv
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from project config and logging
from config import get_processed_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger

# Initialize logger
setup_logging()
logger = get_logger(__name__)

# Constants
RELATIONSHIPS = ["friend", "acquaintance"]

def load_stimuli(stimuli_path: Path) -> List[Dict[str, Any]]:
    """
    Load stimuli from the raw data CSV.

    Args:
        stimuli_path: Path to data/raw/stimuli.csv

    Returns:
        List of dictionaries representing stimuli rows.
    """
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}")

    stimuli = []
    with open(stimuli_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)

    logger.info(f"Loaded {len(stimuli)} stimuli from {stimuli_path}")
    return stimuli

def generate_participant_ids(count: int, seed: int = 42) -> List[str]:
    """
    Generate a list of synthetic participant IDs for the counterbalancing step.
    In a real deployment, these would come from the recruitment list, but for
    this step, we generate deterministic IDs based on the seed.

    Args:
        count: Number of participant IDs to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of participant ID strings (e.g., "P000001").
    """
    random.seed(seed)
    # Using a simple format P followed by 6 digits
    return [f"P{str(i).zfill(6)}" for i in range(1, count + 1)]

def create_counterbalanced_trials(
    stimuli: List[Dict[str, Any]], participant_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Create the counterbalanced trial list.
    Every stimulus is paired with every relationship context for every participant.

    Args:
        stimuli: List of stimulus dictionaries.
        participant_ids: List of participant ID strings.

    Returns:
        List of trial dictionaries containing stimulus and participant info.
    """
    trials = []
    trial_id = 1

    for pid in participant_ids:
        for stimulus in stimuli:
            for relationship in RELATIONSHIPS:
                trial = {
                    "trial_id": f"T{str(trial_id).zfill(6)}",
                    "participant_id": pid,
                    "stimulus_id": stimulus.get("stimulus_id"),
                    "relationship_type": relationship,
                    "stimulus_text": stimulus.get("text"),
                    "emoji_count": stimulus.get("emoji_count"),
                    "punctuation_type": stimulus.get("punctuation_type"),
                    "length_category": stimulus.get("length_category"),
                    "scenario_id": stimulus.get("scenario_id"),
                    "cue_intensity": stimulus.get("cue_intensity"),
                }
                trials.append(trial)
                trial_id += 1

    logger.info(
        f"Created {len(trials)} counterbalanced trials "
        f"({len(participant_ids)} participants x {len(stimuli)} stimuli x {len(RELATIONSHIPS)} contexts)"
    )
    return trials

def save_counterbalanced_trials(trials: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the counterbalanced trials to a CSV file.

    Args:
        trials: List of trial dictionaries.
        output_path: Path to save the CSV file.
    """
    if not trials:
        raise ValueError("No trials to save.")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "trial_id",
        "participant_id",
        "stimulus_id",
        "relationship_type",
        "stimulus_text",
        "emoji_count",
        "punctuation_type",
        "length_category",
        "scenario_id",
        "cue_intensity",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(trials)

    logger.info(f"Saved {len(trials)} trials to {output_path}")

def verify_counterbalancing(trials: List[Dict[str, Any]], stimuli_count: int, participants_count: int) -> bool:
    """
    Verify that the counterbalancing is correct.
    Expected row count = participants_count * stimuli_count * 2 (relationships).

    Args:
        trials: List of trial dictionaries.
        stimuli_count: Number of unique stimuli.
        participants_count: Number of unique participants.

    Returns:
        True if verification passes, False otherwise.
    """
    expected_count = participants_count * stimuli_count * len(RELATIONSHIPS)
    actual_count = len(trials)

    if actual_count != expected_count:
        logger.error(
            f"Verification failed: Expected {expected_count} rows, got {actual_count}"
        )
        return False

    # Check that every participant has every stimulus in both contexts
    unique_participants = set(t["participant_id"] for t in trials)
    unique_stimuli = set(t["stimulus_id"] for t in trials)

    if len(unique_participants) != participants_count:
        logger.error(f"Participant count mismatch: expected {participants_count}, got {len(unique_participants)}")
        return False

    if len(unique_stimuli) != stimuli_count:
        logger.error(f"Stimuli count mismatch: expected {stimuli_count}, got {len(unique_stimuli)}")
        return False

    # Check relationship coverage per participant-stimulus pair
    pairs = {}
    for t in trials:
        key = (t["participant_id"], t["stimulus_id"])
        if key not in pairs:
            pairs[key] = set()
        pairs[key].add(t["relationship_type"])

    for key, rels in pairs.items():
        if set(RELATIONSHIPS) != rels:
            logger.error(f"Missing relationship context for pair {key}: found {rels}")
            return False

    logger.info("Counterbalancing verification passed.")
    return True

def main() -> int:
    """
    Main entry point for the counterbalancing script.
    """
    # Define paths
    raw_data_dir = get_raw_data_dir()
    processed_data_dir = get_processed_data_dir()

    stimuli_path = raw_data_dir / "stimuli.csv"
    output_path = processed_data_dir / "counterbalanced_trials.csv"

    logger.info("Starting counterbalancing process...")

    # Load stimuli
    try:
        stimuli = load_stimuli(stimuli_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    if not stimuli:
        logger.error("No stimuli found. Cannot proceed with counterbalancing.")
        return 1

    # Determine number of participants
    # For this task, we assume a standard number (e.g., 60) as per power analysis
    # In a real pipeline, this might be read from a config or power analysis result.
    # We use a fixed seed for reproducibility as per config.py
    try:
        from config import RANDOM_SEED
    except ImportError:
        RANDOM_SEED = 42

    # Assuming N=60 based on power analysis T091
    n_participants = 60
    participant_ids = generate_participant_ids(n_participants, seed=RANDOM_SEED)

    # Create counterbalanced trials
    trials = create_counterbalanced_trials(stimuli, participant_ids)

    # Verify
    if not verify_counterbalancing(trials, len(stimuli), len(participant_ids)):
        logger.error("Counterbalancing verification failed.")
        return 1

    # Save
    try:
        save_counterbalanced_trials(trials, output_path)
    except Exception as e:
        logger.error(f"Failed to save counterbalanced trials: {e}")
        return 1

    logger.info("Counterbalancing completed successfully.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
