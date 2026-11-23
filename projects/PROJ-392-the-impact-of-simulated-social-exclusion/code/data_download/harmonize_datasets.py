"""
Harmonize datasets from OpenNeuro (ds000246 and ds004738).

This script implements the 'Merged Dataset Strategy':
1. Loads metadata from both datasets.
2. Maps participant IDs to ensure uniqueness across datasets.
3. Aligns condition labels (Exclusion vs Inclusion) to a unified schema.
4. Adds 'Dataset ID' as a covariate tag to the unified metadata.
5. Writes the unified metadata to `data/behavioral/harmonized_metadata.csv`.
6. Generates a provenance sidecar for the harmonization process.

This addresses FR-001 (Data Integration) and the Plan's Critical Design Pivot
regarding the Merged Dataset Strategy.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import csv

# Import provenance utility from the project's utils module
try:
    from utils.provenance import generate_provenance_sidecar
except ImportError:
    # Fallback for direct execution if utils is not in path, though project structure implies it should be
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.provenance import generate_provenance_sidecar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for dataset IDs
DATASET_EXCLUSION = "ds000246"
DATASET_REWARD = "ds004738"

# Unified condition mapping
# Maps raw condition labels from each dataset to a standard 'condition' column
CONDITION_MAPPING = {
    DATASET_EXCLUSION: {
        "Exclusion": "exclusion",
        "Inclusion": "inclusion",
        "exclude": "exclusion",
        "include": "inclusion",
        "Cyberball_Exclusion": "exclusion",
        "Cyberball_Inclusion": "inclusion"
    },
    DATASET_REWARD: {
        # Reward dataset typically has 'Win' vs 'Loss' or 'Anticipation'
        # We map these to a unified 'reward' schema where applicable
        # For this specific task, we focus on the 'exclusion' vs 'inclusion'
        # logic if the reward task has a social component, or we map
        # 'Win'/'Loss' to a generic 'reward' condition if needed for later analysis.
        # However, T010b specifically asks to map conditions to prepare for analysis
        # of the merged strategy.
        # We will standardize on 'condition' column values: 'exclusion', 'inclusion', 'reward', 'neutral'
        "Win": "reward",
        "Loss": "neutral",
        "Anticipation": "anticipation",
        "Outcome": "outcome"
    }
}

def load_dataset_metadata(dataset_id: str, base_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load metadata for a specific dataset.
    Looks for participants.tsv or a derived metadata file.
    """
    dataset_path = base_dir / dataset_id
    if not dataset_path.exists():
        logger.warning(f"Dataset path {dataset_path} does not exist. Skipping {dataset_id}.")
        return None

    # Try to find participants.tsv
    participants_file = dataset_path / "participants.tsv"
    if not participants_file.exists():
        logger.error(f"participants.tsv not found in {dataset_path}. BIDS structure invalid?")
        return None

    participants_data = []
    with open(participants_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            participants_data.append(row)

    return {
        "dataset_id": dataset_id,
        "path": str(dataset_path),
        "participants": participants_data
    }

def load_task_events(dataset_id: str, base_dir: Path) -> List[Dict[str, Any]]:
    """
    Load task events (events.tsv) for all subjects in the dataset.
    Returns a list of event dictionaries.
    """
    events_data = []
    dataset_path = base_dir / dataset_id

    # Scan for events.tsv files
    for tsv_file in dataset_path.rglob("events.tsv"):
        # Extract subject ID from path
        # Path structure: .../sub-<label>/func/sub-<label>_task-<label>_events.tsv
        parts = tsv_file.parts
        subject_part = None
        task_part = None
        for i, part in enumerate(parts):
            if part.startswith("sub-"):
                subject_part = part
            if part.startswith("task-"):
                task_part = part

        if not subject_part:
            continue

        subject_id = subject_part.replace("sub-", "")
        
        with open(tsv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                row['subject_id'] = subject_id
                row['dataset_id'] = dataset_id
                row['task'] = task_part.replace("task-", "") if task_part else "unknown"
                events_data.append(row)

    return events_data

def map_conditions(raw_condition: str, dataset_id: str) -> str:
    """
    Map raw condition labels to unified schema.
    """
    mapping = CONDITION_MAPPING.get(dataset_id, {})
    # Case-insensitive lookup
    lower_cond = raw_condition.lower()
    for key, value in mapping.items():
        if key.lower() == lower_cond:
            return value
    
    # Fallback: return original if no mapping found, but log warning
    logger.warning(f"No mapping found for condition '{raw_condition}' in {dataset_id}. Returning original.")
    return raw_condition

def harmonize_datasets(base_dir: Path, output_dir: Path) -> str:
    """
    Execute the Merged Dataset Strategy.
    
    1. Load metadata from ds000246 and ds004738.
    2. Create a unified list of participants with unique IDs.
    3. Add 'dataset_id' as a covariate tag.
    4. Align condition labels.
    5. Save to data/behavioral/harmonized_metadata.csv.
    
    Returns the path to the output file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "harmonized_metadata.csv"
    
    unified_records = []
    
    datasets_to_process = [DATASET_EXCLUSION, DATASET_REWARD]
    
    for ds_id in datasets_to_process:
        logger.info(f"Processing dataset: {ds_id}")
        meta = load_dataset_metadata(ds_id, base_dir)
        
        if not meta:
            logger.warning(f"Skipping {ds_id} due to missing metadata.")
            continue
        
        # Load events to get condition info if available
        events = load_task_events(ds_id, base_dir)
        
        # Build a lookup for events by subject if needed, 
        # but primarily we are harmonizing participant-level metadata here
        # and tagging them with their dataset origin.
        
        for p in meta["participants"]:
            # Create a unique participant ID to avoid collisions across datasets
            # Format: ds000246_sub-01
            original_id = p.get("participant_id", p.get("sub_id", "unknown"))
            unique_id = f"{ds_id}_{original_id}"
            
            # Determine group/condition if available in participants.tsv
            # Often participants.tsv has 'group' or 'condition' column
            raw_condition = p.get("condition", p.get("group", "unknown"))
            mapped_condition = map_conditions(raw_condition, ds_id)
            
            record = {
                "participant_id": unique_id,
                "original_id": original_id,
                "dataset_id": ds_id,  # Covariate tag
                "condition": mapped_condition,
                "age": p.get("age", ""),
                "sex": p.get("sex", p.get("gender", "")),
                "source_path": meta["path"]
            }
            unified_records.append(record)
    
    if not unified_records:
        raise RuntimeError("No records found to harmonize. Check dataset paths.")
    
    # Write unified metadata
    fieldnames = ["participant_id", "original_id", "dataset_id", "condition", "age", "sex", "source_path"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unified_records)
    
    logger.info(f"Harmonized metadata written to {output_file}")
    logger.info(f"Total participants: {len(unified_records)}")
    
    # Generate provenance sidecar
    provenance_data = {
        "pipeline_step": "harmonize_datasets",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_datasets": [DATASET_EXCLUSION, DATASET_REWARD],
        "output_file": str(output_file),
        "mapping_strategy": "Merged Dataset Strategy with Dataset ID covariate",
        "condition_mapping": CONDITION_MAPPING
    }
    
    provenance_file = output_dir / "harmonized_metadata_provenance.yaml"
    generate_provenance_sidecar(provenance_data, provenance_file)
    logger.info(f"Provenance sidecar written to {provenance_file}")
    
    return str(output_file)

def main():
    parser = argparse.ArgumentParser(description="Harmonize OpenNeuro datasets for social exclusion/reward analysis.")
    parser.add_argument(
        "--base-dir", 
        type=Path, 
        default=Path("data/raw-fmri"),
        help="Base directory containing raw OpenNeuro datasets (ds000246, ds004738)."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/behavioral"),
        help="Directory to write harmonized metadata."
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting harmonization. Base: {args.base_dir}, Output: {args.output_dir}")
    
    try:
        output_path = harmonize_datasets(args.base_dir, args.output_dir)
        print(f"Success: {output_path}")
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()