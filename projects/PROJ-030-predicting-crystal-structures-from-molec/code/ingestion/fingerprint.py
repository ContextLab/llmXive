"""
Fingerprint generation module for crystal structure prediction.

Generates ECFP4 fingerprints from SMILES strings using RDKit.
Handles MemoryError by logging and excluding large molecules.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit import DataStructs

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ingestion.models import MoleculeRecord
from logging_config import get_logger, log_event
from error_handling import handle_memory_error
from config import get_path_absolute

# Constants
FINGERPRINT_RADIUS = 2  # ECFP4 uses radius 2
FINGERPRINT_BITS = 2048  # Standard bit length
MOLECULE_MW_THRESHOLD = 1000.0  # MW threshold to skip large molecules

logger = get_logger(__name__)

class FingerprintError(Exception):
    """Custom exception for fingerprint generation errors."""
    pass

def smiles_to_mol(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert a SMILES string to an RDKit Mol object.

    Args:
        smiles: SMILES string representation of a molecule

    Returns:
        RDKit Mol object or None if parsing fails
    """
    if not smiles or not isinstance(smiles, str):
        return None

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None

        # Add hydrogens for better fingerprint generation
        mol = Chem.AddHs(mol)
        return mol
    except Exception as e:
        logger.warning(f"Error converting SMILES to mol: {e}")
        return None

def generate_ecfp4(mol: Chem.Mol, bits: int = FINGERPRINT_BITS, radius: int = FINGERPRINT_RADIUS) -> Optional[List[int]]:
    """
    Generate ECFP4 fingerprint for a molecule.

    Args:
        mol: RDKit Mol object
        bits: Number of bits in fingerprint (default 2048)
        radius: Radius for ECFP (default 2 for ECFP4)

    Returns:
        List of bit indices set to 1, or None if generation fails
    """
    try:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=bits)
        # Convert to list of indices where bits are set
        indices = list(fp.GetOnBits())
        return indices
    except Exception as e:
        logger.error(f"Error generating ECFP4 fingerprint: {e}")
        return None

def get_molecular_weight(mol: Chem.Mol) -> float:
    """
    Calculate molecular weight of a molecule.

    Args:
        mol: RDKit Mol object

    Returns:
        Molecular weight in g/mol
    """
    try:
      return Chem.Descriptors.MolWt(mol)
    except Exception:
        return 0.0

def process_molecule_for_fingerprint(
    mol: Chem.Mol,
    smiles: str,
    bits: int = FINGERPRINT_BITS,
    radius: int = FINGERPRINT_RADIUS,
    mw_threshold: float = MOLECULE_MW_THRESHOLD
) -> Optional[Tuple[List[int], float]]:
    """
    Process a molecule to generate fingerprint, with memory and size checks.

    Args:
        mol: RDKit Mol object
        smiles: Original SMILES string
        bits: Number of fingerprint bits
        radius: ECFP radius
        mw_threshold: Molecular weight threshold to skip large molecules

    Returns:
        Tuple of (fingerprint_indices, molecular_weight) or None if skipped
    """
    # Check molecular weight first
    mw = get_molecular_weight(mol)
    if mw > mw_threshold:
        logger.info(f"Skipping molecule with MW {mw:.2f} > {mw_threshold} (SMILES: {smiles[:50]}...)")
        return None

    # Generate fingerprint with memory error handling
    try:
        fp_indices = generate_ecfp4(mol, bits, radius)
        if fp_indices is None:
            logger.warning(f"Failed to generate fingerprint for: {smiles}")
            return None
        return (fp_indices, mw)
    except MemoryError:
        handle_memory_error(f"Memory error generating fingerprint for: {smiles}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing molecule {smiles}: {e}")
        return None

def fingerprints_to_bit_vectors(
    fingerprint_list: List[List[int]],
    n_bits: int = FINGERPRINT_BITS
) -> List[List[int]]:
    """
    Convert lists of set bit indices to fixed-length bit vectors.

    Args:
        fingerprint_list: List of lists of set bit indices
        n_bits: Total number of bits in each vector

    Returns:
        List of fixed-length bit vectors (0s and 1s)
    """
    bit_vectors = []
    for fp_indices in fingerprint_list:
        vector = [0] * n_bits
        for idx in fp_indices:
            if 0 <= idx < n_bits:
                vector[idx] = 1
        bit_vectors.append(vector)
    return bit_vectors

