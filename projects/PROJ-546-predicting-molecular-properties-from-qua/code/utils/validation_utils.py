"""
Validation utilities for molecular descriptor output.

Validates that the generated CSV file contains required columns,
correct data types, and physically reasonable ranges (HOMO < LUMO, charge sum).
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when validation of descriptor output fails."""
    pass

REQUIRED_COLUMNS = [
    'smiles', 
    'molecule_id', 
    'homo', 
    'lumo', 
    'mayer_bond_order', 
    'total_charge', 
    'convergence_status'
]

def validate_columns(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Verify that the CSV file contains all required columns.
    
    Args:
        filepath: Path to the CSV file to validate
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    if not filepath.exists():
        raise ValidationError(f"File does not exist: {filepath}")
    
    missing = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValidationError("CSV file is empty or has no header")
            
            for col in REQUIRED_COLUMNS:
                if col not in reader.fieldnames:
                    missing.append(col)
    except csv.Error as e:
        raise ValidationError(f"Failed to read CSV: {e}")
    
    return len(missing) == 0, missing

def validate_physical_ranges(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Verify that physical values are in reasonable ranges.
    
    Checks:
    - HOMO < LUMO for all molecules
    - Total charge sum is within reasonable bounds (typically -10 to +10)
    - No NaN or infinite values in numeric columns
    
    Args:
        filepath: Path to the CSV file to validate
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    numeric_cols = ['homo', 'lumo', 'total_charge']
    
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader, start=2):  # Start at 2 (1-indexed + header)
                # Check for NaN/Inf in numeric columns
                for col in numeric_cols:
                    if col not in row:
                        errors.append(f"Row {row_idx}: Missing column '{col}'")
                        continue
                    
                    try:
                        val = float(row[col])
                        if val != val:  # NaN check
                            errors.append(f"Row {row_idx}: {col} is NaN")
                        elif val == float('inf') or val == float('-inf'):
                            errors.append(f"Row {row_idx}: {col} is infinite")
                    except ValueError:
                        errors.append(f"Row {row_idx}: {col} is not a valid number: {row[col]}")
                
                # Check HOMO < LUMO
                if 'homo' in row and 'lumo' in row:
                    try:
                        homo = float(row['homo'])
                        lumo = float(row['lumo'])
                        if not (homo != homo or lumo != lumo):  # Skip if NaN
                            if homo >= lumo:
                                errors.append(
                                    f"Row {row_idx}: HOMO ({homo:.4f}) >= LUMO ({lumo:.4f})"
                                )
                    except ValueError:
                        pass  # Already caught above
                
                # Check total charge bounds (typical organic molecules: -5 to +5)
                if 'total_charge' in row:
                    try:
                        charge = float(row['total_charge'])
                        if charge < -10 or charge > 10:
                            errors.append(
                                f"Row {row_idx}: Total charge ({charge:.4f}) outside "
                                f"reasonable bounds [-10, 10]"
                            )
                    except ValueError:
                        pass  # Already caught above
                        
    except csv.Error as e:
        raise ValidationError(f"Failed to read CSV: {e}")
    
    return len(errors) == 0, errors

def validate_data_types(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Verify that data types are correct for each column.
    
    Args:
        filepath: Path to the CSV file to validate
        
    Returns:
        Tuple of (is_valid, list_of_error_messages)
    """
    errors = []
    
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_idx, row in enumerate(reader, start=2):
                # SMILES should be a non-empty string
                if 'smiles' in row:
                    if not row['smiles'] or not isinstance(row['smiles'], str):
                        errors.append(f"Row {row_idx}: SMILES is empty or invalid type")
                
                # Numeric columns should be parseable as float
                for col in ['homo', 'lumo', 'total_charge']:
                    if col in row:
                        try:
                            float(row[col])
                        except ValueError:
                            errors.append(
                                f"Row {row_idx}: {col} is not a valid float: {row[col]}"
                            )
                
                # Mayer bond order should be non-negative
                if 'mayer_bond_order' in row:
                    try:
                        mbo = float(row['mayer_bond_order'])
                        if mbo < 0:
                            errors.append(
                                f"Row {row_idx}: Mayer bond order ({mbo:.4f}) is negative"
                            )
                    except ValueError:
                        errors.append(
                            f"Row {row_idx}: Mayer bond order is not a valid float: {row['mayer_bond_order']}"
                        )
                
                # Convergence status should be 'success' or 'failure'
                if 'convergence_status' in row:
                    status = row['convergence_status'].lower()
                    if status not in ['success', 'failure']:
                        errors.append(
                            f"Row {row_idx}: Invalid convergence_status: {row['convergence_status']}"
                        )
                        
    except csv.Error as e:
        raise ValidationError(f"Failed to read CSV: {e}")
    
    return len(errors) == 0, errors

def validate_full(filepath: Path) -> bool:
    """
    Run all validations on the descriptor output file.
    
    Args:
        filepath: Path to the CSV file to validate
        
    Returns:
        True if all validations pass, False otherwise
        
    Raises:
        ValidationError: If any validation fails
    """
    # Validate columns
    cols_ok, missing_cols = validate_columns(filepath)
    if not cols_ok:
        raise ValidationError(
            f"Missing required columns: {', '.join(missing_cols)}"
        )
    
    # Validate physical ranges
    ranges_ok, range_errors = validate_physical_ranges(filepath)
    if not ranges_ok:
        error_msg = "; ".join(range_errors)
        raise ValidationError(f"Physical range validation failed: {error_msg}")
    
    # Validate data types
    types_ok, type_errors = validate_data_types(filepath)
    if not types_ok:
        error_msg = "; ".join(type_errors)
        raise ValidationError(f"Data type validation failed: {error_msg}")
    
    logger.info(f"Validation passed for {filepath}")
    return True

def main():
    """CLI entry point for validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate molecular descriptor output CSV'
    )
    parser.add_argument(
        'filepath',
        type=Path,
        help='Path to the CSV file to validate'
    )
    
    args = parser.parse_args()
    
    try:
        if validate_full(args.filepath):
            print(f"✓ Validation passed for {args.filepath}")
            sys.exit(0)
    except ValidationError as e:
        print(f"✗ Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
