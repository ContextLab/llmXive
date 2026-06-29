"""
Element validation module for alloy composition data.

Validates elemental symbols in composition CSV files against pymatgen's
periodic table. Outputs valid and invalid element records to separate files.

FR-002 Compliance: Validates all elemental symbols before any descriptor
computation to ensure data quality.
"""
import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from pymatgen.core.periodic_table import Element

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def is_valid_element(symbol: str) -> bool:
    """
    Check if a string is a valid elemental symbol.
    
    Args:
        symbol: Element symbol string (e.g., 'Cu', 'Zr')
        
    Returns:
        True if the symbol is valid, False otherwise
    """
    try:
        Element(symbol)
        return True
    except ValueError:
        return False

def validate_composition_elements(composition_str: str) -> tuple[list[str], list[str]]:
    """
    Extract and validate elemental symbols from a composition string.
    
    Composition strings are expected in formats like:
    - 'Cu50Zr50' (element+count)
    - 'Cu-Zr' (dash-separated)
    - 'Cu,Zr' (comma-separated)
    
    Args:
        composition_str: The composition string from the CSV
        
    Returns:
        Tuple of (valid_symbols, invalid_symbols)
    """
    # Clean and normalize the composition string
    clean_str = composition_str.strip()
    
    # Replace common separators with spaces for splitting
    # Handle formats: Cu50Zr50, Cu-Zr, Cu,Zr, Cu Zr
    for sep in ['-', ',', ' ']:
        clean_str = clean_str.replace(sep, ' ')
    
    # Extract element symbols (letters) and counts (digits)
    valid_symbols = []
    invalid_symbols = []
    current_symbol = ''
    
    for char in clean_str:
        if char.isalpha():
            current_symbol += char
        elif char.isdigit() or char.isspace():
            if current_symbol:
                # Check if current_symbol is a valid element
                if is_valid_element(current_symbol):
                    valid_symbols.append(current_symbol)
                else:
                    invalid_symbols.append(current_symbol)
                current_symbol = ''
    
    # Handle remaining symbol at end of string
    if current_symbol:
        if is_valid_element(current_symbol):
            valid_symbols.append(current_symbol)
        else:
            invalid_symbols.append(current_symbol)
    
    return valid_symbols, invalid_symbols

def main():
    """Main entry point for element validation script."""
    parser = argparse.ArgumentParser(
        description='Validate elemental symbols in alloy composition CSV'
    )
    parser.add_argument(
        '--input', '-i',
        default='data/samples/synthetic_alloys.csv',
        help='Input CSV file with alloy compositions'
    )
    parser.add_argument(
        '--output-valid',
        default='data/derived/valid_elements.csv',
        help='Output path for rows with valid elements'
    )
    parser.add_argument(
        '--output-invalid',
        default='data/derived/invalid_elements.csv',
        help='Output path for rows with invalid elements'
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    Path(args.output_valid).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_invalid).parent.mkdir(parents=True, exist_ok=True)
    
    # Read input CSV
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    logger.info(f"Reading input file: {args.input}")
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows from {args.input}")
    
    # Find composition column
    composition_col = None
    for col in ['composition', 'elements', 'formula', 'alloy_composition']:
        if col in df.columns:
            composition_col = col
            break
    
    if composition_col is None:
        logger.error("Could not find composition column. Available columns: " + 
                    ', '.join(df.columns))
        return 1
    
    logger.info(f"Using composition column: {composition_col}")
    
    # Validate each row
    valid_rows = []
    invalid_rows = []
    
    for idx, row in df.iterrows():
        composition_str = str(row[composition_col])
        valid_symbols, invalid_symbols = validate_composition_elements(composition_str)
        
        row_dict = row.to_dict()
        row_dict['valid_elements'] = ','.join(valid_symbols) if valid_symbols else ''
        row_dict['invalid_elements'] = ','.join(invalid_symbols) if invalid_symbols else ''
        row_dict['validation_status'] = 'valid' if invalid_symbols else 'invalid'
        
        if invalid_symbols:
            invalid_rows.append(row_dict)
        else:
            valid_rows.append(row_dict)
    
    # Write output files
    valid_df = pd.DataFrame(valid_rows)
    invalid_df = pd.DataFrame(invalid_rows)
    
    valid_df.to_csv(args.output_valid, index=False)
    invalid_df.to_csv(args.output_invalid, index=False)
    
    logger.info(f"Valid elements written to {args.output_valid} ({len(valid_rows)} rows)")
    logger.info(f"Invalid elements written to {args.output_invalid} ({len(invalid_rows)} rows)")
    
    return 0

if __name__ == "__main__":
    exit(main())
