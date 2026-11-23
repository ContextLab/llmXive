"""
generate_condition_labels.py

Extracts exclusion/inclusion condition labels from BIDS participants.tsv
and task events.json files for OpenNeuro datasets ds000246 (Exclusion)
and ds004738 (Reward).

This script generates a unified CSV mapping participant IDs to their
experimental condition (e.g., 'excluded', 'included', 'neutral') and
task type, suitable for downstream harmonization and analysis.

It handles:
- ds000246: Cyberball task (exclusion vs inclusion groups).
- ds004738: Reward task (typically neutral/control, but labeled as 'reward').
- Fallback to events.json if participants.tsv lacks explicit group columns.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_IDS = ['ds000246', 'ds004738']
OUTPUT_FILE = Path('data/behavioral/condition_labels.csv')
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Mapping for ds000246 (Cyberball)
# The Cyberball task typically has 'Exclusion' and 'Inclusion' groups.
# We map these to standardized labels.
CYBERBALL_GROUP_MAP = {
    'exclusion': 'excluded',
    'inclusion': 'included',
    'Exclusion': 'excluded',
    'Inclusion': 'included',
    'Excluded': 'excluded',
    'Included': 'included'
}

# Mapping for ds004738 (Reward)
# This dataset is primarily a reward task. We label it as 'neutral'
# regarding social exclusion, or 'reward' regarding task type.
# For the purpose of the exclusion analysis, these participants are
# the 'control' or 'included' baseline, but we mark them specifically
# to distinguish from the Cyberball 'inclusion' group.
REWARD_GROUP_MAP = {
    'reward': 'reward_task',
    'control': 'neutral',
    'baseline': 'neutral'
}


def load_participants_tsv(participants_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Load a BIDS participants.tsv file into a list of dictionaries.
    Handles basic TSV parsing without pandas to minimize dependencies.
    """
    if not participants_path.exists():
        logger.warning(f"Participants file not found: {participants_path}")
        return None

    participants = []
    with open(participants_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines:
            return None

        # Parse header
        header = lines[0].strip().split('\t')
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            values = line.split('\t')
            # Ensure we have enough values
            if len(values) < len(header):
                values.extend([''] * (len(header) - len(values)))
            
            participant = dict(zip(header, values))
            participants.append(participant)
    
    return participants


def load_task_events(events_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Load a BIDS events.json file (if it exists as metadata) or
    parse events.tsv if available.
    
    Note: In BIDS, events are usually in events.tsv. events.json is
    metadata describing the columns. We primarily look for events.tsv
    but accept the path passed as 'events_path' which might be the .tsv.
    """
    # If the path ends in .json, we might be looking for metadata,
    # but for condition extraction, we need the actual data (tsv).
    # Let's assume the caller passes the .tsv path or we derive it.
    
    actual_path = events_path
    if events_path.suffix == '.json':
        actual_path = events_path.with_suffix('.tsv')
    
    if not actual_path.exists():
        # Check if .tsv exists next to .json
        if not actual_path.exists():
            logger.warning(f"Events file not found: {actual_path}")
            return None

    events = []
    with open(actual_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if not lines:
            return None

        header = lines[0].strip().split('\t')
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            values = line.split('\t')
            if len(values) < len(header):
                values.extend([''] * (len(header) - len(values)))
            
            event = dict(zip(header, values))
            events.append(event)
    
    return events


def extract_condition_from_participants(
    participant: Dict[str, Any], 
    dataset_id: str
) -> Optional[str]:
    """
    Extract the condition label for a participant based on their row
    in participants.tsv.
    """
    # Look for common column names indicating group
    possible_cols = ['group', 'condition', 'task', 'cyberball_group', 'Group']
    
    condition = None
    for col in possible_cols:
        if col in participant:
            val = participant[col].strip().lower()
            if dataset_id == 'ds000246':
                condition = CYBERBALL_GROUP_MAP.get(val)
            elif dataset_id == 'ds004738':
                condition = REWARD_GROUP_MAP.get(val)
            
            if condition:
                break
    
    # Fallback: if no explicit column, check participant_id pattern
    # (e.g., sub-001_group-exclusion) - though BIDS usually separates this.
    if not condition:
        pid = participant.get('participant_id', '')
        if 'exclusion' in pid.lower():
            condition = 'excluded'
        elif 'inclusion' in pid.lower():
            condition = 'included'
        elif dataset_id == 'ds004738':
            condition = 'neutral' # Default for reward dataset if not specified
    
    return condition


def extract_condition_from_events(
    events: List[Dict[str, Any]], 
    dataset_id: str
) -> Optional[str]:
    """
    Infer condition from events.tsv if participant metadata is missing.
    For ds000246, look for 'exclusion' or 'inclusion' in trial_type.
    For ds004738, look for 'reward' or 'cue'.
    """
    if not events:
        return None

    # Analyze trial_types
    trial_types = set()
    for event in events:
        tt = event.get('trial_type', '')
        if tt:
            trial_types.add(tt.lower())

    if dataset_id == 'ds000246':
        if any('exclusion' in t for t in trial_types):
            return 'excluded'
        elif any('inclusion' in t for t in trial_types):
            return 'included'
    
    elif dataset_id == 'ds004738':
        if any('reward' in t for t in trial_types) or any('cue' in t for t in trial_types):
            return 'neutral' # In the context of exclusion, this is the control condition
    
    return None


def generate_condition_labels(
    raw_data_dir: Path,
    output_path: Path
) -> None:
    """
    Main logic to scan datasets, extract labels, and write a unified CSV.
    
    Args:
        raw_data_dir: Path to the directory containing downloaded datasets (e.g., data/raw-fmri).
        output_path: Path to write the output CSV.
    """
    results = []
    
    for dataset_id in DATASET_IDS:
        dataset_path = raw_data_dir / dataset_id
        if not dataset_path.exists():
            logger.error(f"Dataset directory not found: {dataset_path}")
            continue

        logger.info(f"Processing dataset: {dataset_id}")
        
        # 1. Load participants.tsv
        participants_path = dataset_path / 'participants.tsv'
        participants = load_participants_tsv(participants_path)
        
        if not participants:
            logger.warning(f"No participants found for {dataset_id}, skipping.")
            continue

        # 2. Iterate participants and determine condition
        # We need to find the associated task/events to confirm condition if participants.tsv is ambiguous
        # For ds000246, participants.tsv often has a 'group' column.
        # For ds004738, it might be less explicit.
        
        # Strategy:
        # - Try to get condition from participants row.
        # - If ambiguous, look for events.tsv for the first task run to infer.
        
        tasks = [d for d in dataset_path.iterdir() if d.is_dir() and d.name.startswith('sub-')]
        
        # If we can't find task subdirs, look for task- folders
        task_dirs = [d for d in dataset_path.iterdir() if d.is_dir() and 'task' in d.name]
        if not tasks and not task_dirs:
            # Maybe flat structure?
            tasks = list(dataset_path.iterdir())
        
        # Determine condition for each participant
        for p in participants:
            pid = p.get('participant_id', 'unknown')
            condition = extract_condition_from_participants(p, dataset_id)
            
            # Fallback to events if condition is None
            if condition is None:
                # Find an events file for this subject
                events_file = None
                # Search pattern: sub-<pid>/func/*events.tsv
                sub_dir = dataset_path / pid
                if not sub_dir.exists():
                    # Try sub-<pid>
                    sub_dir = dataset_path / f"sub-{pid}"
                
                if sub_dir.exists():
                    func_dir = sub_dir / 'func'
                    if func_dir.exists():
                        for f in func_dir.glob('*events.tsv'):
                            events_file = f
                            break
                
                if events_file:
                    events = load_task_events(events_file)
                    inferred_cond = extract_condition_from_events(events, dataset_id)
                    if inferred_cond:
                        condition = inferred_cond
                
                # Final fallback: assign a default based on dataset if still None
                if condition is None:
                    if dataset_id == 'ds004738':
                        condition = 'neutral'
                    else:
                        condition = 'unknown'

            results.append({
                'participant_id': pid,
                'dataset_id': dataset_id,
                'condition': condition
            })

    # Write results to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not results:
        logger.warning("No condition labels generated. Writing empty file.")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('participant_id,dataset_id,condition\n')
        for r in results:
            f.write(f"{r['participant_id']},{r['dataset_id']},{r['condition']}\n")
    
    logger.info(f"Condition labels written to {output_path}")
    logger.info(f"Total participants processed: {len(results)}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract exclusion/inclusion labels from BIDS datasets.'
    )
    parser.add_argument(
        '--input-dir', 
        type=str, 
        default=str(PROJECT_ROOT / 'data' / 'raw-fmri'),
        help='Path to the root directory containing downloaded datasets.'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=str(OUTPUT_FILE),
        help='Path to the output CSV file.'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    output_path = Path(args.output_file)
    
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_path}")
        sys.exit(1)
    
    try:
        generate_condition_labels(input_path, output_path)
    except Exception as e:
        logger.error(f"Failed to generate condition labels: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()