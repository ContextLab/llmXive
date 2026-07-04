import os
import sys
import csv
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Adjust imports based on project structure
if 'code' in os.getcwd():
    sys.path.insert(0, os.getcwd())
from src.utils.logging import get_logger, info, warning, error
from src.utils.state_manager import update_state_artifact, get_state_file_path

logger = get_logger(__name__)
PROJECT_ID = "PROJ-206-statistical-analysis-of-publicly-availab"

def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_poll_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load raw poll data from a CSV file."""
    data = []
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        return data
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    logger.info(f"Loaded {len(data)} rows from {input_path}")
    return data

def harmonize_dates(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Parse and standardize date formats."""
    harmonized = []
    for row in data:
        try:
            # Handle common date formats
            date_str = row.get('date', '')
            # Try ISO format first
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
            else:
                # Try common US formats
                for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Fallback: skip or log warning
                    warning(f"Could not parse date: {date_str}")
                    continue
            
            row['date_parsed'] = dt
            row['date_iso'] = dt.strftime('%Y-%m-%d')
            harmonized.append(row)
        except Exception as e:
            warning(f"Error parsing date in row: {row} - {e}")
            continue
    return harmonized

def bin_data_weekly(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Bin data into weekly intervals."""
    # Group by week start date
    weekly_bins = {}
    for row in data:
        if 'date_parsed' not in row:
            continue
        dt = row['date_parsed']
        # Calculate week start (Monday)
        week_start = dt - timedelta(days=dt.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in weekly_bins:
            weekly_bins[week_key] = []
        weekly_bins[week_key].append(row)
    
    # Aggregate or select representative data per bin
    # For simplicity, we keep all rows but add a 'week_start' column
    # In a real scenario, we might average vote_share per week per pollster
    binned_data = []
    for row in data:
        if 'date_parsed' in row:
            dt = row['date_parsed']
            week_start = dt - timedelta(days=dt.weekday())
            row['week_start'] = week_start.strftime('%Y-%m-%d')
        binned_data.append(row)
    
    return binned_data

def check_data_sufficiency(data: List[Dict[str, Any]], election_date: str) -> bool:
    """Check if data is sufficient for analysis."""
    # Check for <5 polls in 30 days preceding election
    # Check for <3 distinct cycles
    # This is a simplified check
    if len(data) < 5:
        warning("Insufficient data: less than 5 polls total.")
        return False
    
    # Check distinct cycles (simplified: distinct years)
    cycles = set()
    for row in data:
        if 'date_parsed' in row:
            cycles.add(row['date_parsed'].year)
    if len(cycles) < 3:
        warning("Insufficient data: less than 3 distinct election cycles.")
        return False
    
    return True

def check_global_poll_count(data: List[Dict[str, Any]]) -> bool:
    """Check if total poll count is >= 500."""
    if len(data) < 500:
        error(f"Global poll count check failed: {len(data)} < 500")
        return False
    return True

def harmonize_and_bin(input_path: Path, output_path: Path) -> bool:
    """Main harmonization and binning logic."""
    data = load_raw_poll_data(input_path)
    if not data:
        return False
    
    harmonized = harmonize_dates(data)
    if not harmonized:
        return False
    
    binned = bin_data_weekly(harmonized)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if binned:
            fieldnames = list(binned[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(binned)
    
    logger.info(f"Wrote harmonized data to {output_path}")
    return True

def main():
    """Main entry point for harmonization."""
    logging.basicConfig(level=logging.INFO)
    
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("state/projects").mkdir(parents=True, exist_ok=True)
    
    input_path = Path("data/processed/poll_data_raw.csv")
    output_path = Path("data/processed/poll_data_cleaned.csv")
    
    if not input_path.exists():
        error(f"Input file not found: {input_path}. Run download.py first.")
        return 1
    
    logger.info("Starting harmonization...")
    
    # Perform checks
    raw_data = load_raw_poll_data(input_path)
    if not check_global_poll_count(raw_data):
        return 1
    
    if not harmonize_and_bin(input_path, output_path):
        return 1
    
    # Update state with hash of cleaned file
    cleaned_hash = compute_sha256(output_path)
    update_state_artifact(
        project_id=PROJECT_ID,
        artifact_path=str(output_path.relative_to(Path.cwd())),
        hash_value=cleaned_hash,
        timestamp=datetime.now().isoformat()
    )
    logger.info(f"Updated state for {output_path} with hash {cleaned_hash}")
    
    logger.info("Harmonization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
