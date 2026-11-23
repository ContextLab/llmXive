import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml

from src.utils.config import get_project_root, get_interim_data_dir

logger = logging.getLogger(__name__)

def load_csv(file_path: Path) -> List[Dict[str, str]]:
    """Load a CSV file into a list of dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    records = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def save_csv(file_path: Path, records: List[Dict[str, str]], fieldnames: Optional[List[str]] = None):
    """Save a list of dictionaries to a CSV file."""
    if not records:
        logger.warning(f"No records to save to {file_path}")
        # Create empty file with headers if fieldnames provided, else empty
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            else:
                f.write("")
        return

    if fieldnames is None:
        fieldnames = list(records[0].keys())

    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def filter_by_snr_threshold(
    input_path: Path,
    output_path: Path,
    exclusion_log_path: Path,
    threshold_db: float = 10.0
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Filter records based on SNR threshold.
    
    Keeps records where snr_db >= threshold_db.
    Excluded records are logged to exclusion_log_path.
    
    Args:
        input_path: Path to input CSV (noise_mapped.csv)
        output_path: Path to output CSV (filtered_snr.csv)
        exclusion_log_path: Path to log excluded records
        threshold_db: Minimum SNR threshold in dB (default 10.0)
        
    Returns:
        Tuple of (kept_records, excluded_records)
    """
    logger.info(f"Loading data from {input_path}")
    records = load_csv(input_path)
    logger.info(f"Loaded {len(records)} records")

    kept_records = []
    excluded_records = []

    for record in records:
        try:
            snr_value = float(record.get('snr_db', -999))
        except (ValueError, TypeError):
            # If SNR is missing or invalid, exclude it
            excluded_record = {
                'recording_id': record.get('recording_id', 'UNKNOWN'),
                'snr_db': record.get('snr_db', 'INVALID'),
                'threshold_applied': str(threshold_db),
                'reason': 'invalid_snr_value'
            }
            excluded_records.append(excluded_record)
            continue

        if snr_value >= threshold_db:
            kept_records.append(record)
        else:
            excluded_record = {
                'recording_id': record.get('recording_id', 'UNKNOWN'),
                'snr_db': str(snr_value),
                'threshold_applied': str(threshold_db),
                'reason': 'snr_below_threshold'
            }
            excluded_records.append(excluded_record)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Save kept records
    logger.info(f"Saving {len(kept_records)} kept records to {output_path}")
    save_csv(output_path, kept_records)

    # Save exclusion log
    if excluded_records:
        exclusion_fieldnames = ['recording_id', 'snr_db', 'threshold_applied', 'reason']
        save_csv(exclusion_log_path, excluded_records, fieldnames=exclusion_fieldnames)
        logger.info(f"Saved {len(excluded_records)} excluded records to {exclusion_log_path}")
    else:
        # Create empty exclusion log with headers
        save_csv(exclusion_log_path, [], fieldnames=['recording_id', 'snr_db', 'threshold_applied', 'reason'])
        logger.info(f"No records excluded. Created empty log at {exclusion_log_path}")

    logger.info(f"Filtering complete. Kept: {len(kept_records)}, Excluded: {len(excluded_records)}")
    return kept_records, excluded_records

def filter_species_by_min_recordings(
    input_path: Path,
    output_path: Path,
    exclusion_log_path: Path,
    min_recordings: int = 5
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Filter species with fewer than min_recordings valid recordings per location.
    
    Args:
        input_path: Path to input CSV (filtered_snr.csv)
        output_path: Path to output CSV (species_filtered.csv - kept records)
        exclusion_log_path: Path to log excluded species records
        min_recordings: Minimum number of recordings required per species per location
        
    Returns:
        Tuple of (kept_records, excluded_records)
    """
    logger.info(f"Loading data from {input_path}")
    records = load_csv(input_path)
    logger.info(f"Loaded {len(records)} records")

    # Count recordings per species per location
    location_counts: Dict[Tuple[str, str], int] = {}
    for record in records:
        species_id = record.get('species_id', 'UNKNOWN')
        # Location could be derived from lat/long or a location_id field
        # Assuming location_id or lat/long combination
        location_id = record.get('location_id', f"{record.get('latitude', 'NA')},{record.get('longitude', 'NA')}")
        key = (species_id, location_id)
        location_counts[key] = location_counts.get(key, 0) + 1

    kept_records = []
    excluded_records = []

    for record in records:
        species_id = record.get('species_id', 'UNKNOWN')
        location_id = record.get('location_id', f"{record.get('latitude', 'NA')},{record.get('longitude', 'NA')}")
        key = (species_id, location_id)
        count = location_counts[key]

        if count >= min_recordings:
            kept_records.append(record)
        else:
            excluded_record = {
                'species_id': species_id,
                'reason_for_exclusion': f'count < {min_recordings}',
                'count': str(count)
            }
            # Add to exclusion log only once per species-location combination
            if not any(r['species_id'] == species_id and r.get('location_id') == location_id for r in excluded_records):
                excluded_record['location_id'] = location_id
                excluded_records.append(excluded_record)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exclusion_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Save kept records
    logger.info(f"Saving {len(kept_records)} kept records to {output_path}")
    save_csv(output_path, kept_records)

    # Save exclusion log
    if excluded_records:
        exclusion_fieldnames = ['species_id', 'location_id', 'reason_for_exclusion', 'count']
        save_csv(exclusion_log_path, excluded_records, fieldnames=exclusion_fieldnames)
        logger.info(f"Saved {len(excluded_records)} excluded species to {exclusion_log_path}")
    else:
        save_csv(exclusion_log_path, [], fieldnames=['species_id', 'location_id', 'reason_for_exclusion', 'count'])
        logger.info(f"No species excluded. Created empty log at {exclusion_log_path}")

    logger.info(f"Species filtering complete. Kept: {len(kept_records)}, Excluded species: {len(excluded_records)}")
    return kept_records, excluded_records

def save_species_filtered_audit(
    excluded_records: List[Dict[str, str]],
    output_path: Path
):
    """
    Save the species filtering audit trail.
    
    Args:
        excluded_records: List of excluded species records
        output_path: Path to save the audit CSV
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if excluded_records:
        fieldnames = ['species_id', 'location_id', 'reason_for_exclusion', 'count']
        save_csv(output_path, excluded_records, fieldnames=fieldnames)
    else:
        save_csv(output_path, [], fieldnames=['species_id', 'location_id', 'reason_for_exclusion', 'count'])
    logger.info(f"Saved species filtering audit to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()

    # Input file from T015
    input_file = interim_dir / 'noise_mapped.csv'
    
    # Output files
    filtered_snr_file = interim_dir / 'filtered_snr.csv'
    exclusion_log_file = interim_dir / 'excluded_snr_records.csv'
    
    # Get SNR threshold from config (default 10.0)
    from src.utils.config import get_snr_threshold
    snr_threshold = get_snr_threshold()

    logger.info(f"Starting SNR filtering with threshold: {snr_threshold} dB")
    
    try:
        kept, excluded = filter_by_snr_threshold(
            input_path=input_file,
            output_path=filtered_snr_file,
            exclusion_log_path=exclusion_log_file,
            threshold_db=snr_threshold
        )
        logger.info(f"Successfully processed {len(kept) + len(excluded)} records")
        logger.info(f"Kept: {len(kept)}, Excluded: {len(excluded)}")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during filtering: {e}")
        return 1

if __name__ == '__main__':
    import sys
    from src.utils.logging import setup_logger
    setup_logger()
    sys.exit(main())
