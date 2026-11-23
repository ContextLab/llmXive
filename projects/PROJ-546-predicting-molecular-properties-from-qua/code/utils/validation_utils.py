"""
Validation utilities for molecular descriptor data.

Provides functions to validate:
- Required columns presence
- Physical ranges (HOMO < LUMO, charge sums)
- Data types
- Full validation suite
"""

import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


def validate_columns(filepath: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a CSV file contains all required columns.
    
    Args:
        filepath: Path to the CSV file
        required_columns: List of required column names
        
    Returns:
        Tuple of (is_valid, list of missing columns)
        
    Raises:
        ValidationError: If file doesn't exist or can't be read
    """
    if not filepath.exists():
        raise ValidationError(f"File not found: {filepath}")
    
    missing_columns = []
    
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValidationError(f"Empty CSV file: {filepath}")
            
            for col in required_columns:
                if col not in reader.fieldnames:
                    missing_columns.append(col)
    except Exception as e:
        raise ValidationError(f"Error reading CSV file: {e}")
    
    is_valid = len(missing_columns) == 0
    return is_valid, missing_columns


def validate_physical_ranges(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Validate physical ranges in descriptor data:
    - HOMO energy must be less than LUMO energy (both in eV)
    - Sum of Mulliken charges must equal net molecular charge (within tolerance)
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, list of error messages)
        
    Raises:
        ValidationError: If file doesn't exist or can't be read
    """
    if not filepath.exists():
        raise ValidationError(f"File not found: {filepath}")
    
    errors = []
    
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check required columns exist
            required = ['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge']
            if reader.fieldnames is None:
                raise ValidationError(f"Empty CSV file: {filepath}")
            
            for col in required:
                if col not in reader.fieldnames:
                    errors.append(f"Missing required column: {col}")
            
            if errors:
                return False, errors
            
            # Validate each row
            row_num = 1
            for row in reader:
                row_num += 1
                smiles = row.get('SMILES', 'unknown')
                
                try:
                    homo = float(row['HOMO_eV'])
                    lumo = float(row['LUMO_eV'])
                    net_charge = float(row['net_charge'])
                    
                    # Check HOMO < LUMO
                    if homo >= lumo:
                        errors.append(
                            f"Row {row_num} ({smiles}): HOMO ({homo} eV) >= LUMO ({lumo} eV)"
                        )
                    
                    # Parse Mulliken charges and verify sum
                    charges_str = row.get('mulliken_charges', '')
                    if charges_str:
                        try:
                            # Expecting format like "[1.2, -0.5, 0.3, ...]" or "1.2,-0.5,0.3,..."
                            charges_str = charges_str.strip()
                            if charges_str.startswith('[') and charges_str.endswith(']'):
                                charges_str = charges_str[1:-1]
                            
                            charges = [float(c.strip()) for c in charges_str.split(',') if c.strip()]
                            charge_sum = sum(charges)
                            
                            # Allow small tolerance for floating point
                            tolerance = 0.01
                            if abs(charge_sum - net_charge) > tolerance:
                                errors.append(
                                    f"Row {row_num} ({smiles}): Sum of Mulliken charges ({charge_sum:.4f}) "
                                    f"does not match net charge ({net_charge}) within tolerance ({tolerance})"
                                )
                        except (ValueError, AttributeError) as e:
                            errors.append(
                                f"Row {row_num} ({smiles}): Invalid Mulliken charges format: {charges_str}"
                            )
                    
                except ValueError as e:
                    errors.append(f"Row {row_num} ({smiles}): Invalid numeric value - {e}")
                
    except Exception as e:
        raise ValidationError(f"Error reading CSV file: {e}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_data_types(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Validate that data types are correct in the descriptor CSV.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        Tuple of (is_valid, list of error messages)
        
    Raises:
        ValidationError: If file doesn't exist or can't be read
    """
    if not filepath.exists():
        raise ValidationError(f"File not found: {filepath}")
    
    errors = []
    
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if reader.fieldnames is None:
                raise ValidationError(f"Empty CSV file: {filepath}")
            
            # Define expected types
            type_checks = {
                'SMILES': str,
                'HOMO_eV': float,
                'LUMO_eV': float,
                'net_charge': float,
                'mulliken_charges': str  # Stored as string representation of list
            }
            
            row_num = 1
            for row in reader:
                row_num += 1
                smiles = row.get('SMILES', 'unknown')
                
                for col, expected_type in type_checks.items():
                    if col not in row:
                        continue  # Handled by column validation
                    
                    value = row[col]
                    
                    if expected_type == float:
                        try:
                            float(value)
                        except (ValueError, TypeError):
                            errors.append(
                                f"Row {row_num} ({smiles}): Column '{col}' should be float, got '{value}'"
                            )
                    
                    elif expected_type == str:
                        if not isinstance(value, str):
                            errors.append(
                                f"Row {row_num} ({smiles}): Column '{col}' should be string, got {type(value)}"
                            )
                
    except Exception as e:
        raise ValidationError(f"Error reading CSV file: {e}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_full(filepath: Path, required_columns: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Run full validation suite on a descriptor CSV file.
    
    Args:
        filepath: Path to the CSV file
        required_columns: Optional list of required columns (defaults to standard set)
        
    Returns:
        Tuple of (is_valid, list of all error messages)
        
    Raises:
        ValidationError: If file doesn't exist or can't be read
    """
    if required_columns is None:
        required_columns = ['SMILES', 'HOMO_eV', 'LUMO_eV', 'mulliken_charges', 'net_charge']
    
    all_errors = []
    
    # Check columns
    try:
        col_valid, col_errors = validate_columns(filepath, required_columns)
        if not col_valid:
            all_errors.extend([f"Column error: {e}" for e in col_errors])
    except ValidationError as e:
        raise e
    
    # Check physical ranges
    try:
        range_valid, range_errors = validate_physical_ranges(filepath)
        if not range_valid:
            all_errors.extend(range_errors)
    except ValidationError as e:
        raise e
    
    # Check data types
    try:
        type_valid, type_errors = validate_data_types(filepath)
        if not type_valid:
            all_errors.extend(type_errors)
    except ValidationError as e:
        raise e
    
    is_valid = len(all_errors) == 0
    return is_valid, all_errors


def main():
    """Command-line interface for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate molecular descriptor CSV files'
    )
    parser.add_argument(
        'filepath',
        type=Path,
        help='Path to the CSV file to validate'
    )
    parser.add_argument(
        '--columns',
        nargs='+',
        default=None,
        help='Required columns (default: SMILES, HOMO_eV, LUMO_eV, mulliken_charges, net_charge)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed error messages'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(levelname)s: %(message)s'
    )
    
    try:
        is_valid, errors = validate_full(args.filepath, args.columns)
        
        if is_valid:
            logger.info(f"✓ Validation passed for {args.filepath}")
            sys.exit(0)
        else:
            logger.error(f"✗ Validation failed for {args.filepath} ({len(errors)} errors)")
            if args.verbose:
                for error in errors:
                    logger.error(f"  - {error}")
            sys.exit(1)
            
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(3)

if __name__ == '__main__':
    main()
