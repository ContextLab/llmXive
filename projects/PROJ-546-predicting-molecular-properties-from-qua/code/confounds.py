"""
Confounds Analysis (T011)

Reads SMILES from data/raw/barrier_dataset.csv, converts to RDKit Mol objects,
calculates molecular weight, atom count, and functional groups.
Outputs data/confounds.csv and logs distribution stats to data/confounds_verification.log.
"""
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import logging

# RDKit imports
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Fragments

# Project imports
from config import PROJECT_ROOT

# Constants
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "barrier_dataset.csv"
OUTPUT_CSV_PATH = PROJECT_ROOT / "data" / "confounds.csv"
VERIFICATION_LOG_PATH = PROJECT_ROOT / "data" / "confounds_verification.log"

# Setup logging for this module
logger = logging.getLogger("confounds_analysis")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def load_molecules_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Loads SMILES strings from the barrier dataset CSV.
    Raises FileNotFoundError if the file does not exist.
    """
    if not csv_path.exists():
        logger.error(f"Input file not found: {csv_path}")
        raise FileNotFoundError(f"Input file not found: {csv_path}")

    molecules = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'SMILES' in row:
                molecules.append({
                    'molecule_id': row.get('molecule_id', f"mol_{len(molecules)}"),
                    'smiles': row['SMILES']
                })
            else:
                # Fallback if column name differs, though spec says SMILES
                # Try to find a column that looks like SMILES
                for key in row.keys():
                    if 'smiles' in key.lower():
                        molecules.append({
                            'molecule_id': row.get('molecule_id', f"mol_{len(molecules)}"),
                            'smiles': row[key]
                        })
                        break
    logger.info(f"Loaded {len(molecules)} molecules from {csv_path}")
    return molecules

def parse_functional_groups(mol: Chem.Mol) -> str:
    """
    Identifies functional groups using RDKit Fragments and Lipinski rules.
    Returns a comma-separated string of detected group names.
    """
    groups = []
    
    # Common functional group checks using Fragments module
    # Note: RDKit Fragments functions return counts (float), we check if > 0
    if Fragments.fr_Aldehyde(mol) > 0:
        groups.append("Aldehyde")
    if Fragments.fr_Ketone(mol) > 0:
        groups.append("Ketone")
    if Fragments.fr_CarboxylicAcid(mol) > 0:
        groups.append("CarboxylicAcid")
    if Fragments.fr_Ester(mol) > 0:
        groups.append("Ester")
    if Fragments.fr_Amine(mol) > 0:
        groups.append("Amine")
    if Fragments.fr_Amide(mol) > 0:
        groups.append("Amide")
    if Fragments.fr_Alcohol(mol) > 0:
        groups.append("Alcohol")
    if Fragments.fr_Aromatic(mol) > 0:
        groups.append("Aromatic")
    if Fragments.fr_Ether(mol) > 0:
        groups.append("Ether")
    if Fragments.fr_Halide(mol) > 0:
        groups.append("Halide")
    if Fragments.fr_Nitro(mol) > 0:
        groups.append("Nitro")
    if Fragments.fr_Nitrile(mol) > 0:
        groups.append("Nitrile")
    if Fragments.fr_Thiol(mol) > 0:
        groups.append("Thiol")
    
    # Lipinski checks (often overlap with fragments, but distinct logic)
    # We rely on Fragments for specific chemical moieties
    
    if not groups:
        return "None"
    
    return "; ".join(sorted(list(set(groups))))

def calculate_molecular_properties(mol: Chem.Mol) -> Dict[str, Any]:
    """
    Calculates MW, Atom Count, and Functional Groups.
    """
    mw = Descriptors.MolWt(mol)
    atom_count = Descriptors.NumAtoms(mol)
    func_groups = parse_functional_groups(mol)
    
    return {
        'mw': mw,
        'atom_count': atom_count,
        'functional_groups': func_groups
    }

def process_molecule(mol_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Converts SMILES to Mol and calculates properties.
    Returns None if parsing fails.
    """
    smiles = mol_record['smiles']
    mol_id = mol_record['molecule_id']
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES for {mol_id}: {smiles}")
            return None
        
        props = calculate_molecular_properties(mol)
        return {
            'molecule_id': mol_id,
            'mw': props['mw'],
            'atom_count': props['atom_count'],
            'functional_groups': props['functional_groups']
        }
    except Exception as e:
        logger.error(f"Error processing {mol_id}: {e}")
        return None

def write_confounds_csv(results: List[Dict[str, Any]], output_path: Path):
    """
    Writes the confounds analysis results to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['molecule_id', 'mw', 'atom_count', 'functional_groups']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    logger.info(f"Wrote {len(results)} records to {output_path}")

def verify_distribution_stats(results: List[Dict[str, Any]], log_path: Path):
    """
    Calculates mean/std for MW and atom_count and logs to verification log.
    """
    if not results:
        logger.warning("No results to verify statistics.")
        return

    mws = [r['mw'] for r in results]
    atom_counts = [r['atom_count'] for r in results]

    # Calculate stats
    mean_mw = sum(mws) / len(mws)
    std_mw = (sum((x - mean_mw) ** 2 for x in mws) / len(mws)) ** 0.5
    
    mean_ac = sum(atom_counts) / len(atom_counts)
    std_ac = (sum((x - mean_ac) ** 2 for x in atom_counts) / len(atom_counts)) ** 0.5

    # Write to log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("Confounds Analysis Verification Log\n")
        f.write(f"Status: PASS (stats calculated)\n")
        f.write(f"Total molecules: {len(results)}\n")
        f.write(f"Molecular Weight - Mean: {mean_mw:.4f}, Std: {std_mw:.4f}\n")
        f.write(f"Atom Count - Mean: {mean_ac:.4f}, Std: {std_ac:.4f}\n")
    
    logger.info(f"Verification stats written to {log_path}")

def main():
    """
    Main entry point for T011 Confounds Analysis.
    """
    logger.info("Starting Confounds Analysis (T011)...")
    
    # 1. Load data (fails loudly if missing)
    try:
        molecules = load_molecules_from_csv(RAW_DATA_PATH)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise e

    # 2. Process molecules
    results = []
    for mol_rec in molecules:
        res = process_molecule(mol_rec)
        if res:
            results.append(res)

    if not results:
        logger.error("No valid molecules processed. Aborting.")
        sys.exit(1)

    # 3. Write output CSV
    write_confounds_csv(results, OUTPUT_CSV_PATH)

    # 4. Verify and log stats (FR-008)
    verify_distribution_stats(results, VERIFICATION_LOG_PATH)

    logger.info("Confounds Analysis (T011) completed successfully.")

if __name__ == "__main__":
    main()
