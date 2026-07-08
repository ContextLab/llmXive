import os
import sys
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def is_bmg_phase(row: Dict[str, Any]) -> bool:
    """
    Check if the material entry corresponds to a Bulk Metallic Glass.
    Heuristic: checks for 'glass' or 'amorphous' in phase/type fields.
    """
    phase = str(row.get('phase', '')).lower()
    structure = str(row.get('structure_type', '')).lower()
    return 'glass' in phase or 'amorphous' in phase or 'bulk' in phase

def standardize_units(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standardize units in the row to SI or standard scientific units.
    Currently a placeholder for specific unit conversion logic.
    """
    # Ensure modulus is in GPa
    if 'shear_modulus_gpa' not in row and 'shear_modulus' in row:
        val = row['shear_modulus']
        unit = str(row.get('shear_modulus_unit', 'GPa')).upper()
        if unit == 'PA':
            row['shear_modulus_gpa'] = float(val) / 1e9
        elif unit == 'KPA':
            row['shear_modulus_gpa'] = float(val) / 1e6
        elif unit == 'MPA':
            row['shear_modulus_gpa'] = float(val) / 1e3
        else:
            row['shear_modulus_gpa'] = float(val)
    return row

def clean_and_filter(input_path: str, output_path: str) -> int:
    """
    Load raw CSV, filter for BMG phase, standardize units, and save.
    Returns the count of rows written.
    """
    logger.info(f"Cleaning data from {input_path}")
    rows_written = 0
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if 'shear_modulus_gpa' not in fieldnames:
            fieldnames = list(fieldnames) + ['shear_modulus_gpa']

        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                if is_bmg_phase(row):
                    cleaned_row = standardize_units(row)
                    writer.writerow(cleaned_row)
                    rows_written += 1
    
    logger.info(f"Cleaned data written to {output_path} ({rows_written} rows)")
    return rows_written

def main():
    """Entry point for running the cleaning script."""
    # Default paths for standalone execution
    input_file = "data/raw/initial_bmg_data.csv"
    output_file = "data/processed/cleaned_bmg_data.csv"
    
    # Override if arguments provided (simple parsing)
    if len(sys.argv) >= 2:
        input_file = sys.argv[1]
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
        
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
        
    clean_and_filter(input_file, output_file)

if __name__ == "__main__":
    main()
