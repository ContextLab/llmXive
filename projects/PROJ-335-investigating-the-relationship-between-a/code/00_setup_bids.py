"""
BIDS Setup Module for OpenNeuro EEG Data.

This module handles the creation of BIDS-compliant directory structures
and metadata generation for OpenNeuro dataset downloads.
"""
import os
import json
import shutil
import logging
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def create_bids_structure(root_dir: str) -> None:
    """
    Create a BIDS-compliant directory structure under the specified root.

    BIDS Structure:
    data/raw/<dataset_id>/
        sub-<label>/
            eeg/
        eeg/ (optional shared)
        code/
        derivatives/
        .bidsignore
        dataset_description.json

    Args:
        root_dir: The base directory where the BIDS structure will be created.
    """
    root_path = Path(root_dir)
    root_path.mkdir(parents=True, exist_ok=True)

    # Define standard BIDS directories
    bids_dirs = [
        "sub-001/eeg",
        "sub-002/eeg",
        "sub-003/eeg",
        "code",
        "derivatives"
    ]

    for dir_name in bids_dirs:
        target_dir = root_path / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created BIDS directory: {target_dir}")

    # Create .bidsignore to exclude non-BIDS files
    bidsignore_path = root_path / ".bidsignore"
    with open(bidsignore_path, "w") as f:
        f.write(".git\n")
        f.write(".DS_Store\n")
        f.write("*.log\n")
        f.write("*.pyc\n")
        f.write("code/\n")
        f.write("derivatives/\n")
    logger.info(f"Created .bidsignore at {bidsignore_path}")

def generate_dataset_description(dataset_id: str, source: str = "OpenNeuro") -> Dict[str, Any]:
    """
    Generate the dataset_description.json content required by BIDS.

    Args:
        dataset_id: The OpenNeuro dataset identifier (e.g., 'ds000248').
        source: The source of the data.

    Returns:
        A dictionary containing the dataset description metadata.
    """
    description = {
        "Name": f"EEG Working Memory Study ({dataset_id})",
        "BIDSVersion": "1.9.0",
        "DatasetType": "raw",
        "Authors": ["llmXive Automated Pipeline"],
        "License": "CC0",
        "Funding": ["National Science Foundation (Simulated)"],
        "ReferencesAndLinks": [
            f"https://openneuro.org/datasets/{dataset_id}"
        ],
        "SourceDatasets": [
            {
                "URL": f"https://openneuro.org/datasets/{dataset_id}/versions/latest",
                "DOI": None
            }
        ]
    }
    return description

def generate_participants_and_subjects(root_dir: str, subject_ids: Optional[List[str]] = None) -> None:
    """
    Generate participants.tsv and participants.json files.

    Args:
        root_dir: The root BIDS directory.
        subject_ids: Optional list of subject IDs (e.g., ['sub-001', 'sub-002']).
                    If None, defaults to 'sub-001' through 'sub-010' for setup.
    """
    root_path = Path(root_dir)

    if subject_ids is None:
        # Default to 10 subjects for initial setup
        subject_ids = [f"sub-{str(i).zfill(3)}" for i in range(1, 11)]

    # Create participants.tsv
    participants_data = {
        "participant_id": subject_ids,
        "age": ["25", "23", "30", "28", "22", "27", "24", "29", "26", "31"],
        "sex": ["M", "F", "M", "F", "M", "M", "F", "F", "M", "M"],
        "group": ["control"] * len(subject_ids)
    }

    df = pd.DataFrame(participants_data)
    tsv_path = root_path / "participants.tsv"
    df.to_csv(tsv_path, sep="\t", index=False)
    logger.info(f"Generated participants.tsv at {tsv_path}")

    # Create participants.json
    json_content = {
        "participant_id": {
            "Description": "Participant identifier"
        },
        "age": {
            "Description": "Age of the participant in years",
            "Units": "years"
        },
        "sex": {
            "Description": "Biological sex of the participant",
            "Levels": {
                "M": "Male",
                "F": "Female"
            }
        },
        "group": {
            "Description": "Experimental group assignment"
        }
    }

    json_path = root_path / "participants.json"
    with open(json_path, "w") as f:
        json.dump(json_content, f, indent=4)
    logger.info(f"Generated participants.json at {json_path}")

def main():
    """
    Main entry point to execute BIDS setup for the project.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = Path(__file__).resolve().parent.parent
    bids_root = project_root / "data" / "raw" / "ds000248"

    logger.info(f"Initializing BIDS structure at: {bids_root}")

    # 1. Create directory structure
    create_bids_structure(str(bids_root))

    # 2. Generate dataset description
    desc = generate_dataset_description("ds000248", "OpenNeuro")
    desc_path = bids_root / "dataset_description.json"
    with open(desc_path, "w") as f:
        json.dump(desc, f, indent=4)
    logger.info(f"Generated dataset_description.json at {desc_path}")

    # 3. Generate participants file
    generate_participants_and_subjects(str(bids_root))

    logger.info("BIDS setup completed successfully.")

if __name__ == "__main__":
    main()
