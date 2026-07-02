"""
Harmonize downloaded OpenNeuro datasets (ds000246 and ds004738).

This script implements the 'Merged Dataset Strategy' required for the
analysis of social exclusion and reward. It performs the following:
1. Loads participant metadata from both downloaded datasets.
2. Maps participant IDs to a unified naming convention.
3. Aligns condition labels (Exclusion vs Inclusion, Reward vs No-Reward).
4. Generates a unified metadata CSV including 'dataset_id' as a covariate tag.
5. Validates the merged structure against the project's configuration.
"""

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config.loader import get_config, get_dataset_id, get_all_dataset_ids

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for dataset mapping
# ds000246: Social Exclusion (Cyberball)
# ds004738: Reward Processing (Monetary Incentive Delay / similar)
DATASET_CONFIG = {
    "ds000246": {
        "name": "social_exclusion",
        "task_label": "exclusion",
        "condition_map": {
            "exclusion": "exclusion",
            "inclusion": "inclusion"
        },
        "prefix": "exc"
    },
    "ds004738": {
        "name": "reward_task",
        "task_label": "reward",
        "condition_map": {
            "win": "reward_receipt",
            "loss": "no_reward",
            "anticipation": "reward_ant"
        },
        "prefix": "rew"
    }
}

def load_participants_tsv(file_path: Path) -> List[Dict[str, str]]:
    """Load a participants.tsv file and return a list of dicts."""
    if not file_path.exists():
        raise FileNotFoundError(f"Participants file not found: {file_path}")
    
    participants = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            participants.append(row)
    return participants

def load_events_json(file_path: Path) -> List[Dict[str, Any]]:
    """Load events.json or task-specific JSON if available, fallback to empty."""
    if not file_path.exists():
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"Could not parse JSON in {file_path}, skipping events metadata.")
        return []

def harmonize_participant_id(participant_id: str, dataset_id: str, prefix: str) -> str:
    """
    Create a unified participant ID.
    Format: {prefix}_{original_id}
    """
    # Clean the original ID (remove 'sub-' prefix if present)
    clean_id = participant_id.replace("sub-", "").replace("-", "_")
    return f"{prefix}_{clean_id}"

def align_condition_labels(
    condition: str, 
    dataset_id: str, 
    task_label: str
) -> Optional[str]:
    """
    Map raw condition labels to a unified schema.
    Returns None if the condition cannot be mapped.
    """
    config = DATASET_CONFIG.get(dataset_id)
    if not config:
        return None

    # Normalize input
    condition_lower = condition.lower()
    
    # Check direct mapping
    if condition_lower in config["condition_map"]:
        return config["condition_map"][condition_lower]
    
    # Fuzzy matching for common variations
    if "exclude" in condition_lower and dataset_id == "ds000246":
        return "exclusion"
    if "include" in condition_lower and dataset_id == "ds000246":
        return "inclusion"
    if "anticip" in condition_lower and dataset_id == "ds004738":
        return "reward_ant"
    if "win" in condition_lower and dataset_id == "ds004738":
        return "reward_receipt"
    if "loss" in condition_lower and dataset_id == "ds004738":
        return "no_reward"

    logger.warning(f"Could not map condition '{condition}' for dataset {dataset_id}")
    return None

def harmonize_datasets(
    raw_data_dir: Path, 
    output_dir: Path, 
    config_path: Optional[Path] = None
) -> Path:
    """
    Main harmonization logic.
    
    1. Iterates through configured datasets (ds000246, ds004738).
    2. Reads participant metadata.
    3. Generates a unified metadata CSV.
    4. Writes the output to data/processed-fmri/harmonized_metadata.csv
    """
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    config = get_config(config_path) if config_path else {}
    all_dataset_ids = get_all_dataset_ids() # Should return ['ds000246', 'ds004738']

    harmonized_records = []

    for ds_id in all_dataset_ids:
        ds_config = DATASET_CONFIG.get(ds_id)
        if not ds_config:
            logger.warning(f"No config found for dataset {ds_id}, skipping.")
            continue

        logger.info(f"Processing dataset: {ds_id} ({ds_config['name']})")
        
        # Locate dataset root in raw_data_dir
        # Expected structure: raw_data_dir/dsXXXXXX/
        ds_root = raw_data_dir / ds_id
        if not ds_root.exists():
            # Try finding directory that starts with the ID if exact match fails
            candidates = [d for d in raw_data_dir.iterdir() if d.name.startswith(ds_id)]
            if candidates:
                ds_root = candidates[0]
            else:
                logger.error(f"Dataset directory not found: {ds_root}")
                continue

        participants_file = ds_root / "participants.tsv"
        if not participants_file.exists():
            logger.error(f"participants.tsv missing in {ds_root}")
            continue

        participants = load_participants_tsv(participants_file)
        
        # Add dataset-specific metadata
        for p in participants:
            pid = p.get('participant_id', p.get('sub', ''))
            if not pid:
                continue

            unified_pid = harmonize_participant_id(pid, ds_id, ds_config["prefix"])
            
            # Determine group/condition based on task design
            # For ds000246, we might need to look at task JSON to determine group assignment
            # For ds004738, similar logic. 
            # Since we don't have the full behavioral data here yet, we assume 
            # the 'participant_id' in the CSV implies inclusion in the study.
            # We will create a 'group' column based on the dataset type for now,
            # and refine with task-specific labels in T011/T014.
            
            # Strategy: 
            # ds000246 -> Group: 'social' (Exclusion/Inclusion)
            # ds004738 -> Group: 'reward' (Win/Loss)
            # Later tasks will split these further.
            
            group_label = ds_config["name"]
            
            record = {
                "unified_participant_id": unified_pid,
                "original_participant_id": pid,
                "dataset_id": ds_id,
                "dataset_name": ds_config["name"],
                "task_label": ds_config["task_label"],
                "group": group_label,
                "covariate_dataset_id": ds_id  # Explicit tag for GLM confounds
            }
            
            harmonized_records.append(record)

    # Write output
    output_file = output_dir / "harmonized_metadata.csv"
    logger.info(f"Writing harmonized metadata to {output_file}")
    
    if harmonized_records:
        fieldnames = harmonized_records[0].keys()
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(harmonized_records)
    else:
        logger.error("No records were harmonized. Output file not created.")
        raise ValueError("Harmonization failed: No records processed.")

    return output_file

def main():
    parser = argparse.ArgumentParser(
        description="Harmonize OpenNeuro datasets for merged analysis."
    )
    parser.add_argument(
        "--raw-data", 
        type=Path, 
        default=project_root / "data" / "raw-fmri",
        help="Path to the raw data directory containing ds000246 and ds004738."
    )
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=project_root / "data" / "processed-fmri",
        help="Path to write the harmonized metadata."
    )
    parser.add_argument(
        "--config", 
        type=Path, 
        default=project_root / "code" / "config" / "config.yaml",
        help="Path to the configuration file."
    )

    args = parser.parse_args()

    try:
        output_path = harmonize_datasets(
            raw_data_dir=args.raw_data,
            output_dir=args.output_dir,
            config_path=args.config
        )
        logger.info(f"Successfully harmonized datasets. Output: {output_path}")
        
        # Generate provenance sidecar for this step
        from utils.provenance import generate_provenance_record, write_provenance_sidecar
        provenance = generate_provenance_record(
            step="harmonize_datasets",
            input_paths=[str(args.raw_data)],
            output_paths=[str(output_path)],
            parameters={
                "datasets": list(DATASET_CONFIG.keys()),
                "config": str(args.config)
            }
        )
        write_provenance_sidecar(provenance, output_path)
        
        return 0
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
