"""
write_metadata.py
Implements metadata parsing, validation, and instrumentation fallback merging.

This script:
1. Loads the merged perovskite dataset from data/raw/perovskites_merged.csv.
2. Parses source metadata to extract TGA instrument details.
3. Uses the instrument registry to determine precision sources.
4. Merges instrumentation fallback information into the metadata.
5. Writes the final metadata to data/raw/metadata.json.

Output Schema:
[
  {
    "formula": str,
    "instrument_model": str,
    "manufacturer": str,
    "precision_source": "source" | "registry" | "default",
    "precision_from_registry": bool,
    "precision_value": float
  }
]
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.instrument_registry import get_precision, reload_registry
from code.utils.uncertainty_parser import parse_temperature_precision

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
MERGED_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "perovskites_merged.csv"
METADATA_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "metadata.json"
FALLBACK_LOG_PATH = PROJECT_ROOT / "data" / "raw" / "instrumentation_fallbacks.log"

def load_merged_perovskites() -> pd.DataFrame:
    """Load the merged perovskite dataset."""
    if not MERGED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Merged data file not found: {MERGED_DATA_PATH}. "
            "Run T012e (merge logic) first."
        )
    df = pd.read_csv(MERGED_DATA_PATH)
    logger.info(f"Loaded {len(df)} records from {MERGED_DATA_PATH}")
    return df

def parse_source_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract instrumentation metadata from source data.
    
    Checks for 'instrument_model', 'manufacturer', and 'temperature_precision'
    in the dataframe columns or metadata fields.
    """
    records = []
    
    # Ensure we have the necessary columns, defaulting if missing
    if 'instrument_model' not in df.columns:
        logger.warning("Column 'instrument_model' not found in merged data. Defaulting to 'Unknown'.")
    if 'manufacturer' not in df.columns:
        logger.warning("Column 'manufacturer' not found in merged data. Defaulting to 'Unknown'.")
        
    for idx, row in df.iterrows():
        record = {
            "formula": row.get('formula', 'Unknown'),
            "instrument_model": str(row.get('instrument_model', 'Unknown')).strip() or 'Unknown',
            "manufacturer": str(row.get('manufacturer', 'Unknown')).strip() or 'Unknown',
            "precision_source": "default",
            "precision_from_registry": False,
            "precision_value": 10.0  # Default fallback
        }
        
        # Try to parse precision if available
        precision_raw = row.get('temperature_precision')
        if precision_raw is not None and precision_raw != '':
            parsed_prec = parse_temperature_precision(precision_raw)
            if parsed_prec is not None:
                record["precision_value"] = parsed_prec
        
        records.append(record)
        
    return records

def process_metadata_entries(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process each metadata entry to determine precision provenance.
    
    Updates:
    - precision_source: 'source' if from data, 'registry' if from registry lookup, 'default' if fallback
    - precision_from_registry: True if the value came from instrument_registry.csv
    """
    # Reload registry to ensure fresh data
    reload_registry()
    
    fallback_entries = []
    
    for record in records:
        model = record["instrument_model"]
        
        if model == 'Unknown':
            # Missing instrumentation data
            record["precision_source"] = "default"
            record["precision_from_registry"] = False
            fallback_entries.append({
                "formula": record["formula"],
                "source": "Unknown Model",
                "default_precision_used": True,
                "message": "Instrument model missing"
            })
            continue
        
        # Attempt to get precision from registry
        precision_val = get_precision(model)
        
        if precision_val is not None and precision_val != 10.0:
            # Found in registry with specific value
            record["precision_source"] = "registry"
            record["precision_from_registry"] = True
            record["precision_value"] = precision_val
        elif precision_val == 10.0 and model != 'Unknown':
            # Model exists but no specific precision in registry, or registry default used
            # If the registry returns the default (10.0) for a known model, 
            # we mark it as registry-derived but with default precision
            record["precision_source"] = "registry"
            record["precision_from_registry"] = True
            record["precision_value"] = 10.0
        else:
            # Not in registry or unknown
            record["precision_source"] = "default"
            record["precision_from_registry"] = False
            record["precision_value"] = 10.0
            fallback_entries.append({
                "formula": record["formula"],
                "source": model,
                "default_precision_used": True,
                "message": f"Instrument '{model}' not in registry"
            })
            
    # Log fallbacks
    if fallback_entries:
        logger.info(f"Found {len(fallback_entries)} entries with missing or registry-fallback instrumentation.")
        with open(FALLBACK_LOG_PATH, 'w') as f:
            for entry in fallback_entries:
                f.write(json.dumps(entry) + '\n')
        logger.info(f"Wrote fallback log to {FALLBACK_LOG_PATH}")
        
    return records

def validate_metadata_structure(records: List[Dict[str, Any]]) -> bool:
    """Validate that all records have required fields."""
    required_fields = ["formula", "instrument_model", "manufacturer", "precision_source", "precision_from_registry", "precision_value"]
    
    for i, record in enumerate(records):
        for field in required_fields:
            if field not in record:
                logger.error(f"Record {i} missing required field: {field}")
                return False
    return True

def main():
    """Main entry point for metadata generation."""
    logger.info("Starting metadata generation and instrumentation fallback merge...")
    
    try:
        # 1. Load data
        df = load_merged_perovskites()
        
        # 2. Parse source metadata
        records = parse_source_metadata(df)
        
        # 3. Process entries (merge fallback info)
        processed_records = process_metadata_entries(records)
        
        # 4. Validate structure
        if not validate_metadata_structure(processed_records):
            raise ValueError("Metadata validation failed.")
        
        # 5. Write output
        METADATA_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(METADATA_OUTPUT_PATH, 'w') as f:
            json.dump(processed_records, f, indent=2)
        
        logger.info(f"Successfully wrote metadata to {METADATA_OUTPUT_PATH}")
        logger.info(f"Total records processed: {len(processed_records)}")
        
    except Exception as e:
        logger.error(f"Error during metadata generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()