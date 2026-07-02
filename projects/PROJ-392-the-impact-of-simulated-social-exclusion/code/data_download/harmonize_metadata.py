import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.loader import get_config, get_path, get_all_dataset_ids
from data_download.harmonize_datasets import load_participants_tsv, load_events_json
from utils.provenance import generate_provenance_record, write_provenance_sidecar

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mapping for condition labels based on dataset specifics
# ds000246 (Cyberball): 'exclusion' vs 'inclusion'
# ds004738 (Reward): 'reward' vs 'neutral' (mapped to task types)
CONDITION_LABEL_MAP = {
    'ds000246': {
        'exclusion': 'exclusion',
        'inclusion': 'inclusion'
    },
    'ds004738': {
        # In reward task, we map the 'reward' condition to the 'reward' task type
        # and 'neutral' to 'neutral' task type for the harmonized view.
        # The 'group' in the metadata will be derived from the social exclusion
        # dataset (ds000246) for participants who were in that study.
        # For ds004738 participants, we might not have a social exclusion group
        # unless the study design implies a separate cohort.
        # However, the task description implies a 'Merged Dataset Strategy'
        # where we link participants to their exclusion/inclusion group.
        # Assuming ds004738 participants are the 'control' or 'neutral' group
        # or we are analyzing the interaction.
        # For this specific task (T014), we create the unified metadata file.
        'reward': 'reward',
        'neutral': 'neutral'
    }
}

def load_dataset_manifest(dataset_id: str) -> Dict[str, Any]:
    """Load the manifest or participants file for a dataset."""
    base_path = get_path('data_raw_fmri')
    ds_path = Path(base_path) / dataset_id
    
    participants_file = ds_path / 'participants.tsv'
    if not participants_file.exists():
        logger.warning(f"Participants file not found for {dataset_id}: {participants_file}")
        return {}
    
    return load_participants_tsv(str(participants_file))

def harmonize_participant_groups(
    exclusion_data: Dict[str, Any],
    reward_data: Dict[str, Any],
    exclusion_ds_id: str,
    reward_ds_id: str
) -> List[Dict[str, Any]]:
    """
    Create a unified list of participant metadata.
    
    Strategy:
    1. For participants in the Exclusion dataset (ds000246):
       - Extract their group (exclusion/inclusion) from the condition labels.
       - Mark task type as 'social_exclusion'.
    2. For participants in the Reward dataset (ds004738):
       - If the study design treats them as a control group for exclusion,
         assign a default group (e.g., 'control' or 'inclusion' equivalent).
       - Mark task type as 'reward'.
    3. Merge into a single list.
    """
    unified_metadata = []
    
    # Process Exclusion Dataset
    if exclusion_data and exclusion_ds_id in exclusion_data.get('participants', []):
        participants = exclusion_data['participants']
        for pid, p_data in participants.items():
            # Determine group based on condition labels or participant.tsv columns
            # Assuming 'condition' column exists or derived from events
            group = 'unknown'
            if 'condition' in p_data:
                # Map raw condition to standard group
                condition = p_data['condition'].lower()
                if 'exclusion' in condition:
                    group = 'exclusion'
                elif 'inclusion' in condition:
                    group = 'inclusion'
            
            unified_metadata.append({
                'participant_id': pid,
                'dataset_id': exclusion_ds_id,
                'group': group,
                'task_type': 'social_exclusion',
                'run_type': 'block' # Default for exclusion task
            })
    
    # Process Reward Dataset
    if reward_data and reward_ds_id in reward_data.get('participants', []):
        participants = reward_data['participants']
        for pid, p_data in participants.items():
            # For reward dataset, we need to determine if they map to a group.
            # In a merged strategy, if we don't have exclusion data for these,
            # we might treat them as a separate cohort or a control.
            # Let's assume they are the 'neutral' group for the purpose of this metadata
            # unless specific exclusion labels are found.
            group = 'neutral' 
            
            # Check if there's a condition column indicating reward/neutral
            if 'condition' in p_data:
                condition = p_data['condition'].lower()
                if 'reward' in condition:
                    group = 'reward' # Or 'exclusion' equivalent if mapped
                elif 'neutral' in condition:
                    group = 'neutral'
            
            unified_metadata.append({
                'participant_id': pid,
                'dataset_id': reward_ds_id,
                'group': group,
                'task_type': 'reward',
                'run_type': 'event' # Default for reward task
            })
    
    return unified_metadata

def write_unified_metadata(metadata: List[Dict[str, Any]], output_path: str) -> None:
    """Write the unified metadata to a CSV file."""
    if not metadata:
        logger.warning("No metadata to write.")
        return

    fieldnames = ['participant_id', 'dataset_id', 'group', 'task_type', 'run_type']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metadata)
    
    logger.info(f"Unified metadata written to {output_path}")

def generate_provenance_for_metadata(metadata_path: str, datasets: List[str]) -> None:
    """Generate provenance sidecar for the unified metadata file."""
    provenance = generate_provenance_record(
        artifact_path=metadata_path,
        task_id="T014",
        task_name="harmonize_metadata",
        input_datasets=datasets,
        parameters={"version": "1.0.0"}
    )
    write_provenance_sidecar(metadata_path, provenance)
    logger.info(f"Provenance sidecar generated for {metadata_path}")

def main():
    parser = argparse.ArgumentParser(description="Harmonize and label data from merged datasets.")
    parser.add_argument('--exclusion-ds', type=str, default='ds000246', help='Exclusion dataset ID')
    parser.add_argument('--reward-ds', type=str, default='ds004738', help='Reward dataset ID')
    parser.add_argument('--output', type=str, default=None, help='Output file path (default: data/results/unified_metadata.csv)')
    args = parser.parse_args()

    config = get_config()
    exclusion_ds_id = args.exclusion_ds
    reward_ds_id = args.reward_ds

    logger.info(f"Starting metadata harmonization for {exclusion_ds_id} and {reward_ds_id}")

    # Load data
    exclusion_data = load_dataset_manifest(exclusion_ds_id)
    reward_data = load_dataset_manifest(reward_ds_id)

    # Harmonize
    unified_metadata = harmonize_participant_groups(
        exclusion_data, reward_data, exclusion_ds_id, reward_ds_id
    )

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        results_dir = get_path('data_results')
        output_path = os.path.join(results_dir, 'unified_metadata.csv')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write
    write_unified_metadata(unified_metadata, output_path)

    # Generate Provenance
    generate_provenance_for_metadata(output_path, [exclusion_ds_id, reward_ds_id])

    logger.info("Harmonization complete.")

if __name__ == '__main__':
    main()
