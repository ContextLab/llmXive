"""
verify_atlas_labels.py

Task T026: Atlas Label Verification & Mapping

Checks if the Schaefer-100 atlas contains a 'Hippocampal-Memory' label.
If missing, generates a mapping file `data/atlas/network_label_map.csv`
to map regions containing 'Hippocampal' or 'Memory' in their source labels
to the canonical 'Hippocampal-Memory' network name.
"""

import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set

# Add parent directory to path to allow relative imports if run as script
# but primarily designed to be imported or run via python -m
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants derived from plan/spec
ATLAS_NAME = "Schaefer100"
TARGET_NETWORK = "Hippocampal-Memory"
OUTPUT_DIR = project_root / "data" / "atlas"
OUTPUT_FILE = OUTPUT_DIR / "network_label_map.csv"

# Path to the Schaefer-100 labels file (standard location in Schaefer downloads)
# The Schaefer-400/100 labels are typically in a file named:
# "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm_labels.txt"
# We assume the user has downloaded the atlas to data/atlas/ or similar.
# We will search for the standard filename pattern.
ATLAS_LABELS_FILENAME = "Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm_labels.txt"
ATLAS_LABELS_PATH = project_root / "data" / "atlas" / ATLAS_LABELS_FILENAME

def load_atlas_labels(file_path: Path) -> Dict[int, str]:
    """
    Loads the Schaefer atlas labels from the text file.
    Returns a dictionary mapping region_id (1-based) to label string.
    """
    labels = {}
    if not file_path.exists():
        logger.error(f"Atlas labels file not found: {file_path}")
        raise FileNotFoundError(f"Atlas labels file not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            # Schaefer format: "1\tDMN_A" or "1\tDMN_A\tNetworkName"
            # We split by tab. The first part is usually the ID, the rest is the name.
            parts = line.split('\t')
            if len(parts) < 2:
                logger.warning(f"Skipping malformed line {line_num}: {line}")
                continue
            
            try:
                region_id = int(parts[0])
                # The label is the rest of the line joined by tabs (in case of internal spaces/tabs)
                # But usually it's just parts[1]. Let's take parts[1] as the primary label.
                label = parts[1]
                labels[region_id] = label
            except ValueError:
                logger.warning(f"Skipping line {line_num} due to invalid ID: {parts[0]}")
                continue
    
    return labels

def check_target_network(labels: Dict[int, str], target: str) -> bool:
    """
    Checks if the target network name exists exactly in the labels.
    """
    return target in labels.values()

def find_mapping_candidates(labels: Dict[int, str]) -> List[Dict]:
    """
    Finds regions that contain 'Hippocampal' or 'Memory' in their source label.
    Returns a list of dicts: {region_id, source_label, mapped_label}
    """
    candidates = []
    target_keywords = ['Hippocampal', 'Memory']
    
    for region_id, source_label in labels.items():
        # Check if any keyword is in the label (case-insensitive)
        if any(kw.lower() in source_label.lower() for kw in target_keywords):
            candidates.append({
                'region_id': region_id,
                'source_label': source_label,
                'mapped_label': TARGET_NETWORK,
                'network_name': TARGET_NETWORK # The canonical network name we are mapping to
            })
    
    return candidates

def generate_mapping_csv(candidates: List[Dict], output_path: Path):
    """
    Generates the network_label_map.csv file.
    Columns: region_id, network_name, source_label, mapped_label
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['region_id', 'network_name', 'source_label', 'mapped_label'])
        writer.writeheader()
        writer.writerows(candidates)
    
    logger.info(f"Generated mapping file: {output_path} with {len(candidates)} entries.")

def main():
    """
    Main entry point for T026.
    1. Load Schaefer-100 labels.
    2. Check for 'Hippocampal-Memory'.
    3. If missing, find candidates and generate CSV.
    """
    logger.info(f"Starting Atlas Label Verification (Task T026)...")
    logger.info(f"Config Summary: {get_config_summary()}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load labels
    try:
        labels = load_atlas_labels(ATLAS_LABELS_PATH)
    except FileNotFoundError as e:
        logger.critical(str(e))
        logger.critical("Cannot proceed without the Schaefer-100 labels file.")
        logger.critical("Please ensure the atlas is downloaded to: " + str(ATLAS_LABELS_PATH))
        sys.exit(1)

    logger.info(f"Loaded {len(labels)} atlas regions.")

    # Check for exact match
    has_target = check_target_network(labels, TARGET_NETWORK)

    if has_target:
        logger.info(f"Success: The atlas already contains the target label '{TARGET_NETWORK}'.")
        logger.info("No mapping file needed.")
        # If the file exists from a previous run, we might want to clean it up or leave it?
        # The task says "If missing, generate...". If present, we don't generate.
        if OUTPUT_FILE.exists():
            logger.info(f"Removing stale mapping file: {OUTPUT_FILE}")
            OUTPUT_FILE.unlink()
        return 0

    logger.warning(f"Target label '{TARGET_NETWORK}' NOT found in atlas.")
    logger.info("Searching for mapping candidates (labels containing 'Hippocampal' or 'Memory')...")

    candidates = find_mapping_candidates(labels)

    if not candidates:
        logger.warning(f"No candidates found for mapping to '{TARGET_NETWORK}'.")
        logger.warning("The analysis in T025 may fail if it strictly requires this network.")
        # We still create an empty file or fail? The task says "generate ... with columns".
        # An empty file is valid but might cause downstream errors.
        # We will generate the file with headers only.
        generate_mapping_csv([], OUTPUT_FILE)
        return 0

    logger.info(f"Found {len(candidates)} candidate regions.")
    generate_mapping_csv(candidates, OUTPUT_FILE)

    logger.info("Task T026 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())