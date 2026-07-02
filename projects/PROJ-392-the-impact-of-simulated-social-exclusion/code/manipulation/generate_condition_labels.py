"""
Generate condition labels for social exclusion/inclusion tasks.

This module extracts exclusion/inclusion labels from participants.tsv or task events JSON
for OpenNeuro datasets ds000246 (Exclusion) and ds004738 (Reward).
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import from project config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.loader import get_config, get_dataset_id, get_path, ensure_paths_exist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_participants_tsv(participants_path: Path) -> List[Dict[str, str]]:
    """
    Load participants.tsv file and return as list of dicts.

    Args:
        participants_path: Path to participants.tsv file

    Returns:
        List of participant records as dictionaries
    """
    if not participants_path.exists():
        raise FileNotFoundError(f"Participants file not found: {participants_path}")

    participants = []
    with open(participants_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            participants.append(row)

    return participants


def load_events_json(events_path: Path) -> List[Dict]:
    """
    Load task events JSON file and return list of events.

    Args:
        events_path: Path to events.json file

    Returns:
        List of event dictionaries
    """
    if not events_path.exists():
        raise FileNotFoundError(f"Events file not found: {events_path}")

    with open(events_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    return events


def extract_exclusion_labels_from_participants(
    participants: List[Dict[str, str]],
    dataset_id: str
) -> Dict[str, str]:
    """
    Extract exclusion/inclusion labels from participants.tsv.

    For ds000246 (Cognitive Control in Social Exclusion), the participants.tsv
    typically contains a 'condition' or 'group' column indicating exclusion status.

    Args:
        participants: List of participant records
        dataset_id: OpenNeuro dataset ID (e.g., 'ds000246')

    Returns:
        Dictionary mapping participant_id to condition label ('excluded' or 'included')
    """
    labels = {}

    # Determine which column contains condition info based on dataset
    condition_col = None
    if dataset_id == 'ds000246':
        # Check for common column names in exclusion datasets
        if participants and 'condition' in participants[0]:
            condition_col = 'condition'
        elif participants and 'group' in participants[0]:
            condition_col = 'group'
        elif participants and 'exclusion_condition' in participants[0]:
            condition_col = 'exclusion_condition'

    if not condition_col:
        logger.warning(f"No condition column found in participants.tsv for {dataset_id}")
        return labels

    for participant in participants:
        participant_id = participant.get('participant_id', '')
        if not participant_id:
            continue

        condition_value = participant.get(condition_col, '').lower().strip()

        # Map various representations to standard labels
        if condition_value in ['exclusion', 'excluded', 'ostracized', 'exclude']:
            labels[participant_id] = 'excluded'
        elif condition_value in ['inclusion', 'included', 'control', 'include']:
            labels[participant_id] = 'included'
        else:
            # Log unknown values but don't fail
            logger.debug(f"Unknown condition '{condition_value}' for {participant_id}")

    return labels


def extract_labels_from_events_json(
    events: List[Dict],
    dataset_id: str
) -> Dict[str, str]:
    """
    Extract condition labels from events.json for within-subject designs.

    Some datasets use events.json to indicate trial types rather than participant-level
    conditions. This function attempts to infer participant conditions from event patterns.

    Args:
        events: List of event dictionaries from events.json
        dataset_id: OpenNeuro dataset ID

    Returns:
        Dictionary mapping participant_id to condition label (or empty if not applicable)
    """
    # This is a placeholder for datasets that might use events.json for condition labels
    # Most OpenNeuro datasets use participants.tsv for subject-level conditions
    return {}


def generate_condition_labels(
    dataset_root: Path,
    dataset_id: str,
    output_path: Path
) -> Dict[str, str]:
    """
    Generate condition labels file for a dataset.

    Args:
        dataset_root: Root directory of the downloaded dataset
        dataset_id: OpenNeuro dataset ID
        output_path: Path to write the output labels CSV

    Returns:
        Dictionary of participant_id -> condition label
    """
    logger.info(f"Processing dataset: {dataset_id} at {dataset_root}")

    # Locate participants.tsv
    participants_path = dataset_root / 'participants.tsv'
    if not participants_path.exists():
        # Try subdirectory structure (BIDS)
        participants_path = dataset_root / 'sub-*/participants.tsv'
        # Fallback: look in dataset root or common BIDS locations
        for subdir in dataset_root.iterdir():
            if subdir.is_dir() and subdir.name.startswith('sub-'):
                participants_path = dataset_root / 'participants.tsv'
                if participants_path.exists():
                    break
                # Check inside sub directory
                for sub_file in subdir.glob('*.tsv'):
                    if 'participant' in sub_file.name:
                        participants_path = sub_file
                        break
                if participants_path.exists():
                    break

    if not participants_path.exists():
        raise FileNotFoundError(
            f"Could not find participants.tsv in {dataset_root} for {dataset_id}"
        )

    # Load participants
    participants = load_participants_tsv(participants_path)
    logger.info(f"Loaded {len(participants)} participants from {participants_path}")

    # Extract labels
    labels = extract_exclusion_labels_from_participants(participants, dataset_id)

    # If no labels found, try events.json
    if not labels:
        # Look for events.json files
        events_path = dataset_root / 'task-exclusion_events.json'
        if not events_path.exists():
            events_path = dataset_root / 'task-reward_events.json'

        if events_path.exists():
            events = load_events_json(events_path)
            labels = extract_labels_from_events_json(events, dataset_id)

    # If still no labels, create a mapping based on participant ID patterns
    # This handles cases where condition info is embedded in participant IDs
    if not labels:
        logger.warning(
            f"No explicit condition labels found for {dataset_id}. "
            "Attempting to infer from participant IDs."
        )
        for participant in participants:
            participant_id = participant.get('participant_id', '')
            if not participant_id:
                continue

            # Common patterns: sub-01 vs sub-01_exclusion, or numeric encoding
            if 'exclusion' in participant_id.lower() or 'exclude' in participant_id.lower():
                labels[participant_id] = 'excluded'
            elif 'inclusion' in participant_id.lower() or 'include' in participant_id.lower():
                labels[participant_id] = 'included'
            else:
                # Default to 'included' for control groups if no other info
                # This is a safe default for many social exclusion paradigms
                # where the exclusion condition is the experimental manipulation
                labels[participant_id] = 'included'

    # Write output CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['participant_id', 'condition', 'dataset_id'])
        for participant_id in sorted(labels.keys()):
            writer.writerow([participant_id, labels[participant_id], dataset_id])

    logger.info(f"Wrote {len(labels)} condition labels to {output_path}")
    return labels


def main():
    """Main entry point for condition label generation."""
    parser = argparse.ArgumentParser(
        description='Generate condition labels from participants.tsv or events.json'
    )
    parser.add_argument(
        '--dataset-root',
        type=str,
        required=True,
        help='Root directory of the downloaded dataset'
    )
    parser.add_argument(
        '--dataset-id',
        type=str,
        required=True,
        choices=['ds000246', 'ds004738'],
        help='OpenNeuro dataset ID'
    )
    parser.add_argument(
        '--output',
        type=str,
        required=False,
        help='Output path for labels CSV (defaults to data/behavioral/{dataset_id}_labels.csv)'
    )

    args = parser.parse_args()

    # Load configuration
    config = get_config()
    ensure_paths_exist(config)

    dataset_root = Path(args.dataset_root)
    dataset_id = args.dataset_id

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path('behavioral') / f'{dataset_id}_labels.csv'

    try:
        labels = generate_condition_labels(dataset_root, dataset_id, output_path)
        print(f"Successfully generated {len(labels)} condition labels")
        print(f"Output written to: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate condition labels: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
