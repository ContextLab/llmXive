"""
Helper script to generate the ground truth file for synthetic data.
This script should be run after generate_synthetic_data.py to create
the ground truth JSON based on the metadata generated during synthesis.

The synthetic generator (T026) writes a metadata file indicating which records
were intentionally made inconsistent. This script reads that metadata and
formats it into the standard ground truth JSON structure expected by T029.
"""
import json
import logging
import sys
from pathlib import Path

from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    metadata_path = project_root / "data" / "synthetic" / "metadata.json"
    output_path = project_root / "data" / "synthetic" / "ground_truth.json"

    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}. Run generate_synthetic_data.py first.")
        return 1

    logger.info(f"Reading metadata from {metadata_path}")
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    # Expected metadata structure: {"records": [{"id": "...", "is_inconsistent": true/false}, ...]}
    # We assume the generator already created this structure.
    # If the generator creates a different structure, we adapt here.
    
    # If the metadata contains a list of records with inconsistency flags, we just copy it.
    # If it's a different format, we transform it.
    
    ground_truth = {"records": []}
    
    if "records" in metadata:
        ground_truth["records"] = metadata["records"]
    else:
        # Fallback: try to infer from a list of summaries if metadata is just the summaries list
        # But metadata should be separate.
        logger.warning("Metadata does not contain 'records' key. Attempting to parse as list.")
        if isinstance(metadata, list):
            for i, item in enumerate(metadata):
                # Assume 'is_inconsistent' is a field in the item, or default to False if not present
                is_inc = item.get("is_inconsistent", False)
                record_id = item.get("id", str(i))
                ground_truth["records"].append({"id": record_id, "is_inconsistent": is_inc})
        else:
            logger.error("Metadata format unrecognized.")
            return 1

    logger.info(f"Writing ground truth to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Ground truth generated with {len(ground_truth['records'])} records.")
    return 0

if __name__ == "__main__":
    sys.exit(main())