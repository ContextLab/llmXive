"""
Preprocessing script for cosmic ray event data.

Filters events with E > 50 EeV, excludes missing data, and logs exclusions.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from utils.logging import setup_logger, log_event_exclusion

def main():
    logger = setup_logger("preprocess")
    logger.info("Starting preprocessing pipeline")

    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load combined data (assuming previous step concatenated Auger+TA)
    # For this script, we assume a single input file 'combined_events.csv'
    input_file = raw_dir / "combined_events.csv"

    if not input_file.exists():
        logger.error(f"Input file {input_file} not found. Run download_events.py first.")
        sys.exit(1)

    df = pd.read_csv(input_file)

    initial_count = len(df)
    logger.info(f"Loaded {initial_count} events from {input_file}")

    # Filter by energy > 50 EeV
    if 'energy' not in df.columns:
        logger.error("Energy column missing in input data.")
        sys.exit(1)

    df = df[df['energy'] > 50.0]
    energy_filtered = initial_count - len(df)
    log_event_exclusion(logger, "Energy <= 50 EeV", energy_filtered)

    # Exclude missing coordinates
    if 'ra' in df.columns and 'dec' in df.columns:
        ra_mask = df['ra'].notna()
        dec_mask = df['dec'].notna()
        coord_mask = ra_mask & dec_mask
        df = df[coord_mask]
        coord_filtered = initial_count - energy_filtered - len(df)
        log_event_exclusion(logger, "Missing RA/Dec", coord_filtered)
    else:
        logger.error("RA/Dec columns missing in input data.")
        sys.exit(1)

    # Exclude missing energy
    if 'energy' in df.columns:
        e_mask = df['energy'].notna()
        df = df[e_mask]
        e_filtered = initial_count - energy_filtered - coord_filtered - len(df)
        log_event_exclusion(logger, "Missing Energy", e_filtered)

    final_count = len(df)
    logger.info(f"Preprocessing complete. Retained {final_count} events ({initial_count - final_count} excluded).")

    # Save processed data
    output_file = processed_dir / "events_filtered.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"Saved filtered events to {output_file}")

if __name__ == "__main__":
    main()
