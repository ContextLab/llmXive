import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_uncertainty(metadata_str: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Parse TGA precision/uncertainty from source metadata strings.
    
    Expected formats:
    - "±5°C", "±10°C", "± 5 °C", "uncertainty: 5", "precision 10 degrees"
    
    Returns:
        Dict with 'value' (float) and 'unit' (str, default 'C') or None if not found.
    """
    if not metadata_str or not isinstance(metadata_str, str):
        return None
    
    # Normalize string
    text = metadata_str.lower()
    
    # Pattern for ±X°C or ± X °C
    pattern_celsius = r'[±\+/-]\s*(\d+(?:\.\d+)?)\s*(?:°|deg)?\s*c'
    match = re.search(pattern_celsius, text)
    if match:
        return {
            'value': float(match.group(1)),
            'unit': 'C',
            'source_text': metadata_str
        }
    
    # Pattern for "uncertainty: X" or "precision X"
    pattern_generic = r'(?:uncertainty|precision|error|tolerance)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:°|deg)?\s*c?'
    match = re.search(pattern_generic, text)
    if match:
        return {
            'value': float(match.group(1)),
            'unit': 'C',
            'source_text': metadata_str
        }
    
    return None

def extract_instrument_model(metadata_str: Optional[str]) -> Optional[str]:
    """
    Extract TGA instrument model from source metadata.
    
    Common patterns:
    - "TGA Q500", "SDT Q600", "TGA/DSC 1", "Mettler Toledo TGA", "TA Instruments"
    
    Returns:
        Extracted model string or None if not found.
    """
    if not metadata_str or not isinstance(metadata_str, str):
        return None
    
    text = metadata_str
    
    # Common TGA instrument patterns
    patterns = [
        r'(TGA\s+Q\d{3})',           # TA Instruments Q-series
        r'(SDT\s+Q\d{3})',           # TA Instruments SDT series
        r'(TGA/\s*DSC\s+\d)',        # Mettler Toledo
        r'(Mettler\s+Toledo\s+\w+)', # Mettler Toledo models
        r'(TA\s+Instruments\s+\w+)', # TA Instruments models
        r'(Netzsch\s+\w+)',          # Netzsch models
        r'(PerkinElmer\s+\w+)',      # PerkinElmer models
        r'(TGA\s+\d{4})',            # Generic 4-digit model
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Fallback: look for any mention of TGA followed by text
    fallback = re.search(r'(TGA[^,;\n]{0,30})', text, re.IGNORECASE)
    if fallback:
        cleaned = fallback.group(1).strip()
        if len(cleaned) > 3 and len(cleaned) < 35:  # Reasonable length check
            return cleaned
    
    return None

def process_metadata_entries(df: pd.DataFrame, metadata_column: str = 'source_metadata') -> List[Dict[str, Any]]:
    """
    Process a DataFrame of perovskite entries to extract structured metadata.
    
    Args:
        df: DataFrame with perovskite entries
        metadata_column: Name of column containing raw metadata strings
        
    Returns:
        List of dictionaries with parsed metadata for each entry
    """
    if metadata_column not in df.columns:
        logger.warning(f"Metadata column '{metadata_column}' not found in DataFrame")
        return []
    
    processed = []
    
    for idx, row in df.iterrows():
        entry_id = row.get('id', idx)
        raw_metadata = row.get(metadata_column, '')
        
        parsed_entry = {
            'entry_id': entry_id,
            'raw_metadata': raw_metadata,
            'instrument_model': extract_instrument_model(raw_metadata),
            'uncertainty': parse_uncertainty(raw_metadata)
        }
        
        # Validate uncertainty value is reasonable (0-100 range)
        if parsed_entry['uncertainty']:
            if not (0 < parsed_entry['uncertainty']['value'] <= 100):
                logger.warning(f"Unreasonable uncertainty value {parsed_entry['uncertainty']['value']} for entry {entry_id}")
                parsed_entry['uncertainty'] = None
        
        processed.append(parsed_entry)
    
    return processed

def main():
    """
    Main function to process metadata from raw data and write to JSON.
    
    Reads: data/raw/nrel_perovskites.csv
    Writes: data/raw/metadata.json
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'data' / 'raw' / 'nrel_perovskites.csv'
    output_path = project_root / 'data' / 'raw' / 'metadata.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Processing {len(df)} entries for metadata extraction")
    metadata_entries = process_metadata_entries(df, metadata_column='source_metadata')
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata_entries, f, indent=2, default=str)
    
    logger.info(f"Wrote metadata to {output_path}")
    
    # Summary statistics
    entries_with_model = sum(1 for e in metadata_entries if e['instrument_model'])
    entries_with_uncertainty = sum(1 for e in metadata_entries if e['uncertainty'])
    
    logger.info(f"Summary: {entries_with_model}/{len(metadata_entries)} entries have instrument model")
    logger.info(f"Summary: {entries_with_uncertainty}/{len(metadata_entries)} entries have parsed uncertainty")
    
    return metadata_entries

if __name__ == '__main__':
    main()