def generate_fingerprints_for_dataset(
    molecules: List[Dict[str, Any]],
    output_path: Optional[str] = None,
    bits: int = FINGERPRINT_BITS,
    radius: int = FINGERPRINT_RADIUS
) -> List[Dict[str, Any]]:
    """
    Generate fingerprints for a list of molecule records.

    Args:
        molecules: List of molecule dictionaries with 'smiles' key
        output_path: Optional path to save results as CSV
        bits: Number of fingerprint bits
        radius: ECFP radius

    Returns:
        List of molecule records with fingerprint data added
    """
    logger.info(f"Starting fingerprint generation for {len(molecules)} molecules")

    results = []
    skipped_count = 0
    error_count = 0

    for i, mol_data in enumerate(molecules):
        smiles = mol_data.get('smiles', '')
        if not smiles:
            logger.warning(f"Skipping record {i}: missing SMILES")
            error_count += 1
            continue

        mol = smiles_to_mol(smiles)
        if mol is None:
            error_count += 1
            continue

        try:
            result = process_molecule_for_fingerprint(mol, smiles, bits, radius)
            if result is None:
                skipped_count += 1
                continue

            fp_indices, mw = result

            # Create result record
            record = {
                **mol_data,
                'molecular_weight': mw,
                'fingerprint_indices': fp_indices,
                'fingerprint_length': bits
            }
            results.append(record)

            # Progress logging
            if (i + 1) % 100 == 0:
                logger.info(f"Processed {i + 1}/{len(molecules)} molecules "
                            f"(skipped: {skipped_count}, errors: {error_count})")

        except MemoryError:
            handle_memory_error(f"Memory error at molecule {i}: {smiles[:50]}")
            skipped_count += 1
            continue
        except Exception as e:
            logger.error(f"Error processing molecule {i}: {e}")
            error_count += 1
            continue

    logger.info(f"Fingerprint generation complete: "
                f"{len(results)} successful, {skipped_count} skipped, {error_count} errors")

    # Save to CSV if output path provided
    if output_path:
        save_fingerprints_to_csv(results, output_path)

    return results

def save_fingerprints_to_csv(records: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save fingerprint results to a CSV file.

    Args:
        records: List of molecule records with fingerprint data
        output_path: Path to output CSV file
    """
    import csv

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'smiles', 'molecular_weight', 'fingerprint_length',
        'fingerprint_indices', 'space_group', 'lattice_a', 'lattice_b',
        'lattice_c', 'lattice_alpha', 'lattice_beta', 'lattice_gamma'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            # Convert fingerprint_indices to string for CSV storage
            row = {k: v for k, v in record.items() if k in fieldnames}
            if 'fingerprint_indices' in row:
                row['fingerprint_indices'] = ';'.join(map(str, row['fingerprint_indices']))
            writer.writerow(row)

    logger.info(f"Saved {len(records)} records to {output_path}")

def main():
    """Main entry point for fingerprint generation script."""
    logger.info("Starting fingerprint generation module")

    # Example usage with sample data
    sample_molecules = [
        {'smiles': 'CCO', 'space_group': 'P21/c'},
        {'smiles': 'c1ccccc1', 'space_group': 'P21/c'},
        {'smiles': 'CC(=O)Oc1ccccc1C(=O)O', 'space_group': 'P1'}
    ]

    results = generate_fingerprints_for_dataset(
        sample_molecules,
        output_path=str(get_path_absolute('data/processed/sample_fingerprints.csv')),
        bits=FINGERPRINT_BITS,
        radius=FINGERPRINT_RADIUS
    )

    logger.info(f"Generated fingerprints for {len(results)} molecules")

    # Verify results
    for record in results:
        if 'fingerprint_indices' not in record:
            logger.error(f"Missing fingerprint for: {record.get('smiles')}")
        else:
            logger.info(f"SMILES: {record['smiles'][:30]}... -> {len(record['fingerprint_indices'])} bits")

    return results

if __name__ == "__main__":
    main()
