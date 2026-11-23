import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from utils.instrument_registry import get_precision, get_registry_details
from utils.uncertainty_parser import parse_temperature_precision

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_merged_perovskites(file_path: Path) -> pd.DataFrame:
    """Load the merged perovskites dataset."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    logger.info(f"Loading data from {file_path}")
    return pd.read_csv(file_path)

def parse_source_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract raw metadata fields from the dataframe.
    Looks for columns like 'instrument_model', 'manufacturer', 'temperature_precision', 'source'.
    """
    metadata_list = []
    for idx, row in df.iterrows():
        entry = {
            'formula': row.get('formula', 'Unknown'),
            'source': row.get('source', 'Unknown'),
            'source_T_d': 'T_d', # Map to the canonical column name
            'raw_instrument_model': row.get('instrument_model', None),
            'raw_manufacturer': row.get('manufacturer', None),
            'raw_precision': row.get('temperature_precision', None),
        }
        metadata_list.append(entry)
    return metadata_list

def process_metadata_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw metadata entries to determine final instrument, manufacturer, and precision source.
    Logic:
    1. If instrument_model is present, use it. Else default to 'Unknown'.
    2. If manufacturer is present, use it. Else default to 'Unknown'.
    3. Check registry for precision. If found, source='registry'. Else source='default'.
    4. Log warnings for missing data.
    """
    processed = []
    for entry in entries:
        # Determine Instrument Model
        instrument_model = entry['raw_instrument_model']
        if not instrument_model or str(instrument_model).strip() == '' or str(instrument_model).lower() == 'nan':
            instrument_model = 'Unknown'
            logger.warning(f"Missing instrument_model for {entry['formula']}, defaulting to 'Unknown'")

        # Determine Manufacturer
        manufacturer = entry['raw_manufacturer']
        if not manufacturer or str(manufacturer).strip() == '' or str(manufacturer).lower() == 'nan':
            manufacturer = 'Unknown'
            logger.warning(f"Missing manufacturer for {entry['formula']}, defaulting to 'Unknown'")

        # Determine Precision Source and Value
        precision_source = 'default'
        precision_value = 10.0 # Default fallback per spec

        # Try to get precision from registry if we have an instrument model
        if instrument_model != 'Unknown':
            registry_precision = get_precision(instrument_model)
            if registry_precision is not None:
                precision_value = registry_precision
                precision_source = 'registry'
            else:
                # Not in registry, but we have a model name -> still default precision but maybe log specific
                logger.warning(f"Instrument {instrument_model} not found in registry for {entry['formula']}, using default ±10°C")
        else:
            logger.warning(f"No instrument model for {entry['formula']}, using default ±10°C")

        processed_entry = {
            'formula': entry['formula'],
            'instrument_model': instrument_model,
            'manufacturer': manufacturer,
            'precision_source': precision_source,
            'source_T_d': entry['source_T_d'],
            'precision_value': precision_value,
            'source': entry['source']
        }
        processed.append(processed_entry)

    return processed

def validate_metadata_structure(metadata_list: List[Dict[str, Any]]) -> bool:
    """
    Validate that the metadata list conforms to the expected schema.
    Required keys: formula, instrument_model, manufacturer, precision_source, source_T_d
    """
    required_keys = {'formula', 'instrument_model', 'manufacturer', 'precision_source', 'source_T_d'}
    valid = True
    for i, entry in enumerate(metadata_list):
        if not isinstance(entry, dict):
            logger.error(f"Entry {i} is not a dictionary.")
            valid = False
            continue
        
        missing = required_keys - set(entry.keys())
        if missing:
            logger.error(f"Entry {i} missing required keys: {missing}")
            valid = False
        
        # Validate precision_source values
        if entry.get('precision_source') not in ['source', 'registry', 'default']:
            logger.warning(f"Entry {i} has unexpected precision_source: {entry.get('precision_source')}")
    
    if valid:
        logger.info("Metadata structure validation passed.")
    else:
        logger.error("Metadata structure validation failed.")
    return valid

def main():
    """Main entry point for testing the module."""
    logger.info("Running data_ingestion_metadata module...")
    # This is primarily a library module; main execution usually handled by write_metadata.py
    pass

if __name__ == '__main__':
    main()
