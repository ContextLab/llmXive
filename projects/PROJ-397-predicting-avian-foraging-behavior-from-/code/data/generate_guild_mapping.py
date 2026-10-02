"""
T008b: Generate processed guild mapping from raw source.

Reads the raw guild source CSV (produced by T008a) and writes a processed
guild mapping CSV with an added 'extraction_date' column for provenance.

Input:  data/raw/guild_source.csv (or data/raw/guild_mapping_manual.csv if T008a used that name)
Output: data/processed/guild_mapping.csv
"""
import os
import sys
import csv
import logging
import json
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_raw_data_dir, get_processed_dir, get_metadata_file
from utils.provenance import record_source_info, load_metadata_config, save_metadata_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# T008a description mentions 'data/raw/guild_mapping_manual.csv' but the task line for T008b
# says 'read data/raw/guild_source.csv'. We check both, preferring the explicit T008b requirement.
# However, looking at T008a description: "write data/raw/guild_mapping_manual.csv".
# And T008b description: "read data/raw/guild_source.csv".
# We will implement logic to find the file produced by T008a.
# The most robust approach is to check for the file mentioned in T008a's output.
RAW_SOURCE_FILES = [
    "guild_mapping_manual.csv", # As per T008a description
    "guild_source.csv"          # As per T008b description
]

OUTPUT_FILE = "guild_mapping.csv"

def get_input_file_path():
    raw_dir = get_raw_data_dir()
    for fname in RAW_SOURCE_FILES:
        fpath = raw_dir / fname
        if fpath.exists():
            logger.info(f"Found input file: {fpath}")
            return fpath
    raise FileNotFoundError(
        f"Could not find raw guild source file. Looked for: {RAW_SOURCE_FILES} "
        f"in {raw_dir}. Ensure T008a has completed successfully."
    )

def get_output_file_path():
    return get_processed_dir() / OUTPUT_FILE

def load_guild_source(input_path: Path) -> list:
    """Load the raw guild source CSV."""
    rows = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if not rows:
        raise ValueError("Input guild source file is empty or has no data rows.")
    return rows

def validate_schema(rows: list, input_path: Path) -> None:
    """Validate that the input has required columns."""
    required_cols = {'species_id', 'foraging_guild', 'source_citation'}
    if not rows:
        raise ValueError("No rows to validate.")
    actual_cols = set(rows[0].keys())
    missing = required_cols - actual_cols
    if missing:
        raise ValueError(f"Input file {input_path} is missing required columns: {missing}")

def save_mapping(rows: list, output_path: Path, extraction_date: str) -> None:
    """Write the processed mapping with extraction date."""
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['species_id', 'foraging_guild', 'source_citation', 'extraction_date']
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            row['extraction_date'] = extraction_date
            writer.writerow(row)
    logger.info(f"Wrote {len(rows)} rows to {output_path}")

def record_provenance_in_metadata(input_path: Path, output_path: Path, extraction_date: str):
    """Update the project metadata.yaml with provenance for this step."""
    metadata_path = get_metadata_file()
    config = load_metadata_config(metadata_path)

    step_name = "T008b_generate_guild_mapping"
    record = {
        "step": step_name,
        "input_file": str(input_path.name),
        "output_file": str(output_path.name),
        "extraction_date": extraction_date,
        "timestamp": datetime.now().isoformat(),
        "description": "Processed raw guild source into final mapping with extraction date."
    }

    if "steps" not in config:
        config["steps"] = []
    config["steps"].append(record)

    save_metadata_config(metadata_path, config)
    logger.info(f"Recorded provenance in {metadata_path}")

def main():
    logger.info("Starting T008b: Generate Guild Mapping")
    
    # 1. Locate input
    input_path = get_input_file_path()
    
    # 2. Load and validate
    rows = load_guild_source(input_path)
    validate_schema(rows, input_path)
    logger.info(f"Loaded {len(rows)} records from {input_path.name}")

    # 3. Determine output path
    output_path = get_output_file_path()

    # 4. Generate extraction date (ISO format)
    extraction_date = datetime.now().strftime("%Y-%m-%d")

    # 5. Save processed mapping
    save_mapping(rows, output_path, extraction_date)

    # 6. Record provenance
    record_provenance_in_metadata(input_path, output_path, extraction_date)

    logger.info("T008b completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
