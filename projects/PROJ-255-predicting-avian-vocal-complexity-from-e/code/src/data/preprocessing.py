import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from src.utils.config import get_project_root, get_interim_data_dir, get_processed_data_dir
from src.utils.logging import setup_logger

# Initialize logger for this module
logger = setup_logger("preprocessing")

def load_csv(file_path: Path) -> List[Dict]:
    """Load a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def save_csv(records: List[Dict], file_path: Path, fieldnames: Optional[List[str]] = None):
    """Save a list of dictionaries to a CSV file."""
    if not records:
        logger.warning(f"No records to save to {file_path}")
        # Create empty file with headers if provided, otherwise empty
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            else:
                f.write("")
        return

    if fieldnames is None:
        fieldnames = list(records[0].keys())
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def filter_species_by_min_recordings(
    input_path: Path, 
    output_path: Path, 
    excluded_path: Path,
    min_recordings_per_location: int = 5,
    location_col: str = 'location_id',
    species_col: str = 'species_id',
    record_id_col: str = 'record_id'
) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter records to keep only species that have >= min_recordings_per_location 
    valid recordings at each location.
    
    This implements the logic for T018: 
    "Filter species with <5 valid recordings per location and log exclusions."
    
    Args:
        input_path: Path to input CSV (e.g., filtered_snr.csv)
        output_path: Path to save filtered records
        excluded_path: Path to save excluded species/records
        min_recordings_per_location: Minimum count required (default 5)
        location_col: Column name for location identifier
        species_col: Column name for species identifier
        record_id_col: Column name for unique record identifier
        
    Returns:
        Tuple of (kept_records, excluded_records)
    """
    logger.info(f"Loading input data from {input_path}")
    records = load_csv(input_path)
    
    if not records:
        logger.warning("Input file is empty. Creating empty outputs.")
        save_csv([], output_path)
        save_csv([], excluded_path, fieldnames=['species_id', 'location_id', 'reason'])
        return [], []
    
    # Count records per (species, location) pair
    counts = {}
    for rec in records:
        species = rec.get(species_col, 'unknown')
        location = rec.get(location_col, 'unknown')
        key = (species, location)
        counts[key] = counts.get(key, 0) + 1
    
    # Identify valid (species, location) pairs
    valid_pairs = {k for k, v in counts.items() if v >= min_recordings_per_location}
    logger.info(f"Found {len(valid_pairs)} valid (species, location) pairs "
               f"(>= {min_recordings_per_location} recordings each)")
    
    # Separate records
    kept_records = []
    excluded_records = []
    
    for rec in records:
        species = rec.get(species_col, 'unknown')
        location = rec.get(location_col, 'unknown')
        key = (species, location)
        
        if key in valid_pairs:
            kept_records.append(rec)
        else:
            excluded_records.append({
                'record_id': rec.get(record_id_col, ''),
                species_col: species,
                location_col: location,
                'reason': f"insufficient_recordings (count={counts.get(key, 0)}, min={min_recordings_per_location})"
            })
    
    logger.info(f"Kept {len(kept_records)} records, excluded {len(excluded_records)} records")
    
    # Save outputs
    save_csv(kept_records, output_path)
    
    # For excluded file, we need specific fieldnames
    excluded_fieldnames = [record_id_col, species_col, location_col, 'reason']
    save_csv(excluded_records, excluded_path, fieldnames=excluded_fieldnames)
    
    logger.info(f"Saved filtered dataset to {output_path}")
    logger.info(f"Saved excluded records to {excluded_path}")
    
    return kept_records, excluded_records

def main():
    """
    Main entry point for T018: Filter species with <5 valid recordings per location.
    
    Reads from data/interim/filtered_snr.csv (output of T017b)
    Writes to:
      - data/interim/species_filtered.csv (kept records)
      - data/interim/species_excluded.csv (excluded records for audit trail)
    """
    root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    input_file = interim_dir / "filtered_snr.csv"
    output_file = interim_dir / "species_filtered.csv"
    excluded_file = interim_dir / "species_excluded.csv"
    
    logger.info("=" * 60)
    logger.info("T018: Species Filter by Minimum Recordings per Location")
    logger.info("=" * 60)
    
    try:
        kept, excluded = filter_species_by_min_recordings(
            input_path=input_file,
            output_path=output_file,
            excluded_path=excluded_file,
            min_recordings_per_location=5,
            location_col='location_id',
            species_col='species_id',
            record_id_col='record_id'
        )
        
        logger.info("T018 completed successfully.")
        logger.info(f"  - Input: {input_file} ({len(kept) + len(excluded)} total records)")
        logger.info(f"  - Output: {output_file} ({len(kept)} kept)")
        logger.info(f"  - Excluded: {excluded_file} ({len(excluded)} excluded)")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Ensure T017b (default SNR filter) has been run first.")
        return 1
    except Exception as e:
        logger.error(f"Error during species filtering: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
