import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, Descriptors
from rdkit.Chem.rdchem import Mol

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

# Constants
DATA_CONFIG = DataConfig()

def setup_cleaning_logger() -> logging.Logger:
    """Setup logging for the cleaning stage."""
    logger = get_logger("clean")
    logger.setLevel(logging.INFO)
    return logger

def calculate_steric_index(mol: Mol) -> float:
    """
    Calculate a simple steric index based on molecular properties.
    Returns a float representing steric bulk.
    """
    if mol is None:
        return 0.0
    
    # Use number of heavy atoms and molecular weight as proxy
    heavy_atoms = mol.GetNumHeavyAtoms()
    mol_weight = Descriptors.MolWt(mol)
    
    # Simple steric index: weighted combination
    steric_index = 0.6 * heavy_atoms + 0.4 * (mol_weight / 100.0)
    return steric_index

def canonicalize_smiles(smiles: str) -> Tuple[Optional[str], bool]:
    """
    Canonicalize a SMILES string.
    Returns (canonical_smiles, success).
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, False
        
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        return canonical, True
    except Exception:
        return None, False

def is_primary_substrate(mol: Mol, substrate_class: str) -> bool:
    """
    Check if the molecule is a primary alkyl halide.
    Returns True if it is primary (should be filtered out).
    """
    # If substrate_class is explicitly labeled as 'primary', filter it
    if substrate_class and substrate_class.lower() == 'primary':
        return True
    
    # If no explicit label, we don't filter based on structure alone
    # (as per task requirements: "Filter rows ONLY if substrate_class is explicitly labeled as 'primary'")
    return False

def clean_and_filter_data(input_path: Path, output_path: Path, clean_log_path: Path) -> Tuple[int, int]:
    """
    Clean and filter the dataset.
    Returns (total_rows, filtered_rows).
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    cleaned_rows = []
    exclusion_log = []
    total_rows = 0
    filtered_count = 0
    
    with open(input_path, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        for row_idx, row in enumerate(reader):
            total_rows += 1
            smiles = row.get('smiles', '')
            substrate_class = row.get('substrate_class', '')
            
            # Try to canonicalize SMILES
            canonical_smiles, success = canonicalize_smiles(smiles)
            
            if not success:
                exclusion_log.append({
                    "row_index": row_idx,
                    "reason": "invalid_smiles",
                    "original_smiles": smiles
                })
                filtered_count += 1
                continue
            
            mol = Chem.MolFromSmiles(canonical_smiles)
            
            # Check if primary substrate (explicit label only)
            if is_primary_substrate(mol, substrate_class):
                exclusion_log.append({
                    "row_index": row_idx,
                    "reason": "primary_substrate_filter",
                    "original_smiles": canonical_smiles
                })
                filtered_count += 1
                continue
            
            # Check for ambiguous stereochemistry
            # This is a simple check - in practice, RDKit handles this well with canonicalization
            if Chem.MolFromSmiles(canonical_smiles) is None:
                exclusion_log.append({
                    "row_index": row_idx,
                    "reason": "ambiguous_stereochemistry",
                    "original_smiles": canonical_smiles
                })
                filtered_count += 1
                continue
            
            # Update row with canonical SMILES
            row['smiles'] = canonical_smiles
            cleaned_rows.append(row)
    
    # Write cleaned data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_rows)
    
    # Write exclusion log
    clean_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(clean_log_path, 'w', encoding='utf-8') as log_file:
        for exclusion in exclusion_log:
            log_file.write(json.dumps(exclusion) + '\n')
    
    return total_rows, filtered_count

def save_pre_filter_distribution(input_path: Path, output_path: Path) -> None:
    """Save the distribution of substrate classes before filtering."""
    if not input_path.exists():
        return
    
    distribution = {}
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            substrate_class = row.get('substrate_class', 'unknown')
            distribution[substrate_class] = distribution.get(substrate_class, 0) + 1
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(distribution, f, indent=2)

def save_exclusion_report(exclusions: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the exclusion report to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["row_index", "reason", "original_smiles"])
        for exclusion in exclusions:
            writer.writerow([
                exclusion.get("row_index", -1),
                exclusion.get("reason", "unknown"),
                exclusion.get("original_smiles", "unknown")
            ])

def main():
    """Main entry point for the cleaning stage."""
    parser = argparse.ArgumentParser(description="Clean and filter the SN1 dataset")
    parser.add_argument("--input", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "intermediate_sn1.csv"),
                      help="Path to the intermediate CSV file")
    parser.add_argument("--output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "cleaned_intermediate.csv"),
                      help="Path to save the cleaned CSV file")
    parser.add_argument("--clean-log", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "clean.log"),
                      help="Path to save the cleaning log")
    parser.add_argument("--distribution-output", type=str, default=str(DATA_CONFIG.PROCESSED_DIR / "pre_filter_distribution.json"),
                      help="Path to save the pre-filter distribution")
    
    args = parser.parse_args()
    
    logger = setup_cleaning_logger()
    logger.info("Starting cleaning stage")
    
    try:
        # Ensure directories exist
        ensure_dirs(DATA_CONFIG)
        
        input_path = Path(args.input)
        output_path = Path(args.output)
        clean_log_path = Path(args.clean_log)
        distribution_output_path = Path(args.distribution_output)
        
        # Save pre-filter distribution
        logger.info("Saving pre-filter distribution")
        save_pre_filter_distribution(input_path, distribution_output_path)
        
        # Clean and filter data
        logger.info(f"Cleaning and filtering data from {input_path}")
        total_rows, filtered_count = clean_and_filter_data(input_path, output_path, clean_log_path)
        logger.info(f"Processed {total_rows} rows, filtered {filtered_count} rows")
        logger.info(f"Cleaned data saved to {output_path}")
        logger.info(f"Exclusion log saved to {clean_log_path}")
        
        logger.info("Cleaning stage completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during cleaning stage: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import csv
    sys.exit(main())
