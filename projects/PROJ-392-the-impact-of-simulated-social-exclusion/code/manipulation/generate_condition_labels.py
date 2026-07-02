"""
Generate condition labels for social exclusion/inclusion tasks.

This module extracts exclusion/inclusion labels from participants.tsv or task JSON
files for each dataset (ds000246, ds004738) and creates a unified condition mapping.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_participants_tsv(participants_path: Path) -> pd.DataFrame:
    """Load participants.tsv file."""
    if not participants_path.exists():
        raise FileNotFoundError(f"Participants file not found: {participants_path}")
    return pd.read_csv(participants_path, sep='\t')


def load_task_events(events_path: Path) -> pd.DataFrame:
    """Load task events JSON or TSV file."""
    if not events_path.exists():
        raise FileNotFoundError(f"Events file not found: {events_path}")
    
    if events_path.suffix == '.tsv':
        return pd.read_csv(events_path, sep='\t')
    elif events_path.suffix == '.json':
        with open(events_path, 'r') as f:
            data = json.load(f)
            # Convert JSON structure to DataFrame if needed
            if isinstance(data, list):
                return pd.DataFrame(data)
            return pd.DataFrame([data])
    else:
        raise ValueError(f"Unsupported events file format: {events_path.suffix}")


def extract_condition_from_participants(
    participants_df: pd.DataFrame,
    dataset_name: str
) -> Dict[str, str]:
    """
    Extract condition labels from participants.tsv.
    
    For ds000246 (Cyberball): Look for 'group' or 'condition' column
    For ds004738 (Reward): Look for relevant condition indicators
    
    Returns a mapping of participant_id to condition label.
    """
    condition_mapping = {}
    
    # Common column names that might indicate group/condition
    condition_cols = ['group', 'condition', 'task_condition', 'exclusion_group']
    
    # Find the relevant column
    condition_col = None
    for col in condition_cols:
        if col in participants_df.columns:
            condition_col = col
            break
    
    if condition_col is None:
        logger.warning(f"No condition column found in {dataset_name} participants.tsv")
        # Default mapping based on participant ID patterns if available
        for _, row in participants_df.iterrows():
            pid = row.get('participant_id', row.get('sub'))
            if pid:
                # Default to 'inclusion' if no specific condition found
                condition_mapping[str(pid)] = 'inclusion'
        return condition_mapping
    
    # Map conditions based on dataset-specific logic
    for _, row in participants_df.iterrows():
        pid = row.get('participant_id', row.get('sub'))
        condition_value = str(row[condition_col]).lower().strip()
        
        if pid:
            if dataset_name == 'ds000246':
                # Cyberball dataset: map exclusion/inclusion groups
                if any(term in condition_value for term in ['exclusion', 'exclude', 'ostracized']):
                    condition_mapping[str(pid)] = 'exclusion'
                elif any(term in condition_value for term in ['inclusion', 'include', 'control']):
                    condition_mapping[str(pid)] = 'inclusion'
                else:
                    # Default to inclusion for unknown values
                    condition_mapping[str(pid)] = 'inclusion'
            elif dataset_name == 'ds004738':
                # Reward task dataset: typically control condition
                condition_mapping[str(pid)] = 'inclusion'  # Control group
            else:
                condition_mapping[str(pid)] = 'unknown'
    
    return condition_mapping


def extract_condition_from_events(
    events_df: pd.DataFrame,
    dataset_name: str
) -> Dict[str, str]:
    """
    Extract condition labels from task events files.
    
    Analyzes event types to determine if a participant experienced
    exclusion or inclusion conditions.
    """
    participant_conditions = {}
    
    # Common event type names
    exclusion_events = ['exclusion', 'ostracism', 'social_exclusion', 'exclude']
    inclusion_events = ['inclusion', 'control', 'social_inclusion', 'include']
    
    # Group by participant
    participant_col = None
    for col in ['participant_id', 'sub', 'subject']:
        if col in events_df.columns:
            participant_col = col
            break
    
    if participant_col is None:
        logger.warning(f"No participant column found in events for {dataset_name}")
        return {}
    
    event_type_col = None
    for col in ['event_type', 'type', 'trial_type', 'condition']:
        if col in events_df.columns:
            event_type_col = col
            break
    
    if event_type_col is None:
        logger.warning(f"No event type column found in events for {dataset_name}")
        return {}
    
    for participant_id in events_df[participant_col].unique():
        participant_events = events_df[events_df[participant_col] == participant_id]
        event_types = participant_events[event_type_col].str.lower().tolist()
        
        # Determine condition based on event types
        has_exclusion = any(any(term in event for term in exclusion_events) for event in event_types)
        has_inclusion = any(any(term in event for term in inclusion_events) for event in event_types)
        
        if has_exclusion and not has_inclusion:
            participant_conditions[str(participant_id)] = 'exclusion'
        elif has_inclusion and not has_exclusion:
            participant_conditions[str(participant_id)] = 'inclusion'
        elif has_exclusion and has_inclusion:
            # Mixed: use majority or first occurrence
            exclusion_count = sum(1 for event in event_types if any(term in event for term in exclusion_events))
            inclusion_count = sum(1 for event in event_types if any(term in event for term in inclusion_events))
            if exclusion_count > inclusion_count:
                participant_conditions[str(participant_id)] = 'exclusion'
            else:
                participant_conditions[str(participant_id)] = 'inclusion'
        else:
            participant_conditions[str(participant_id)] = 'unknown'
    
    return participant_conditions


def generate_condition_labels(
    dataset_path: Path,
    dataset_name: str,
    output_path: Path
) -> pd.DataFrame:
    """
    Generate condition labels for a dataset.
    
    Args:
        dataset_path: Path to the dataset root directory
        dataset_name: Name of the dataset (e.g., 'ds000246', 'ds004738')
        output_path: Path to save the condition labels CSV
    
    Returns:
        DataFrame with participant_id and condition columns
    """
    logger.info(f"Generating condition labels for {dataset_name}")
    
    # Try to load from participants.tsv first
    participants_path = dataset_path / 'participants.tsv'
    events_path = None
    
    # Look for events files
    task_dirs = list(dataset_path.glob('sub-*/func/*events*.tsv'))
    if task_dirs:
        events_path = task_dirs[0]
    
    condition_mapping = {}
    
    if participants_path.exists():
        try:
            participants_df = load_participants_tsv(participants_path)
            condition_mapping = extract_condition_from_participants(
                participants_df, dataset_name
            )
            logger.info(f"Extracted {len(condition_mapping)} conditions from participants.tsv")
        except Exception as e:
            logger.warning(f"Failed to extract from participants.tsv: {e}")
    
    # If participants.tsv didn't yield results, try events files
    if not condition_mapping and events_path:
        try:
            events_df = load_task_events(events_path)
            condition_mapping = extract_condition_from_events(events_df, dataset_name)
            logger.info(f"Extracted {len(condition_mapping)} conditions from events files")
        except Exception as e:
            logger.warning(f"Failed to extract from events: {e}")
    
    # If still no results, create a default mapping
    if not condition_mapping:
        logger.warning("No conditions found, creating default mapping")
        # Try to get participant list from any available source
        participant_ids = []
        if participants_path.exists():
            try:
                participants_df = load_participants_tsv(participants_path)
                participant_ids = participants_df.get('participant_id', 
                                                     participants_df.get('sub', [])).tolist()
            except:
                pass
        
        for pid in participant_ids:
            if pid:
                condition_mapping[str(pid)] = 'inclusion'  # Default
    
    # Create output DataFrame
    result_df = pd.DataFrame([
        {'participant_id': pid, 'condition': cond}
        for pid, cond in condition_mapping.items()
    ])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved condition labels to {output_path}")
    
    return result_df


def main():
    """Main entry point for condition label generation."""
    parser = argparse.ArgumentParser(
        description='Generate exclusion/inclusion condition labels from dataset files'
    )
    parser.add_argument(
        '--dataset-path',
        type=Path,
        required=True,
        help='Path to the dataset root directory'
    )
    parser.add_argument(
        '--dataset-name',
        type=str,
        required=True,
        help='Name of the dataset (e.g., ds000246, ds004738)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output path for condition labels CSV'
    )
    
    args = parser.parse_args()
    
    try:
        generate_condition_labels(
            args.dataset_path,
            args.dataset_name,
            args.output
        )
        logger.info("Condition label generation completed successfully")
    except Exception as e:
        logger.error(f"Condition label generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
