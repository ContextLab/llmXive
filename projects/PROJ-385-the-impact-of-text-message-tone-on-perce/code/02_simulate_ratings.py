"""
Mock Prolific Data Collection Simulation.

Generates synthetic human ratings for text message stimuli to validate the pipeline
in 'Simulation Mode'. This script enforces the target_N constraint derived from
the power analysis (T009) and simulates Prolific ID formats.

Output:
    data/raw/ratings.csv: Participant ratings with P-IDs, stimulus IDs, relationship context, and Likert scores.
"""
import csv
import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config utilities to resolve paths
try:
    from config import get_raw_data_dir, get_processed_data_dir, get_project_root
except ImportError:
    # Fallback for direct execution or different import context
    from pathlib import Path
    import sys
    # Add parent to path if running directly
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_raw_data_dir, get_processed_data_dir, get_project_root


def load_power_analysis_results() -> Dict[str, Any]:
    """
    Loads the power analysis results to determine the target number of participants.

    Returns:
        Dict containing 'target_N' and other power analysis metrics.

    Raises:
        FileNotFoundError: If the power analysis results file does not exist.
        KeyError: If 'target_N' is missing from the results.
    """
    processed_dir = get_processed_data_dir()
    file_path = processed_dir / "power_analysis_results.json"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Power analysis results not found at {file_path}. "
            "Ensure T009 (Power Analysis) has been completed successfully."
        )

    with open(file_path, 'r') as f:
        data = json.load(f)

    if 'target_N' not in data:
        raise KeyError(
            f"'target_N' key missing in {file_path}. "
            "The power analysis output does not contain the required participant count."
        )

    return data


def generate_prolific_id() -> str:
    """
    Generates a mock Prolific ID in the standard format (e.g., 'a1b2c3d4').

    Returns:
        str: A mock Prolific ID.
    """
    # Prolific IDs are typically 8 hexadecimal characters
    return ''.join(random.choices('0123456789abcdef', k=8))


def validate_prolific_id(pid: str) -> bool:
    """
    Validates the format of a Prolific ID.

    Args:
        pid: The ID string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    # Standard Prolific ID is 8 hex characters
    pattern = r'^[0-9a-f]{8}$'
    return bool(re.match(pattern, pid))


def simulate_rating(stimulus_id: str, participant_id: str, relationship: str) -> int:
    """
    Simulates a Likert scale rating (1-7) for a given stimulus and participant.

    In a real study, this would be human input. Here, we simulate a distribution
    that might show slight effects based on relationship or random noise,
    but primarily serves to fill the dataset structure.

    Args:
        stimulus_id: The ID of the stimulus being rated.
        participant_id: The ID of the participant.
        relationship: The relationship context ('friend' or 'acquaintance').

    Returns:
        int: A rating between 1 and 7.
    """
    # Base random rating
    base_rating = random.randint(1, 7)

    # Add slight bias based on relationship for simulation realism
    # (Friends might rate slightly higher on average in this mock)
    if relationship == 'friend':
        # Slight upward bias, clamped to 1-7
        adjusted = base_rating + random.choice([-1, 0, 0, 1])
    else:
        adjusted = base_rating

    return max(1, min(7, adjusted))


def log_randomization(participant_id: str, relationship: str) -> None:
    """
    Logs the randomization of relationship context for a participant.

    In a real study, this ensures the relationship context was randomized.
    Here, we just record the assignment for the audit log (optional, but good practice).

    Args:
        participant_id: The ID of the participant.
        relationship: The assigned relationship context.
    """
    # In a full implementation, this might write to a specific randomization log.
    # For now, we assume the assignment in the ratings CSV is sufficient for the mock.
    pass


def load_stimuli() -> List[Dict[str, Any]]:
    """
    Loads the list of generated stimuli from the raw data directory.

    Returns:
        List of dictionaries representing stimuli.

    Raises:
        FileNotFoundError: If stimuli.csv is not found.
    """
    raw_dir = get_raw_data_dir()
    file_path = raw_dir / "stimuli.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Stimuli file not found at {file_path}. "
            "Ensure T013 (Stimulus Generation) has been completed successfully."
        )

    stimuli = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)

    return stimuli


def generate_ratings(target_n: int, stimuli: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates the full dataset of ratings.

    Each participant rates ALL stimuli. The total number of participants
    is determined by target_n.

    Args:
        target_n: The required number of unique participants.
        stimuli: List of stimulus dictionaries.

    Returns:
        List of rating records.
    """
    if len(stimuli) == 0:
        raise ValueError("No stimuli found to rate. T013 must be completed first.")

    ratings = []
    used_pids = set()

    # Generate unique PIDs
    attempts = 0
    while len(used_pids) < target_n and attempts < target_n * 100:
        pid = generate_prolific_id()
        if pid not in used_pids:
            used_pids.add(pid)
        attempts += 1

    if len(used_pids) < target_n:
        raise RuntimeError(
            f"Failed to generate {target_n} unique Prolific IDs after {attempts} attempts. "
            "This is unlikely but indicates a collision issue in the generator."
        )

    relationship_choices = ['friend', 'acquaintance']

    for pid in used_pids:
        # Randomize relationship context for this participant
        relationship = random.choice(relationship_choices)
        log_randomization(pid, relationship)

        for stimulus in stimuli:
            stimulus_id = stimulus['id']
            rating = simulate_rating(stimulus_id, pid, relationship)

            ratings.append({
                'participant_id': pid,
                'stimulus_id': stimulus_id,
                'relationship': relationship,
                'rating': rating
            })

    return ratings


