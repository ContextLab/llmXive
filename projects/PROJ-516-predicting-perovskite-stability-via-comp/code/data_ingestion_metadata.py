"""
T013: Extract metadata (instrument, precision) and write to data/raw/metadata.json.
"""
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from utils.instrument_registry import get_precision
from utils.uncertainty_parser import parse_temperature_precision
from utils.uncertainty_propagator import calculate_combined_uncertainty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MERGED_PATH = Path(__file__).parent.parent / "data" / "raw" / "perovskites_merged.csv"
METADATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "metadata.json"

def load_merged_perovskites() -> pd.DataFrame:
    if not MERGED_PATH.exists():
        raise FileNotFoundError(f"Merged file not found: {MERGED_PATH}")
    return pd.read_csv(MERGED_PATH)

def parse_source_metadata(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts instrument and precision from row.
    """
    formula = row.get("formula", "Unknown")
    instrument_model = row.get("instrument_model", "Unknown")
    manufacturer = row.get("manufacturer", "Unknown")
    
    # Get precision from registry or default
    precision = get_precision(instrument_model)
    
    # Parse any reported experimental error if available
    exp_error = row.get("experimental_error", 0.0)
    if exp_error is None:
        exp_error = 0.0
    
    # Calculate sigma
    sigma = calculate_combined_uncertainty(precision, exp_error)
    
    return {
        "formula": formula,
        "instrument_model": instrument_model,
        "manufacturer": manufacturer,
        "temperature_precision": precision,
        "experimental_error": exp_error,
        "T_d_uncertainty": sigma,
        "source_instrumentation": instrument_model != "Unknown"
    }

def process_metadata_entries(df: pd.DataFrame) -> List[Dict[str, Any]]:
    metadata = []
    for _, row in df.iterrows():
        meta = parse_source_metadata(row.to_dict())
        metadata.append(meta)
    return metadata

def generate_uncertainty_flags(metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Placeholder for flagging logic
    return metadata

def validate_metadata_structure(metadata: List[Dict[str, Any]]) -> bool:
    required_keys = ["formula", "instrument_model", "manufacturer", "T_d_uncertainty"]
    for item in metadata:
        if not all(k in item for k in required_keys):
            return False
    return True

def main():
    logger.info("Starting T013: Metadata Extraction")
    try:
        df = load_merged_perovskites()
        metadata = process_metadata_entries(df)
        
        if not validate_metadata_structure(metadata):
            logger.error("Metadata structure validation failed.")
            return

        with open(METADATA_PATH, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Saved metadata to {METADATA_PATH}")
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
