import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import from sibling utils to ensure config consistency
from utils.config_loader import load_config, get_dataset_by_id

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_dataset_metadata(dataset_root: Path) -> Dict[str, Any]:
    """
    Load dataset metadata (dataset_description.json) and participants.tsv.
    Returns a dictionary containing dataset info and participant data.
    """
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset root not found: {dataset_root}")

    # Load dataset_description.json
    desc_file = dataset_root / "dataset_description.json"
    if not desc_file.exists():
        raise FileNotFoundError(f"dataset_description.json not found in {dataset_root}")

    with open(desc_file, 'r') as f:
        dataset_desc = json.load(f)

    # Load participants.tsv
    participants_file = dataset_root / "participants.tsv"
    if not participants_file.exists():
        raise FileNotFoundError(f"participants.tsv not found in {dataset_root}")

    participants_df = pd.read_csv(participants_file, sep='\t')

    return {
        "name": dataset_desc.get("Name", "Unknown"),
        "id": dataset_desc.get("ID", dataset_root.name),
        "description": dataset_desc,
        "participants": participants_df
    }


def load_task_events(dataset_root: Path, task_name: str) -> pd.DataFrame:
    """
    Load events.tsv for a specific task from the dataset.
    """
    # Find events.tsv files for the task
    # Standard BIDS path: sub-<label>/func/sub-<label>_<task-<task_label>>_events.tsv
    events_files = list(dataset_root.glob(f"sub-*/func/*task-{task_name}*events.tsv"))

    if not events_files:
        logger.warning(f"No events.tsv found for task '{task_name}' in {dataset_root}")
        return pd.DataFrame()

    # Combine events from all subjects for this task
    all_events = []
    for ef in events_files:
        subject_id = ef.parent.name.split('_')[0]  # sub-<label>
        df = pd.read_csv(ef, sep='\t')
        df['subject_id'] = subject_id
        df['source_file'] = str(ef.relative_to(dataset_root))
        all_events.append(df)

    if all_events:
        return pd.concat(all_events, ignore_index=True)
    return pd.DataFrame()


def map_conditions(metadata: Dict[str, Any], dataset_type: str) -> pd.DataFrame:
    """
    Map raw condition labels to standardized 'exclusion', 'inclusion', or 'reward' groups.
    Returns a DataFrame with participant_id, original_label, mapped_group.
    """
    participants = metadata["participants"]
    if participants.empty:
        return pd.DataFrame(columns=["participant_id", "original_label", "mapped_group"])

    # Heuristic mapping based on common OpenNeuro dataset conventions
    # For ds000246 (Cyberball): conditions usually 'exclude', 'include', 'neutral'
    # For ds004738 (Reward): conditions usually 'reward', 'loss', 'neutral' or similar
    
    mapped_rows = []
    
    # Get unique condition labels from participants or events if available
    # We assume the 'participants.tsv' might have a 'group' or 'condition' column,
    # or we derive it from the task events if the metadata includes task info.
    # Since this is a harmonization step, we look for standard columns first.
    
    condition_col = None
    for col in ['condition', 'group', 'task_condition', 'task_label']:
        if col in participants.columns:
            condition_col = col
            break

    if condition_col:
        for _, row in participants.iterrows():
            pid = row['participant_id']
            raw_label = str(row[condition_col]).strip()
            
            mapped_group = "unknown"
            if dataset_type == "exclusion":
                if any(x in raw_label.lower() for x in ['exclude', 'exclusion']):
                    mapped_group = "exclusion"
                elif any(x in raw_label.lower() for x in ['include', 'inclusion', 'control']):
                    mapped_group = "inclusion"
            elif dataset_type == "reward":
                # For reward tasks, we map to 'reward' or 'neutral' based on task type
                # But T014 specifically asks to link to exclusion/inclusion group.
                # Since ds004738 is purely reward, we might need to map participants
                # to a 'neutral' or 'reward' group, or if the study design implies
                # a social context, map accordingly. 
                # However, the task says: "linking participants to their exclusion/inclusion group".
                # If the dataset doesn't have exclusion, we must map based on the task design.
                # For ds004738 (Reward), typically all participants are in a 'reward' context.
                # We will map them to 'reward_task' to distinguish from 'exclusion_task'.
                # The analysis later (T018) will compare Exclusion vs Inclusion groups.
                # If a dataset is purely reward, it might be used as a control or
                # the 'inclusion' condition might be inferred if the study had a social component.
                # Given the prompt "merged exclusion and reward datasets", we assume
                # ds000246 provides Exclusion/Inclusion, and ds004738 provides Reward data
                # (potentially for a different analysis or as a control).
                # For the specific requirement "linking participants to their exclusion/inclusion group",
                # we map ds004738 participants to a 'reward' group if they don't fit exclusion/inclusion.
                
                if any(x in raw_label.lower() for x in ['reward', 'win']):
                    mapped_group = "reward"
                elif any(x in raw_label.lower() for x in ['loss', 'neutral']):
                    mapped_group = "neutral"
                else:
                    mapped_group = "reward" # Default for reward dataset
            
            mapped_rows.append({
                "participant_id": pid,
                "original_label": raw_label,
                "mapped_group": mapped_group,
                "dataset_type": dataset_type
            })
    else:
        # Fallback: If no condition column, assume all are 'inclusion' for exclusion dataset
        # and 'reward' for reward dataset, based on the dataset's primary purpose.
        for _, row in participants.iterrows():
            pid = row['participant_id']
            if dataset_type == "exclusion":
                mapped_group = "inclusion" # Default assumption if no label found
            elif dataset_type == "reward":
                mapped_group = "reward"
            else:
                mapped_group = "unknown"
            
            mapped_rows.append({
                "participant_id": pid,
                "original_label": "default",
                "mapped_group": mapped_group,
                "dataset_type": dataset_type
            })

    return pd.DataFrame(mapped_rows)


