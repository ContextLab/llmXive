"""
Runner script for T029: Execute descriptor computation on validated data.

This script loads the validated composition data from data/processed/validated_compositions.csv,
computes thermodynamic descriptors (ΔHmix, δ, VEC, Δχ) using the existing 
code/descriptor_computation module, and writes the results to data/processed/computed_descriptors.csv.

Dependencies:
- code/descriptor_computation.py (must exist with compute_descriptors function)
- data/metadata/descriptor_sources.yaml (must exist with elemental property tables)
- data/processed/validated_compositions.csv (must exist from T025)

Output:
- data/processed/computed_descriptors.csv: CSV with composition, gfa_label, and all computed descriptors.
"""
import os
import csv
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from existing module
from descriptor_computation import (
    configure_logging,
    load_descriptor_sources,
    compute_descriptors,
    calculate_enthalpy_of_mixing,
    calculate_atomic_size_difference,
    calculate_valence_electron_concentration,
    calculate_electronegativity_difference
)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "validated_compositions.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "computed_descriptors.csv"
METADATA_FILE = PROJECT_ROOT / "data" / "metadata" / "descriptor_sources.yaml"
LOG_FILE = PROJECT_ROOT / "results" / "validation" / "descriptor_computation.log"

def ensure_directories():
    """Ensure output directories exist."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_validated_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load validated composition data from CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        raise ValueError("Input file is empty or contains no data rows.")
    
    return data

def write_output(output_path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]):
    """Write computed descriptors to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """Main entry point for T029."""
    # Configure logging
    configure_logging(log_file=str(LOG_FILE))
    logger = logging.getLogger(__name__)
    logger.info("Starting descriptor computation pipeline (T029)")

    try:
        # Ensure directories exist
        ensure_directories()

        # Load descriptor sources
        logger.info(f"Loading descriptor sources from {METADATA_FILE}")
        descriptor_sources = load_descriptor_sources(METADATA_FILE)

        # Load validated data
        logger.info(f"Loading validated data from {INPUT_FILE}")
        input_data = load_validated_data(INPUT_FILE)
        logger.info(f"Loaded {len(input_data)} samples")

        # Process each sample
        computed_rows = []
        skipped_count = 0

        for idx, sample in enumerate(input_data):
            try:
                # Extract composition and label
                composition_str = sample.get('composition', '')
                gfa_label = sample.get('gfa_label', '')

                if not composition_str:
                    logger.warning(f"Sample {idx}: Missing composition, skipping")
                    skipped_count += 1
                    continue

                # Compute descriptors
                descriptors = compute_descriptors(
                    composition_str,
                    descriptor_sources=descriptor_sources
                )

                if descriptors is None:
                    logger.warning(f"Sample {idx}: Computation failed for '{composition_str}', skipping")
                    skipped_count += 1
                    continue

                # Build output row
                row = {
                    'composition': composition_str,
                    'gfa_label': gfa_label
                }
                
                # Add computed descriptors
                for key, value in descriptors.items():
                    row[key] = value

                computed_rows.append(row)

            except Exception as e:
                logger.error(f"Sample {idx}: Error processing '{sample.get('composition', '')}': {e}")
                skipped_count += 1
                continue

        # Write output
        if computed_rows:
            # Determine fieldnames
            fieldnames = ['composition', 'gfa_label']
            # Add all descriptor keys found
            descriptor_keys = set()
            for row in computed_rows:
                descriptor_keys.update(k for k in row.keys() if k not in ['composition', 'gfa_label'])
            fieldnames.extend(sorted(descriptor_keys))

            write_output(OUTPUT_FILE, computed_rows, fieldnames)
            logger.info(f"Successfully wrote {len(computed_rows)} rows to {OUTPUT_FILE}")
            logger.info(f"Skipped {skipped_count} samples due to errors or missing data")
        else:
            logger.error("No valid rows computed. Output file not created.")
            raise RuntimeError("No valid data to write.")

        logger.info("T029 completed successfully")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()