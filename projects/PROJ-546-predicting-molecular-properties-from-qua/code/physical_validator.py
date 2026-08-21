import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """Setup a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def validate_homo_lumo_relationship(homo: float, lumo: float) -> bool:
    """
    Validate that HOMO energy is strictly less than LUMO energy.
    
    Args:
        homo: HOMO energy in eV
        lumo: LUMO energy in eV
        
    Returns:
        True if HOMO < LUMO, False otherwise
    """
    return homo < lumo

def log_structural_failure(
    logger: logging.Logger,
    molecule_id: str,
    homo: float,
    lumo: float,
    error_code: str = "HOMO_LUMO_VIOLATION",
    error_message: Optional[str] = None
) -> None:
    """
    Log a structural failure where HOMO >= LUMO.
    
    Args:
        logger: Logger instance
        molecule_id: ID of the molecule that failed validation
        homo: HOMO energy value
        lumo: LUMO energy value
        error_code: Error code for the failure
        error_message: Optional detailed error message
    """
    if error_message is None:
        error_message = f"HOMO ({homo:.6f} eV) is not less than LUMO ({lumo:.6f} eV)"
    
    log_entry = {
        "molecule_id": molecule_id,
        "timestamp": None,  # Will be added by logger
        "error_code": error_code,
        "error_message": error_message,
        "homo_energy": homo,
        "lumo_energy": lumo,
        "status": "failed_after_retry"
    }
    
    logger.error(f"Structural failure for {molecule_id}: {error_message}")

def validate_descriptors_file(
    input_path: str,
    output_log_path: str,
    homo_col: str = "HOMO_energy",
    lumo_col: str = "LUMO_energy",
    id_col: str = "molecule_id"
) -> Tuple[int, int]:
    """
    Validate a descriptors CSV file for HOMO < LUMO constraint.
    
    Args:
        input_path: Path to the input CSV file
        output_log_path: Path to the structural failures log file
        homo_col: Name of the HOMO energy column
        lumo_col: Name of the LUMO energy column
        id_col: Name of the molecule ID column
        
    Returns:
        Tuple of (valid_count, invalid_count)
    """
    logger = setup_logger(
        "physical_validator",
        output_log_path,
        logging.INFO
    )
    
    valid_count = 0
    invalid_count = 0
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return 0, 0
    
    with open(input_path, 'r', newline='') as infile:
        reader = csv.DictReader(infile)
        
        # Validate columns exist
        if reader.fieldnames is None:
            logger.error("CSV file is empty or has no headers")
            return 0, 0
        
        if id_col not in reader.fieldnames:
            logger.error(f"Required column '{id_col}' not found in {input_path}")
            return 0, 0
        if homo_col not in reader.fieldnames:
            logger.error(f"Required column '{homo_col}' not found in {input_path}")
            return 0, 0
        if lumo_col not in reader.fieldnames:
            logger.error(f"Required column '{lumo_col}' not found in {input_path}")
            return 0, 0
        
        for row_num, row in enumerate(reader, start=2):
            molecule_id = row.get(id_col, f"row_{row_num}")
            
            try:
                homo = float(row.get(homo_col, 0.0))
                lumo = float(row.get(lumo_col, 0.0))
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid numeric value at row {row_num}: {e}")
                invalid_count += 1
                log_structural_failure(
                    logger,
                    molecule_id,
                    homo if 'homo' in locals() else 0.0,
                    lumo if 'lumo' in locals() else 0.0,
                    error_code="INVALID_NUMERIC",
                    error_message=f"Could not parse HOMO/LUMO values: {e}"
                )
                continue
            
            if validate_homo_lumo_relationship(homo, lumo):
                valid_count += 1
            else:
                invalid_count += 1
                log_structural_failure(
                    logger,
                    molecule_id,
                    homo,
                    lumo,
                    error_code="HOMO_LUMO_VIOLATION",
                    error_message=f"HOMO ({homo:.6f} eV) >= LUMO ({lumo:.6f} eV)"
                )
    
    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
    return valid_count, invalid_count

def main():
    """Main entry point for physical validator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate molecular descriptors for HOMO < LUMO constraint"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/descriptors_semi.csv",
        help="Path to input descriptors CSV file"
    )
    parser.add_argument(
        "--log",
        type=str,
        default="logs/structural_failures.log",
        help="Path to output log file for structural failures"
    )
    parser.add_argument(
        "--homo-col",
        type=str,
        default="HOMO_energy",
        help="Name of the HOMO energy column"
    )
    parser.add_argument(
        "--lumo-col",
        type=str,
        default="LUMO_energy",
        help="Name of the LUMO energy column"
    )
    parser.add_argument(
        "--id-col",
        type=str,
        default="molecule_id",
        help="Name of the molecule ID column"
    )
    
    args = parser.parse_args()
    
    # Ensure log directory exists
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    valid_count, invalid_count = validate_descriptors_file(
        input_path=args.input,
        output_log_path=str(log_path),
        homo_col=args.homo_col,
        lumo_col=args.lumo_col,
        id_col=args.id_col
    )
    
    if invalid_count > 0:
        print(f"Warning: {invalid_count} molecules failed HOMO < LUMO validation. "
              f"See {args.log} for details.")
        sys.exit(1)
    else:
        print(f"Success: All {valid_count} molecules passed HOMO < LUMO validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()