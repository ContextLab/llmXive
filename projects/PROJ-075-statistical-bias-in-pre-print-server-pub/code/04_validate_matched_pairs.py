"""
Validation module for matched_pairs.csv.

Ensures that included rows contain at least one valid p-value and one valid effect size
for both the pre-print and the journal versions.
"""
import os
import sys
import csv
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/validation_log.txt')
    ]
)
logger = logging.getLogger(__name__)

def has_valid_p_value(row: dict, venue: str) -> bool:
    """
    Check if the row contains at least one valid p-value for the specified venue.
    
    Args:
        row: Dictionary representing a row from matched_pairs.csv
        venue: Either 'preprint' or 'journal'
        
    Returns:
        True if a valid p-value exists, False otherwise
    """
    # Define column names based on venue
    if venue == 'preprint':
        p_col = 'preprint_p_value'
    elif venue == 'journal':
        p_col = 'journal_p_value'
    else:
        raise ValueError(f"Invalid venue: {venue}. Must be 'preprint' or 'journal'")
    
    if p_col not in row:
        logger.warning(f"Column {p_col} not found in row")
        return False
    
    value = row[p_col]
    if value is None or value == '' or pd.isna(value):
        return False
    
    # Check if it's a valid number (not an inequality string)
    try:
        p_val = float(value)
        if 0.0 < p_val <= 1.0:
            return True
        else:
            logger.debug(f"P-value {p_val} out of range (0, 1]")
            return False
    except (ValueError, TypeError):
        # Check if it's an inequality string (which should be excluded from analysis)
        # But for this validation, we require a valid numeric p-value
        logger.debug(f"P-value '{value}' is not a valid numeric value")
        return False

def has_valid_effect_size(row: dict, venue: str) -> bool:
    """
    Check if the row contains at least one valid effect size for the specified venue.
    
    Args:
        row: Dictionary representing a row from matched_pairs.csv
        venue: Either 'preprint' or 'journal'
        
    Returns:
        True if a valid effect size exists, False otherwise
    """
    # Define column names based on venue
    if venue == 'preprint':
        es_col = 'preprint_effect_size'
        es_type_col = 'preprint_effect_size_type'
    elif venue == 'journal':
        es_col = 'journal_effect_size'
        es_type_col = 'journal_effect_size_type'
    else:
        raise ValueError(f"Invalid venue: {venue}. Must be 'preprint' or 'journal'")
    
    if es_col not in row or es_type_col not in row:
        logger.warning(f"Effect size columns not found in row")
        return False
    
    es_value = row[es_col]
    es_type = row[es_type_col]
    
    if es_value is None or es_value == '' or pd.isna(es_value):
        return False
    
    if es_type is None or es_type == '':
        logger.debug("Effect size type is missing")
        return False
    
    try:
        es_num = float(es_value)
        # Effect sizes can be negative, so we just check if it's a valid number
        return True
    except (ValueError, TypeError):
        logger.debug(f"Effect size '{es_value}' is not a valid numeric value")
        return False

def validate_row(row: dict, row_num: int) -> dict:
    """
    Validate a single row from matched_pairs.csv.
    
    Args:
        row: Dictionary representing a row
        row_num: Row number for logging purposes
        
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        'row_num': row_num,
        'preprint_p_valid': has_valid_p_value(row, 'preprint'),
        'preprint_es_valid': has_valid_effect_size(row, 'preprint'),
        'journal_p_valid': has_valid_p_value(row, 'journal'),
        'journal_es_valid': has_valid_effect_size(row, 'journal'),
        'is_valid': False
    }
    
    # A row is valid if it has valid p-value and effect size for BOTH venues
    validation_result['is_valid'] = (
        validation_result['preprint_p_valid'] and
        validation_result['preprint_es_valid'] and
        validation_result['journal_p_valid'] and
        validation_result['journal_es_valid']
    )
    
    return validation_result

def main():
    """
    Main function to validate matched_pairs.csv.
    
    Reads the CSV, validates each row, and outputs:
    1. A validation report to data/processed/validation_report.txt
    2. A cleaned CSV with only valid rows to data/processed/matched_pairs_validated.csv
    """
    input_path = Path('data/processed/matched_pairs.csv')
    output_path = Path('data/processed/matched_pairs_validated.csv')
    report_path = Path('data/processed/validation_report.txt')
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Starting validation of {input_path}")
    
    valid_rows = []
    invalid_rows = []
    validation_details = []
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        if not fieldnames:
            logger.error("CSV file is empty or has no headers")
            sys.exit(1)
        
        logger.info(f"Found {len(fieldnames)} columns: {fieldnames}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
            result = validate_row(row, row_num)
            validation_details.append(result)
            
            if result['is_valid']:
                valid_rows.append(row)
            else:
                invalid_rows.append((row_num, result))
    
    # Write validation report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("Validation Report for matched_pairs.csv\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Total rows processed: {len(validation_details)}\n")
        f.write(f"Valid rows: {len(valid_rows)}\n")
        f.write(f"Invalid rows: {len(invalid_rows)}\n")
        f.write(f"Validation rate: {len(valid_rows) / len(validation_details) * 100:.2f}%\n")
        f.write("\n")
        f.write("Invalid Row Details:\n")
        f.write("-" * 80 + "\n")
        
        for row_num, details in invalid_rows:
            f.write(f"Row {row_num}:\n")
            f.write(f"  - Preprint p-value valid: {details['preprint_p_valid']}\n")
            f.write(f"  - Preprint effect size valid: {details['preprint_es_valid']}\n")
            f.write(f"  - Journal p-value valid: {details['journal_p_valid']}\n")
            f.write(f"  - Journal effect size valid: {details['journal_es_valid']}\n")
            f.write("-" * 80 + "\n")
    
    # Write validated CSV
    if fieldnames:
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_rows)
    
    logger.info(f"Validation complete. Valid rows: {len(valid_rows)}, Invalid rows: {len(invalid_rows)}")
    logger.info(f"Validation report written to: {report_path}")
    logger.info(f"Validated data written to: {output_path}")
    
    # Return summary for programmatic use
    return {
        'total_rows': len(validation_details),
        'valid_rows': len(valid_rows),
        'invalid_rows': len(invalid_rows),
        'validation_rate': len(valid_rows) / len(validation_details) * 100 if validation_details else 0
    }

if __name__ == '__main__':
    main()
