import json
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
import logging

# Ensure we can import from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from validation import run_schema_validation, save_validation_report

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for generating the dataset schema and running validation.
    
    This script:
    1. Generates `contracts/dataset.schema.yaml` based on data-model.md and
       the structure of participant_logs.json (if available).
    2. Runs schema validation on `data/raw/participant_logs.json` against
       the generated schema.
    3. Saves the validation report to `data/processed/validation_report.json`.
    """
    project_root = Path(__file__).parent.parent
    contracts_dir = project_root / "contracts"
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"

    # Ensure directories exist
    contracts_dir.mkdir(parents=True, exist_ok=True)
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)

    schema_path = contracts_dir / "dataset.schema.yaml"
    raw_data_path = data_raw_dir / "participant_logs.json"
    validation_report_path = data_processed_dir / "validation_report.json"

    logger.info(f"Generating schema at: {schema_path}")
    
    # Generate the schema
    # This function is expected to exist in validation.py as per the API surface
    # It should create the YAML file based on data-model.md and sample data structure
    run_schema_validation(
        schema_output_path=str(schema_path),
        raw_data_path=str(raw_data_path),
        report_output_path=str(validation_report_path)
    )

    if schema_path.exists():
        logger.info(f"Schema generated successfully at {schema_path}")
    else:
        logger.error("Schema generation failed: file not created.")
        sys.exit(1)

    if validation_report_path.exists():
        logger.info(f"Validation report generated at {validation_report_path}")
    else:
        logger.warning("Validation report not generated (raw data might be missing).")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
