"""
Script to run the data cleaner on extracted studies and produce cleaned_studies.csv.

This script:
1. Loads raw extracted studies from data/raw/extracted_studies.json (if exists)
2. Applies inclusion criteria filtering
3. Writes included studies to data/processed/cleaned_studies.csv
4. Writes excluded studies log to data/raw/excluded_studies.log
"""

import json
import csv
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.cleaner import filter_included_studies
from utils.logging import get_logger, log_event
from utils.config import get_data_path, get_output_path

logger = get_logger(__name__)

def main():
    """Main entry point for the cleaner script."""
    
    # Define paths
    raw_data_dir = get_data_path("raw")
    processed_data_dir = get_data_path("processed")
    
    extracted_file = raw_data_dir / "extracted_studies.json"
    cleaned_file = processed_data_dir / "cleaned_studies.csv"
    excluded_log = raw_data_dir / "excluded_studies.log"
    
    # Ensure output directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not extracted_file.exists():
        logger.error(f"Input file not found: {extracted_file}")
        logger.error("Please run the extractor first to generate extracted_studies.json")
        sys.exit(1)
    
    # Load extracted studies
    logger.info(f"Loading extracted studies from {extracted_file}")
    with open(extracted_file, 'r', encoding='utf-8') as f:
        studies = json.load(f)
    
    logger.info(f"Loaded {len(studies)} studies")
    
    # Apply inclusion criteria
    logger.info("Applying inclusion criteria...")
    included_studies = filter_included_studies(studies)
    
    # Write included studies to CSV
    logger.info(f"Writing {len(included_studies)} included studies to {cleaned_file}")
    
    if included_studies:
        # Get all unique keys from all studies for CSV headers
        all_keys = set()
        for study in included_studies:
            all_keys.update(study.keys())
        
        # Sort keys for consistent ordering
        fieldnames = sorted(list(all_keys))
        
        with open(cleaned_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(included_studies)
    else:
        logger.warning("No studies met inclusion criteria. Creating empty CSV with headers.")
        # Create empty CSV with at least study_id column
        with open(cleaned_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['study_id'])
            writer.writeheader()
    
    # Write excluded studies log
    logger.info(f"Writing exclusion log to {excluded_log}")
    excluded_studies = [s for s in studies if s not in included_studies]
    
    with open(excluded_log, 'w', encoding='utf-8') as f:
        f.write(f"# Excluded Studies Log\n")
        f.write(f"# Generated: {log_event('cleaner_run', 'start')['timestamp']}\n")
        f.write(f"# Total studies: {len(studies)}\n")
        f.write(f"# Included: {len(included_studies)}\n")
        f.write(f"# Excluded: {len(excluded_studies)}\n")
        f.write(f"#\n")
        f.write(f"# Format: study_id | exclusion_reason\n")
        f.write(f"#\n")
        
        # We need to re-run the logic to capture reasons
        # For simplicity, we'll log the studies that didn't make it
        for study in excluded_studies:
            study_id = study.get("study_id", "Unknown")
            age_min = study.get("age_min")
            age_max = study.get("age_max")
            diagnosis = study.get("diagnosis", [])
            outcomes = study.get("outcomes", [])
            
            reasons = []
            
            if age_min is None or age_max is None or not (age_min <= 12 and age_max >= 6):
                reasons.append("age")
            
            if not any(any(kw in d.lower() for d in diagnosis) for kw in ["asd", "autism", "autism spectrum disorder", "autistic"]):
                reasons.append("diagnosis")
            
            if not any(any(kw in o.lower() for o in outcomes) for kw in ["social", "peer", "interaction", "communication", "relationship", "social skills", "social responsiveness", "social communication"]):
                reasons.append("outcome")
            
            reason_str = ", ".join(reasons) if reasons else "unknown"
            f.write(f"{study_id} | {reason_str}\n")
    
    logger.info("Cleaning complete!")
    logger.info(f"Output files:")
    logger.info(f"  - Included: {cleaned_file}")
    logger.info(f"  - Excluded log: {excluded_log}")
    
    return len(included_studies)

if __name__ == "__main__":
    main()
