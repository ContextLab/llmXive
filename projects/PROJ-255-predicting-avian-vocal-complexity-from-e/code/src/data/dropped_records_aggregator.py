import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

from src.utils.config import get_project_root, get_interim_data_dir

logger = logging.getLogger(__name__)

def read_dropped_csv(file_path: Path) -> List[Dict[str, str]]:
    """
    Read a CSV file containing dropped records.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of dictionaries representing the records
    """
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}. Returning empty list.")
        return []
    
    records = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise
    
    return records

def aggregate_dropped_records(
    osm_missing_path: Optional[Path] = None,
    snr_filtered_path: Optional[Path] = None,
    species_filtered_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Aggregate dropped records from multiple filtering stages into a single CSV.
    
    This satisfies US-1 Acceptance Scenario 3 by collecting all excluded records
    from:
    1. T015: Missing OSM data (dropped_missing_osm.csv)
    2. T017: SNR filtering (filtered_snr.csv exclusion log)
    3. T018: Species count filtering (species_filtered.csv)
    
    Args:
        osm_missing_path: Path to T015 dropped records
        snr_filtered_path: Path to T017 dropped/excluded records
        species_filtered_path: Path to T018 dropped records
        output_path: Path for the aggregated output file
        
    Returns:
        Path to the aggregated dropped records file
    """
    if output_path is None:
        output_path = get_interim_data_dir() / "dropped_records.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_dropped = []
    
    # Collect from T015: Missing OSM
    if osm_missing_path is None:
        osm_missing_path = get_interim_data_dir() / "dropped_missing_osm.csv"
    
    if osm_missing_path.exists():
        osm_records = read_dropped_csv(osm_missing_path)
        for record in osm_records:
            record['_exclusion_reason'] = 'missing_osm'
            record['_exclusion_task'] = 'T015'
        all_dropped.extend(osm_records)
        logger.info(f"Collected {len(osm_records)} records from T015 (missing OSM)")
    else:
        logger.warning(f"T015 dropped file not found: {osm_missing_path}")
    
    # Collect from T017: SNR Filtering
    # The SNR filter typically logs excluded records to a separate file or
    # the filtered output contains only passing records. We need to check
    # if there's an exclusion log or reconstruct from the process.
    # Based on T017a implementation, we look for the exclusion log.
    if snr_filtered_path is None:
        # Try common exclusion log names
        exclusion_candidates = [
            get_interim_data_dir() / "snr_excluded.csv",
            get_interim_data_dir() / "dropped_snr.csv",
            get_interim_data_dir() / "excluded_snr.csv"
        ]
        snr_excluded_path = None
        for candidate in exclusion_candidates:
            if candidate.exists():
                snr_excluded_path = candidate
                break
        
        if snr_excluded_path is None:
            # If no explicit exclusion log, check if the filtering script
            # logged to a specific location or if we need to reconstruct
            logger.warning("No SNR exclusion log found. Checking if filtered_snr.csv exists...")
            filtered_path = get_interim_data_dir() / "filtered_snr.csv"
            if filtered_path.exists():
                logger.info("filtered_snr.csv exists but exclusion log missing. "
                          "Records in filtered file passed SNR check. "
                          "Excluded records may be in logs or need reconstruction.")
                # We cannot reconstruct without the original pre-filter dataset
                # This is a known limitation - the exclusion log should exist
    else:
        if snr_filtered_path.exists():
            snr_records = read_dropped_csv(snr_filtered_path)
            for record in snr_records:
                record['_exclusion_reason'] = 'snr_below_threshold'
                record['_exclusion_task'] = 'T017'
            all_dropped.extend(snr_records)
            logger.info(f"Collected {len(snr_records)} records from T017 (SNR filter)")
        else:
            logger.warning(f"T017 dropped file not found: {snr_filtered_path}")
    
    # Collect from T018: Species Filtering
    if species_filtered_path is None:
        species_filtered_path = get_interim_data_dir() / "species_filtered.csv"
    
    if species_filtered_path.exists():
        species_records = read_dropped_csv(species_filtered_path)
        for record in species_records:
            record['_exclusion_reason'] = 'insufficient_species_records'
            record['_exclusion_task'] = 'T018'
        all_dropped.extend(species_records)
        logger.info(f"Collected {len(species_records)} records from T018 (species filter)")
    else:
        logger.warning(f"T018 dropped file not found: {species_filtered_path}")
    
    # Write aggregated output
    if all_dropped:
        # Ensure consistent columns
        fieldnames = []
        if all_dropped:
            # Get all keys from first record and add exclusion info
            base_keys = list(all_dropped[0].keys())
            fieldnames = [k for k in base_keys if k not in ['_exclusion_reason', '_exclusion_task']]
            fieldnames.extend(['_exclusion_reason', '_exclusion_task'])
        else:
            fieldnames = ['_exclusion_reason', '_exclusion_task']
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_dropped)
        
        logger.info(f"Aggregated {len(all_dropped)} dropped records to {output_path}")
    else:
        # Write empty file with headers if no dropped records found
        logger.warning("No dropped records found from any source. Writing empty file.")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['_exclusion_reason', '_exclusion_task'])
            writer.writeheader()
    
    return output_path

def main():
    """
    Main entry point for T021: Aggregate dropped records.
    
    This function orchestrates the aggregation of all dropped records from
    the three main filtering stages (T015, T017, T018) into a single
    dropped_records.csv file.
    """
    logger.info("Starting T021: Dropped Records Aggregation")
    
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    # Define paths based on previous task outputs
    osm_missing_path = interim_dir / "dropped_missing_osm.csv"
    snr_excluded_path = interim_dir / "snr_excluded.csv"  # Expected from T017
    species_filtered_path = interim_dir / "species_filtered.csv"
    output_path = interim_dir / "dropped_records.csv"
    
    # Perform aggregation
    result_path = aggregate_dropped_records(
        osm_missing_path=osm_missing_path,
        snr_filtered_path=snr_excluded_path,
        species_filtered_path=species_filtered_path,
        output_path=output_path
    )
    
    logger.info(f"T021 completed. Aggregated file: {result_path}")
    
    # Verify output exists
    if result_path.exists():
        logger.info(f"Output file exists: {result_path.stat().st_size} bytes")
    else:
        logger.error("Output file was not created!")
        raise FileNotFoundError(f"Expected output not created: {result_path}")
    
    return result_path

if __name__ == "__main__":
    # Setup basic logging if run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    main()
