"""
write_metadata.py

Implements task T013b: Write parsed instrumentation metadata to
data/raw/metadata.json adhering to contracts/metadata.schema.yaml.

This script loads the raw perovskite data, extracts instrumentation
metadata (model, uncertainty) using the logic from data_ingestion_metadata,
validates the structure against the contract, and writes the final JSON.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Import from sibling modules as per API surface
from data_ingestion_metadata import parse_uncertainty, extract_instrument_model

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "nrel_perovskites.csv"
METADATA_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "metadata.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "metadata.schema.yaml"

def load_raw_data() -> pd.DataFrame:
    """Load the raw perovskite data CSV."""
    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(f"Raw data file not found: {RAW_DATA_PATH}")
    logger.info(f"Loading raw data from {RAW_DATA_PATH}")
    df = pd.read_csv(RAW_DATA_PATH)
    
    # Ensure required columns exist
    required_cols = ["formula", "T_d", "metadata_text"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw data: {missing_cols}")
    
    return df

def validate_metadata_structure(entries: List[Dict[str, Any]]) -> bool:
    """
    Validate the structure of the metadata entries against the contract.
    This implements a basic structural check matching the schema requirements.
    """
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            logger.error(f"Entry {i} is not a dictionary")
            return False
        
        required_fields = ["index", "formula", "instrument_model", "uncertainty", "raw_metadata_text"]
        for field in required_fields:
            if field not in entry:
                logger.error(f"Entry {i} missing required field: {field}")
                return False
        
        # Validate uncertainty structure
        unc = entry["uncertainty"]
        if not isinstance(unc, dict):
            logger.error(f"Entry {i} uncertainty is not a dictionary")
            return False
        
        unc_fields = ["unit", "type", "value"]
        for field in unc_fields:
            if field not in unc:
                logger.error(f"Entry {i} uncertainty missing field: {field}")
                return False
        
        # Validate types
        if not isinstance(entry["index"], int):
            logger.error(f"Entry {i} index is not an integer")
            return False
        
        if unc["type"] not in ["single", "range"]:
            logger.error(f"Entry {i} uncertainty type invalid: {unc['type']}")
            return False
        
        if unc["unit"] != "Celsius":
            logger.error(f"Entry {i} uncertainty unit invalid: {unc['unit']}")
            return False
        
        if unc["type"] == "single" and not isinstance(unc["value"], (int, float)):
            logger.error(f"Entry {i} uncertainty value for single type is not numeric")
            return False
        
        if unc["type"] == "range" and not (isinstance(unc["value"], list) and len(unc["value"]) == 2):
            logger.error(f"Entry {i} uncertainty value for range type is not a list of 2")
            return False

    return True

def process_metadata_entries(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process the dataframe to extract and structure instrumentation metadata.
    """
    entries = []
    
    for idx, row in df.iterrows():
        formula = row["formula"]
        raw_text = str(row["metadata_text"])
        
        # Extract instrument model
        instrument_model = extract_instrument_model(raw_text)
        
        # Parse uncertainty
        uncertainty = parse_uncertainty(raw_text)
        
        # Fallback to default if parsing fails (but log it)
        if uncertainty is None:
            logger.warning(f"Could not parse uncertainty for {formula}, using default ±10°C")
            uncertainty = {
                "unit": "Celsius",
                "type": "single",
                "value": 10.0
            }
        
        entry = {
            "index": idx,
            "formula": formula,
            "instrument_model": instrument_model or "Unknown",
            "uncertainty": uncertainty,
            "raw_metadata_text": raw_text
        }
        entries.append(entry)
    
    return entries

def main():
    """Main entry point for T013b."""
    logger.info("Starting T013b: Write parsed instrumentation metadata")
    
    try:
        # Load raw data
        df = load_raw_data()
        logger.info(f"Loaded {len(df)} rows")
        
        # Process entries
        entries = process_metadata_entries(df)
        logger.info(f"Processed {len(entries)} metadata entries")
        
        # Validate structure
        if not validate_metadata_structure(entries):
            raise ValueError("Metadata structure validation failed")
        logger.info("Metadata structure validation passed")
        
        # Construct output object
        output = {
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "source_file": str(RAW_DATA_PATH.relative_to(PROJECT_ROOT)),
            "entries": entries
        }
        
        # Ensure output directory exists
        METADATA_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to JSON
        with open(METADATA_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Successfully wrote metadata to {METADATA_OUTPUT_PATH}")
        
        # Verify file exists and is not empty
        if not METADATA_OUTPUT_PATH.exists() or METADATA_OUTPUT_PATH.stat().st_size == 0:
            raise RuntimeError("Output file was not created or is empty")
        
        logger.info("T013b completed successfully")
        
    except Exception as e:
        logger.error(f"T013b failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
