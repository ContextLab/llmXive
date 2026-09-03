"""
Clean and filter the dataset: canonicalize SMILES, filter primary alkyl halides.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import rdkit
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from config import DataConfig, ensure_dirs
from utils.logger import get_logger

def setup_cleaning_logger(log_file: Path):
    """Setup logging for the cleaning stage."""
    ensure_dirs()
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return get_logger(__name__)

def calculate_steric_index(smiles: str) -> float:
    """
    Calculate a simple steric index based on molecular weight and heavy atoms.
    Note: This is a proxy-free calculation using RDKit properties.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.0
        mw = rdMolDescriptors.CalcExactMolWt(mol)
        heavy_atoms = mol.GetNumHeavyAtoms()
        if heavy_atoms == 0:
            return 0.0
        return mw / heavy_atoms
    except Exception:
        return 0.0

def canonicalize_smiles(smiles: str) -> Optional[str]:
    """Canonicalize a SMILES string."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, isomericSmiles=True)
    except Exception:
        return None

def is_primary_substrate(mol: Chem.Mol) -> bool:
    """
    Check if the molecule is a primary alkyl halide.
    A primary alkyl halide has a carbon attached to the halogen that is attached to only one other carbon.
    """
    if mol is None:
        return False

    # Find halogen atoms (F, Cl, Br, I)
    halogens = [atom for atom in mol.GetAtoms() if atom.GetSymbol() in ['F', 'Cl', 'Br', 'I']]
    
    for halogen in halogens:
        neighbors = list(halogen.GetNeighbors())
        if len(neighbors) != 1:
            continue
        
        carbon = neighbors[0]
        if carbon.GetAtomicNum() != 6:
            continue
        
        # Count carbon neighbors of the alpha carbon (excluding the halogen)
        carbon_neighbors = [n for n in carbon.GetNeighbors() if n.GetAtomicNum() == 6]
        if len(carbon_neighbors) == 0:
            # Primary: alpha carbon attached to 0 other carbons (only H's and the halogen)
            return True
        
    return False

def clean_and_filter_data(input_path: Path, output_path: Path, exclusion_log_path: Path, log_file: Path):
    """Clean and filter the dataset."""
    logger = get_logger(__name__)
    exclusions = []

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # Write fatal error log
        with open(log_file, 'w') as f:
            f.write("status: 'fatal_error'\nreason: 'input_missing'\n")
        return

    with open(input_path, 'r', newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile, \
         open(exclusion_log_path, 'w', newline='', encoding='utf-8') as excl_file:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        if not fieldnames:
            logger.error("Empty input file")
            return

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        excl_writer = csv.writer(excl_file)
        excl_writer.writerow(["row_index", "reason", "original_smiles"])

        for i, row in enumerate(reader):
            smiles = row.get('smiles', '')
            if not smiles:
                exclusions.append((i, "missing_smiles", smiles))
                excl_writer.writerow([i, "missing_smiles", smiles])
                continue

            # Canonicalize
            canonical = canonicalize_smiles(smiles)
            if canonical is None:
                exclusions.append((i, "invalid_smiles", smiles))
                excl_writer.writerow([i, "invalid_smiles", smiles])
                continue

            # Check for stereochemistry ambiguity (simplified: if canonical differs significantly or has wildcards)
            # For this task, we assume canonicalization handles standard cases.
            # If specific stereo is needed, we'd check for '@' or '?'
            if '?' in canonical or '.' in canonical:
                exclusions.append((i, "ambiguous_stereochemistry", smiles))
                excl_writer.writerow([i, "ambiguous_stereochemistry", smiles])
                continue

            mol = Chem.MolFromSmiles(canonical)
            if mol is None:
                exclusions.append((i, "rdkit_parse_failed", smiles))
                excl_writer.writerow([i, "rdkit_parse_failed", smiles])
                continue

            # Filter primary substrates
            if is_primary_substrate(mol):
                exclusions.append((i, "primary_substrate_filter", smiles))
                excl_writer.writerow([i, "primary_substrate_filter", smiles])
                continue

            # Update SMILES with canonical
            row['smiles'] = canonical
            writer.writerow(row)

    logger.info(f"Cleaned {output_path}. Excluded {len(exclusions)} rows.")

def save_pre_filter_distribution(input_path: Path, output_path: Path):
    """Save the distribution of substrate classes before filtering."""
    distribution = {}
    if not input_path.exists():
        return

    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cls = row.get('substrate_class', 'unknown')
            distribution[cls] = distribution.get(cls, 0) + 1

    with open(output_path, 'w') as f:
        json.dump(distribution, f, indent=2)

def save_exclusion_report(exclusions: List[tuple], output_path: Path):
    """Save the exclusion report."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["row_index", "reason", "original_smiles"])
        for exc in exclusions:
            writer.writerow(exc)

def main():
    """Main entry point for cleaning."""
    config = DataConfig()
    ensure_dirs()
    log_file = Path(config.log_dir) / "clean.log"
    logger = setup_cleaning_logger(log_file)

    logger.info("Starting data cleaning...")

    input_path = Path(config.intermediate_sn1_path)
    output_path = Path(config.cleaned_intermediate_path)
    exclusion_log_path = Path(config.clean_log_path) # Reusing clean_log for exclusion details in this stage

    clean_and_filter_data(input_path, output_path, exclusion_log_path, log_file)

    # Save distribution
    dist_path = Path(config.log_dir) / "pre_filter_distribution.json"
    save_pre_filter_distribution(input_path, dist_path)

    logger.info("Data cleaning completed.")

if __name__ == "__main__":
    import csv # Import here to avoid circular if needed in module scope
    main()
