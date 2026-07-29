"""
T027 Implementation: Validate subset alignment between DFTB+ and DFT calculations.

This module ensures that the same set of molecules (identified by SMILES) is used
for both the semi-empirical (DFTB+) and high-level (DFT) descriptor sets, while
respecting that they utilize different optimized geometries as per FR-002 and FR-003.
"""
import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def load_smiles_set(file_path: Path) -> Set[str]:
    """
    Load the set of unique SMILES strings from a CSV file.
    Expects a CSV with a 'SMILES' column.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    smiles_set = set()
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'SMILES' not in reader.fieldnames:
                raise ValueError(f"File {file_path} is missing required 'SMILES' column. Found: {reader.fieldnames}")
            
            for row in reader:
                smiles = row['SMILES'].strip()
                if smiles:
                    smiles_set.add(smiles)
    except csv.Error as e:
        logger.error(f"CSV parsing error in {file_path}: {e}")
        raise
    
    logger.info(f"Loaded {len(smiles_set)} unique molecules from {file_path.name}")
    return smiles_set

def compare_subsets(
    semi_set: Set[str], 
    dft_set: Set[str], 
    semi_path: Path, 
    dft_path: Path
) -> Tuple[bool, List[str], List[str], List[str]]:
    """
    Compare two sets of SMILES to ensure they represent the same subset of molecules.
    
    Returns:
      is_aligned: True if sets are identical.
      missing_in_dft: SMILES present in semi but missing in dft.
      extra_in_dft: SMILES present in dft but missing in semi.
      missing_in_semi: SMILES present in dft but missing in semi (alias for clarity).
    """
    missing_in_dft = semi_set - dft_set
    extra_in_dft = dft_set - semi_set
    
    is_aligned = (missing_in_dft == set()) and (extra_in_dft == set())
    
    if not is_aligned:
        logger.warning(f"Mismatch detected between {semi_path.name} and {dft_path.name}")
        if missing_in_dft:
            logger.warning(f"  Molecules in DFTB+ but missing in DFT: {len(missing_in_dft)}")
        if extra_in_dft:
            logger.warning(f"  Molecules in DFT but missing in DFTB+: {len(extra_in_dft)}")
    else:
        logger.info("Subset alignment verified: Both datasets contain the exact same molecules.")
        
    return is_aligned, list(missing_in_dft), list(extra_in_dft), list(missing_in_dft)

def validate_subset_alignment(
    semi_descriptors_path: Path,
    dft_descriptors_path: Path,
    strict: bool = True
) -> bool:
    """
    Main validation logic for T027.
    
    Validates that the same subset of molecules is used for both DFTB+ and DFT
    calculations. This is critical for the paired t-test in US2 to be valid.
    
    Note: This validation checks molecule identity (SMILES). It acknowledges that
    DFTB+ uses DFTB-optimized geometries and DFT uses DFT-optimized geometries,
    but the underlying molecular graph (SMILES) must match.
    """
    logger.info(f"Starting subset alignment validation...")
    logger.info(f"  DFTB+ descriptors: {semi_descriptors_path}")
    logger.info(f"  DFT descriptors:   {dft_descriptors_path}")

    try:
        semi_smiles = load_smiles_set(semi_descriptors_path)
        dft_smiles = load_smiles_set(dft_descriptors_path)
    except Exception as e:
        logger.error(f"Failed to load descriptor files: {e}")
        return False

    is_aligned, missing_in_dft, extra_in_dft, _ = compare_subsets(
        semi_smiles, dft_smiles, semi_descriptors_path, dft_descriptors_path
    )

    if strict and not is_aligned:
        logger.error("Validation FAILED: Subsets do not match. The paired t-test cannot be performed.")
        return False
    elif not is_aligned:
        logger.warning("Validation WARNING: Subsets do not match (strict mode off). Proceed with caution.")
        return True
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Validate that the same subset of molecules is used for DFTB+ and DFT calculations."
    )
    parser.add_argument(
        "--semi-descriptors",
        type=str,
        required=True,
        help="Path to the semi-empirical descriptors CSV (e.g., data/descriptors_semi.csv)"
    )
    parser.add_argument(
        "--dft-descriptors",
        type=str,
        required=True,
        help="Path to the DFT descriptors CSV (e.g., data/descriptors_dft.csv)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Fail if subsets do not match exactly (default: True)"
    )
    
    args = parser.parse_args()
    
    semi_path = Path(args.semi_descriptors)
    dft_path = Path(args.dft_descriptors)
    
    if not semi_path.exists():
        logger.error(f"Semi-empirical file not found: {semi_path}")
        sys.exit(1)
    if not dft_path.exists():
        logger.error(f"DFT file not found: {dft_path}")
        sys.exit(1)
    
    success = validate_subset_alignment(semi_path, dft_path, strict=args.strict)
    
    if success:
        logger.info("Validation PASSED: Subsets are aligned.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED: Subsets are misaligned.")
        sys.exit(1)

if __name__ == "__main__":
    main()
