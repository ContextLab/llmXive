"""
T018b: Audit Trail Generator
Generates data/interim/species_filtered.csv containing all species excluded by T018.

T018 filters species with <5 valid recordings per location.
This script identifies those excluded species and writes them to the audit trail.
"""
import os
import sys
import logging
import csv
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import load_csv, save_csv
from src.utils.config import get_project_root, get_interim_data_dir
from src.utils.logging import setup_logger

MIN_RECORDINGS_PER_LOCATION = 5

def main():
    """
    Generate the audit trail CSV for species excluded by T018.
    
    Reads the input data (filtered_snr.csv), calculates record counts per species per location,
    identifies species that fail the threshold, and writes them to species_filtered.csv.
    """
    # Setup logging
    logger = setup_logger("T018b_AuditTrail")
    logger.info("Starting T018b Audit Trail generation")
    
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    input_file = interim_dir / "filtered_snr.csv"
    output_file = interim_dir / "species_filtered.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T017b has been executed to generate filtered_snr.csv")
        sys.exit(1)
    
    logger.info(f"Reading input from: {input_file}")
    rows = load_csv(str(input_file))
    
    if not rows:
        logger.warning("Input file is empty. Creating empty audit trail.")
        save_csv(str(output_file), [], ["species_id", "location_id", "recording_count", "exclusion_reason"])
        logger.info(f"Audit trail created (empty): {output_file}")
        return
    
    # Count recordings per species per location
    # Structure: {(species_id, location_id): count}
    species_location_counts = defaultdict(int)
    species_location_records = defaultdict(list)
    
    for row in rows:
        species_id = row.get("species_id")
        location_id = row.get("location_id")
        
        if not species_id or not location_id:
            continue
        
        key = (species_id, location_id)
        species_location_counts[key] += 1
        species_location_records[key].append(row)
    
    # Identify excluded species/locations
    excluded_records = []
    included_species_locations = set()
    
    for (species_id, location_id), count in species_location_counts.items():
        if count < MIN_RECORDINGS_PER_LOCATION:
            # This species-location pair is excluded
            # Add all records for this pair to the excluded list
            for record in species_location_records[(species_id, location_id)]:
                excluded_records.append({
                    "species_id": species_id,
                    "location_id": location_id,
                    "recording_count": count,
                    "exclusion_reason": f"Less than {MIN_RECORDINGS_PER_LOCATION} recordings at location"
                })
        else:
            included_species_locations.add((species_id, location_id))
    
    # Also identify species that are completely excluded (no locations met threshold)
    # This is the primary "species filtered" list
    all_species = set(row.get("species_id") for row in rows if row.get("species_id"))
    kept_species = set(spec_id for (spec_id, loc_id) in included_species_locations)
    completely_excluded_species = all_species - kept_species
    
    # Build the audit trail: all records belonging to completely excluded species
    # OR records where the species-location pair failed the threshold
    audit_rows = []
    
    # We need to track which species were excluded due to low counts at ALL their locations
    species_location_summary = defaultdict(lambda: {"total_locations": 0, "valid_locations": 0})
    
    for (species_id, location_id), count in species_location_counts.items():
        species_location_summary[species_id]["total_locations"] += 1
        if count >= MIN_RECORDINGS_PER_LOCATION:
            species_location_summary[species_id]["valid_locations"] += 1
    
    # Identify species that have NO valid locations
    species_with_no_valid_locations = set()
    for species_id, summary in species_location_summary.items():
        if summary["valid_locations"] == 0 and summary["total_locations"] > 0:
            species_with_no_valid_locations.add(species_id)
    
    # Collect all records for species that have no valid locations
    for row in rows:
        species_id = row.get("species_id")
        location_id = row.get("location_id")
        count = species_location_counts.get((species_id, location_id), 0)
        
        if species_id in species_with_no_valid_locations:
            audit_rows.append({
                "species_id": species_id,
                "location_id": location_id,
                "recording_count": count,
                "exclusion_reason": f"Species has no locations with >= {MIN_RECORDINGS_PER_LOCATION} recordings"
            })
    
    # Sort by species_id for readability
    audit_rows.sort(key=lambda x: (x["species_id"], x["location_id"]))
    
    # Define columns
    columns = ["species_id", "location_id", "recording_count", "exclusion_reason"]
    
    logger.info(f"Writing {len(audit_rows)} excluded records to: {output_file}")
    save_csv(str(output_file), audit_rows, columns)
    
    logger.info(f"T018b Audit Trail complete. Excluded {len(species_with_no_valid_locations)} species.")
    print(f"Audit trail generated: {output_file}")
    print(f"Total excluded records: {len(audit_rows)}")
    print(f"Excluded species count: {len(species_with_no_valid_locations)}")

if __name__ == "__main__":
    main()