def harmonize_datasets(exclusion_root: Path, reward_root: Path, output_path: Path) -> Path:
    """
    Harmonize data from exclusion and reward datasets.
    Creates a unified metadata file linking participants to their group and task type.
    
    This function:
    1. Loads metadata from both datasets.
    2. Maps conditions to standardized groups.
    3. Merges into a single DataFrame.
    4. Saves to a unified CSV/TSV file.
    """
    logger.info(f"Starting harmonization of {exclusion_root} and {reward_root}")
    
    # Load metadata
    exc_meta = load_dataset_metadata(exclusion_root)
    reward_meta = load_dataset_metadata(reward_root)
    
    # Map conditions
    exc_mapped = map_conditions(exc_meta, "exclusion")
    reward_mapped = map_conditions(reward_meta, "reward")
    
    # Concatenate
    unified_df = pd.concat([exc_mapped, reward_mapped], ignore_index=True)
    
    # Add dataset ID column for provenance (FR-001 compliance)
    unified_df['source_dataset'] = [
        exc_meta['id'] if row['dataset_type'] == 'exclusion' else reward_meta['id']
        for _, row in unified_df.iterrows()
    ]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to TSV (standard for tabular data)
    unified_df.to_csv(output_path, sep='\t', index=False)
    
    logger.info(f"Harmonized metadata saved to {output_path}")
    logger.info(f"Total participants: {len(unified_df)}")
    logger.info(f"Group distribution:\n{unified_df['mapped_group'].value_counts()}")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Harmonize exclusion and reward datasets")
    parser.add_argument("--exclusion-root", type=str, required=True, help="Path to exclusion dataset root (e.g., ds000246)")
    parser.add_argument("--reward-root", type=str, required=True, help="Path to reward dataset root (e.g., ds004738)")
    parser.add_argument("--output", type=str, default="data/behavioral/harmonized_metadata.tsv", help="Output file path")
    
    args = parser.parse_args()
    
    exclusion_root = Path(args.exclusion_root)
    reward_root = Path(args.reward_root)
    output_path = Path(args.output)
    
    if not exclusion_root.exists():
        logger.error(f"Exclusion root not found: {exclusion_root}")
        sys.exit(1)
    if not reward_root.exists():
        logger.error(f"Reward root not found: {reward_root}")
        sys.exit(1)
        
    try:
        harmonize_datasets(exclusion_root, reward_root, output_path)
        logger.info("Harmonization completed successfully.")
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()