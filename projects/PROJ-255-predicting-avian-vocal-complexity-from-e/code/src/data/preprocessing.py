import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir

logger = logging.getLogger(__name__)

def load_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_csv(data: List[Dict[str, str]], file_path: Path) -> None:
    """Save a list of dictionaries to a CSV file."""
    if not data:
        logger.warning(f"Saving empty CSV to {file_path}")
        # Create file with headers if we know them, otherwise empty
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    fieldnames = list(data[0].keys())
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def filter_by_snr_threshold(
    data: List[Dict[str, str]], 
    threshold_db: float = 10.0
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Filter records based on SNR threshold.
    Returns (kept_records, excluded_records).
    """
    kept = []
    excluded = []
    
    for record in data:
        try:
            snr = float(record.get('snr_db', -999))
            if snr > threshold_db:
                kept.append(record)
            else:
                excluded.append(record)
        except (ValueError, TypeError):
            # Invalid SNR, exclude
            excluded.append(record)
            
    return kept, excluded

def filter_species_by_min_recordings(
    data: List[Dict[str, str]], 
    min_count: int = 5
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Filter species that have at least min_count valid recordings per location.
    
    Returns:
        Tuple of (kept_records, excluded_records)
    """
    # Count records per species
    species_counts: Dict[str, int] = {}
    for record in data:
        species_id = record.get('species_id', 'unknown')
        species_counts[species_id] = species_counts.get(species_id, 0) + 1
    
    # Identify species to exclude
    excluded_species = {sp for sp, count in species_counts.items() if count < min_count}
    
    kept = []
    excluded = []
    
    for record in data:
        species_id = record.get('species_id', 'unknown')
        if species_id in excluded_species:
            excluded.append(record)
        else:
            kept.append(record)
            
    return kept, excluded

def save_species_filtered_audit(
    excluded_records: List[Dict[str, str]], 
    output_path: Path
) -> None:
    """
    Save the audit trail of species excluded by the filtering logic.
    This satisfies T018b requirement.
    """
    save_csv(excluded_records, output_path)
    logger.info(f"Saved {len(excluded_records)} excluded species records to {output_path}")

def main():
    """
    Main entry point for T018b: Species filtering audit trail generation.
    Reads filtered SNR data, applies species count filter, and saves audit.
    """
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    # Input: filtered SNR data from T017b
    input_path = interim_dir / "filtered_snr.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Run T017b first.")
        return

    logger.info(f"Loading data from {input_path}")
    data = load_csv(input_path)
    logger.info(f"Loaded {len(data)} records")
    
    # Apply species filtering (T018 logic)
    kept, excluded = filter_species_by_min_recordings(data, min_count=5)
    
    logger.info(f"Kept {len(kept)} records, excluded {len(excluded)} records due to species count < 5")
    
    # Save the audit trail (T018b specific requirement)
    audit_output_path = interim_dir / "species_filtered.csv"
    save_species_filtered_audit(excluded, audit_output_path)
    
    # Also save the kept records for downstream processing (T018 logic continuation)
    kept_output_path = interim_dir / "species_kept.csv"
    save_csv(kept, kept_output_path)
    
    logger.info("Species filtering complete.")

if __name__ == "__main__":
    main()
