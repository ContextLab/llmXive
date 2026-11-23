"""
Reference Generator Service for T039.

Implements FR-008 and US-3 requirements:
1. Validates independence of kappa source via IndependenceValidator.
2. Aggregates validated kappa values and metadata.
3. Outputs the final reference file `data/derived/reference/κ_values.csv`.
"""
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.lib.config import get_config
from src.services.independence_validator import (
    setup_logger,
    load_trajectory_ids,
    load_kappa_trajectory_ids,
    validate_independence,
    FatalError
)

def generate_reference_output(
    kappa_file_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Reads the validated kappa values, ensures the output directory exists,
    and writes the final reference CSV.

    Args:
        kappa_file_path: Path to the validated kappa values CSV (from T057).
        output_path: Path for the final output CSV.
        logger: Logger instance.
    """
    logger.info(f"Generating reference output at {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read input and write output (validation already done by T057/T039 validator)
    # We simply copy/normalize the validated data to the final location.
    # In a more complex scenario, we might add metadata columns here.
    
    input_rows = []
    with open(kappa_file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise ValueError("Input kappa file is empty or has no header.")
        for row in reader:
            input_rows.append(row)
    
    if not input_rows:
        logger.warning("Input kappa file contains no data rows. Output will be empty.")
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(input_rows)
    
    logger.info(f"Reference output written successfully to {output_path}")
    logger.info(f"Total rows written: {len(input_rows)}")

def main() -> None:
    """
    Main entry point for Reference Generator.
    1. Loads metadata and kappa IDs.
    2. Validates independence (FR-008).
    3. Generates the final reference output.
    """
    logger = setup_logger()
    config = get_config()
    
    # Paths
    metadata_path = config.data_metadata_dir / "trajectory_ids.json"
    kappa_input_path = config.data_derived_ref_dir / "kappa_values.csv"
    kappa_output_path = config.data_derived_ref_dir / "κ_values.csv"
    
    try:
        # 1. Load IDs for validation
        logger.info("Step 1: Loading trajectory IDs for independence check...")
        meta_ids = load_trajectory_ids(metadata_path)
        kappa_ids = load_kappa_trajectory_ids(kappa_input_path)
        
        # 2. Validate Independence (FR-008)
        # This will raise FatalError if not independent, halting the pipeline.
        logger.info("Step 2: Validating independence of sources...")
        validate_independence(meta_ids, kappa_ids, logger)
        
        # 3. Generate Output
        logger.info("Step 3: Generating final reference output...")
        generate_reference_output(kappa_input_path, kappa_output_path, logger)
        
        logger.info("Reference generation completed successfully.")
        
    except FatalError as e:
        logger.critical(f"FR-008 Violation: {e}")
        raise
    except FileNotFoundError as e:
        logger.critical(f"Required file missing: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error in reference generation: {e}")
        raise

if __name__ == "__main__":
    main()
