import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from utils.instrument_registry import get_precision
from utils.uncertainty_parser import parse_temperature_precision

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_uncertainty(record: Dict[str, Any]) -> float:
    """
    Parse temperature precision from a record.
    
    Args:
        record: Data record
        
    Returns:
        Precision value (default 10.0)
    """
    precision = parse_temperature_precision(record)
    return precision if precision is not None else 10.0

def extract_instrument_model(record: Dict[str, Any]) -> str:
    """
    Extract instrument model from a record.
    
    Args:
        record: Data record
        
    Returns:
        Instrument model string or 'Unknown'
    """
    model = record.get('instrument_model') or record.get('instrument')
    if not model:
        return 'Unknown'
    return str(model)

def process_metadata_entries(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process dataframe entries to extract metadata.
    
    Args:
        df: DataFrame with perovskite data
        
    Returns:
        List of metadata entries
    """
    metadata_entries = []
    
    for _, row in df.iterrows():
        formula = row.get('formula', 'Unknown')
        instrument_model = extract_instrument_model(row)
        manufacturer = row.get('manufacturer', 'Unknown')
        
        # Get precision from registry or default
        precision = get_precision(instrument_model)
        
        # Determine precision source
        precision_source = "registry" if instrument_model != 'Unknown' else "default"
        
        entry = {
            "formula": formula,
            "instrument_model": instrument_model,
            "manufacturer": manufacturer,
            "precision_source": precision_source,
            "temperature_precision": precision
        }
        metadata_entries.append(entry)
        
        # Log fallbacks
        if instrument_model == 'Unknown' or precision_source == "default":
            logger.warning(f"Missing instrumentation for {formula}, using default precision {precision}°C")
    
    return metadata_entries

def main():
    """Main entry point for metadata processing."""
    logger.info("Starting T013: Metadata Extraction")
    
    merged_path = Path("data/raw/perovskites_merged.csv")
    if not merged_path.exists():
        logger.error(f"Merged dataset not found: {merged_path}")
        return
    
    df = pd.read_csv(merged_path)
    metadata = process_metadata_entries(df)
    
    output_path = Path("data/raw/metadata.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved metadata to {output_path}")
    logger.info("T013 completed successfully.")

if __name__ == "__main__":
    main()