def save_ratings(ratings: List[Dict[str, Any]]) -> str:
    """
    Saves the generated ratings to the raw data directory.

    Args:
        ratings: List of rating dictionaries.

    Returns:
        str: Path to the saved file.
    """
    raw_dir = get_raw_data_dir()
    file_path = raw_dir / "ratings.csv"

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['participant_id', 'stimulus_id', 'relationship', 'rating']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ratings)

    return str(file_path)


def generate_mock_consent_log(participant_ids: List[str]) -> None:
    """
    Generates a log of mock consent for simulation mode.
    Note: Real consent records are NOT generated in simulation mode (T015c handles real data).
    This is just an internal log for the mock process.
    """
    # In simulation mode, we do not generate real consent records in data/consent/
    # as per Constitution Principle VI and the task distinction between T014 and T015.
    pass


def main():
    """
    Main entry point for the mock data collection script.

    1. Loads target_N from power analysis results.
    2. Loads stimuli from raw data.
    3. Generates ratings for all stimuli by target_N participants.
    4. Validates the count of participants matches target_N.
    5. Saves the ratings to data/raw/ratings.csv.
    """
    print("Starting Mock Prolific Data Collection (T014)...")

    # 1. Load Power Analysis Results
    try:
        power_results = load_power_analysis_results()
        target_n = power_results['target_N']
        print(f"Target number of participants (N) from power analysis: {target_n}")
    except (FileNotFoundError, KeyError) as e:
        print(f"ERROR: {e}")
        return

    # 2. Load Stimuli
    try:
        stimuli = load_stimuli()
        print(f"Loaded {len(stimuli)} stimuli.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    # 3. Generate Ratings
    print(f"Generating ratings for {target_n} participants across {len(stimuli)} stimuli...")
    ratings = generate_ratings(target_n, stimuli)

    # 4. Validate Participant Count
    unique_pids = set(r['participant_id'] for r in ratings)
    if len(unique_pids) != target_n:
        # This should theoretically not happen if generate_ratings works correctly,
        # but we enforce the requirement strictly.
        raise RuntimeError(
            f"Generated dataset has {len(unique_pids)} unique participants, "
            f"but target_N is {target_n}. This violates the power analysis constraint."
        )

    # 5. Save Ratings
    output_path = save_ratings(ratings)
    print(f"Successfully saved {len(ratings)} ratings to {output_path}")
    print(f"Unique participants: {len(unique_pids)}")
    print("Mock Prolific Data Collection (T014) completed successfully.")


if __name__ == '__main__':
    main()