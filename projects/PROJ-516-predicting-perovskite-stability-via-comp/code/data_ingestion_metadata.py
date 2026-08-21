import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)

# Regex patterns for extracting precision ranges
# Matches formats like "±5°C", "± 5 °C", "±10°C", "± 10 °C", "±5-10°C"
PRECISION_PATTERN = re.compile(
    r'[±+]\s*(\d+(?:\.\d+)?)\s*(?:°C|C|°)\s*(?:-\s*(\d+(?:\.\d+)?)\s*(?:°C|C|°))?',
    re.IGNORECASE
)

# Common TGA instrument model keywords to look for in metadata strings
INSTRUMENT_KEYWORDS = [
    'TA Instruments', 'Q500', 'Q50', 'Q600', 'Discovery',
    'Mettler Toledo', 'TGA/DSC', 'SDT', 'TGA550',
    'PerkinElmer', 'TGA 4000', 'Pyris',
    'NETZSCH', 'STA 449', 'TGA 2050',
    'Hitachi', 'TGA 7000'
]

def parse_uncertainty(uncertainty_str: str) -> Optional[Dict[str, Any]]:
    """
    Parse an uncertainty string (e.g., '±5°C', '±10°C', '±5-10°C') into a structured object.
    
    Args:
        uncertainty_str: Raw uncertainty string from metadata
        
    Returns:
        Dictionary with 'value' (float or range) and 'unit' (str), or None if not parseable
    """
    if not uncertainty_str or not isinstance(uncertainty_str, str):
        return None
        
    match = PRECISION_PATTERN.search(uncertainty_str)
    if not match:
        return None
        
    low_val = float(match.group(1))
    high_val = match.group(2)
    
    result = {
        'unit': 'Celsius',
        'type': 'range' if high_val else 'single'
    }
    
    if high_val:
        result['value'] = [low_val, float(high_val)]
    else:
        result['value'] = low_val
        
    return result

def extract_instrument_model(metadata_text: str) -> Optional[str]:
    """
    Extract the TGA instrument model from metadata text.
    
    Args:
        metadata_text: Raw metadata string containing instrument info
        
    Returns:
        Extracted instrument model string or None if not found
    """
    if not metadata_text or not isinstance(metadata_text, str):
        return None
        
    for keyword in INSTRUMENT_KEYWORDS:
        if keyword.lower() in metadata_text.lower():
            # Extract the specific model number if present
            # Look for patterns like "TA Instruments Q500" or "Mettler Toledo TGA/DSC"
            pattern = re.compile(
                rf'({re.escape(keyword)}[^,.\n\r]{{0,50}})',
                re.IGNORECASE
            )
            match = pattern.search(metadata_text)
            if match:
                return match.group(1).strip()
                
    # Fallback: return the full text if a keyword is found but no specific model
    for keyword in INSTRUMENT_KEYWORDS:
        if keyword.lower() in metadata_text.lower():
            return keyword
            
    return None

def process_metadata_entries(raw_data_path: str, output_path: str) -> None:
    """
    Process raw perovskite data to extract TGA instrument models and precision ranges.
    
    This function:
    1. Loads the raw CSV data
    2. Extracts instrument model and precision from metadata columns
    3. Writes structured metadata to JSON
    
    Args:
        raw_data_path: Path to the raw perovskite CSV file
        output_path: Path to write the metadata JSON file
    """
    raw_path = Path(raw_data_path)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
        
    logger.info(f"Loading raw data from {raw_data_path}")
    df = pd.read_csv(raw_path)
    
    # Identify potential metadata columns
    metadata_candidates = [col for col in df.columns if 'meta' in col.lower() or 'source' in col.lower() or 'instrument' in col.lower()]
    
    # If no specific metadata columns found, assume the 'notes' or 'description' column exists
    if not metadata_candidates:
        if 'notes' in df.columns:
            metadata_candidates = ['notes']
        elif 'description' in df.columns:
            metadata_candidates = ['description']
        else:
            # Fallback: use the first text-like column that isn't a standard data column
            standard_cols = {'formula', 'T_d', 'T_d_uncertainty', 'A_site', 'B_site', 'X_site'}
            metadata_candidates = [col for col in df.columns if col not in standard_cols and df[col].dtype == 'object']
            if not metadata_candidates:
                logger.warning("No metadata columns found. Creating empty metadata file.")
                metadata_entries = []
            else:
                metadata_candidates = [metadata_candidates[0]]
    
    logger.info(f"Scanning metadata columns: {metadata_candidates}")
    
    metadata_entries = []
    
    for idx, row in df.iterrows():
        entry = {
            'index': idx,
            'formula': row.get('formula', 'Unknown'),
            'instrument_model': None,
            'uncertainty': None,
            'raw_metadata_text': None
        }
        
        # Search across metadata candidate columns
        for col in metadata_candidates:
            cell_value = str(row.get(col, ''))
            if not cell_value or cell_value == 'nan':
                continue
                
            # Try to extract instrument model
            if not entry['instrument_model']:
                entry['instrument_model'] = extract_instrument_model(cell_value)
                
            # Try to extract uncertainty
            if not entry['uncertainty']:
                parsed_unc = parse_uncertainty(cell_value)
                if parsed_unc:
                    entry['uncertainty'] = parsed_unc
                    
            # Store raw text if we found something
            if entry['instrument_model'] or entry['uncertainty']:
                entry['raw_metadata_text'] = cell_value
                break
                
        # Only include entries where we found at least one piece of metadata
        if entry['instrument_model'] or entry['uncertainty']:
            metadata_entries.append(entry)
    
    logger.info(f"Processed {len(metadata_entries)} entries with extracted metadata")
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'processed_at': pd.Timestamp.now().isoformat(),
            'source_file': str(raw_path),
            'entries': metadata_entries
        }, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Wrote metadata to {output_path}")

def main():
    """Main entry point for metadata extraction."""
    # Default paths based on project structure
    raw_data_path = "data/raw/nrel_perovskites.csv"
    output_path = "data/raw/metadata.json"
    
    # Allow command-line overrides
    import sys
    if len(sys.argv) > 1:
        raw_data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        process_metadata_entries(raw_data_path, output_path)
        print(f"Metadata extraction complete. Output written to {output_path}")
    except Exception as e:
        logger.error(f"Failed to process metadata: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
