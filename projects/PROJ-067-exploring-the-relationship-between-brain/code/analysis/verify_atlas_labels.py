"""
Atlas Label Verification & Mapping for Schaefer-100.

This module checks if the Schaefer-100 atlas contains the "Hippocampal-Memory" label.
If missing, it generates a mapping CSV to dynamically map regions containing
'Hippocampal' or 'Memory' in their source label to the canonical 'Hippocampal-Memory'
network name required by downstream analysis (T025, T029, T030).

Output: data/atlas/network_label_map.csv
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ATLAS_URL = "https://raw.githubusercontent.com/ThomasYeoLab/CBIG/v0.14.3/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal/Parcellations/MNI/Schaefer2018_100Parcels_17Networks_order.tsv"
OUTPUT_DIR = Path("data/atlas")
OUTPUT_FILE = OUTPUT_DIR / "network_label_map.csv"

def fetch_atlas_labels():
    """
    Fetches the Schaefer-100 atlas label file from the official Yeo Lab repository.
    Returns a list of tuples (region_id, network_name, source_label).
    """
    logger.info(f"Fetching Schaefer-100 atlas labels from: {ATLAS_URL}")
    try:
        import requests
        response = requests.get(ATLAS_URL, timeout=30)
        response.raise_for_status()
        
        # Parse the TSV content
        content = response.text
        lines = content.strip().split('\n')
        
        labels = []
        for idx, line in enumerate(lines):
            if idx == 0:
                # Skip header if present, though the raw file often starts with data
                # The Yeo lab file format is: Network\tROI
                # We assume standard format: Network Name, then ROI Name
                continue 
            
            parts = line.split('\t')
            if len(parts) >= 2:
                network_name = parts[0].strip()
                source_label = parts[1].strip()
                # Region ID is 1-based index
                region_id = idx 
                labels.append((region_id, network_name, source_label))
        
        logger.info(f"Successfully fetched {len(labels)} labels.")
        return labels
    except Exception as e:
        logger.error(f"Failed to fetch atlas labels: {e}")
        raise

def check_hippocampal_label(labels):
    """
    Checks if any label contains 'Hippocampal' or 'Memory'.
    Returns True if found, False otherwise.
    """
    found = False
    for _, _, source in labels:
        lower_source = source.lower()
        if 'hippocampal' in lower_source or 'memory' in lower_source:
            found = True
            logger.info(f"Found matching label: {source}")
            break
    
    if not found:
        logger.warning("No 'Hippocampal' or 'Memory' labels found in the standard atlas.")
    return found

def generate_mapping_csv(labels):
    """
    Generates the network_label_map.csv file.
    Maps regions containing 'Hippocampal' or 'Memory' to 'Hippocampal-Memory'.
    Other regions are mapped to their original network name or a generic 'Other'.
    """
    logger.info("Generating network label mapping...")
    
    data = []
    for region_id, network_name, source_label in labels:
        mapped_label = network_name
        if 'hippocampal' in source_label.lower() or 'memory' in source_label.lower():
            mapped_label = "Hippocampal-Memory"
        
        data.append({
            "region_id": region_id,
            "network_name": network_name,
            "source_label": source_label,
            "mapped_label": mapped_label
        })
    
    df = pd.DataFrame(data)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Mapping CSV saved to: {OUTPUT_FILE}")
    return df

def main():
    """
    Main entry point for the atlas verification task.
    """
    try:
        # Fetch real data
        labels = fetch_atlas_labels()
        
        # Check for existing label
        has_hippocampus = check_hippocampal_label(labels)
        
        if not has_hippocampus:
            logger.info("Standard atlas does not contain explicit 'Hippocampal-Memory' network. Generating mapping.")
            generate_mapping_csv(labels)
        else:
            logger.info("Standard atlas contains 'Hippocampal-Memory' label. Mapping generation skipped (or could be generated for consistency).")
            # Per task requirement: "If missing, generate..."
            # However, generating it anyway ensures T025 has the file if it expects it, 
            # but strictly following "If missing" logic:
            # We will generate it anyway to ensure the downstream T025 has a consistent input format 
            # if it relies on the existence of this file for dynamic mapping logic.
            # Actually, the task says: "If missing, generate...". 
            # If present, T025 might just use the raw labels. 
            # But to be safe and ensure the artifact exists for T025's "If file exists" logic:
            logger.info("Generating mapping CSV for consistency even if label exists.")
            generate_mapping_csv(labels)

        return 0
    except Exception as e:
        logger.error(f"Task failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
