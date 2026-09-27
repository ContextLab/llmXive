"""
Conformer generation module for molecular flexibility analysis.

This module implements the generation of 3D conformer ensembles using RDKit.
It adheres to FR-003 by generating ensembles of size 50 with an energy window
of <= 10 kcal/mol.

Dependencies:
- rdkit
- pandas
- numpy
"""

import logging
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Import from local utils
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Import from local data modules
from data.preprocessing import load_raw_data, parse_protocol_metadata

# Configure logging
logger = get_logger(__name__)


def load_filtered_data() -> pd.DataFrame:
    """
    Load the filtered data from the preprocessing step.

    Returns:
        pd.DataFrame: DataFrame containing SMILES and other filtered data.

    Raises:
        FileNotFoundError: If the filtered data file does not exist.
        ValueError: If the required columns are missing.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "filtered_data.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Filtered data file not found at {input_path}. "
                                "Please ensure T010 (preprocessing) has been completed.")

    df = pd.read_csv(input_path)

    required_columns = ['smiles', 'logPapp']
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")

    logger.info(f"Loaded {len(df)} filtered records from {input_path}")
    return df


def generate_conformers(smiles_list: List[str],
                        num_conformers: int = 50,
                        energy_window: float = 10.0) -> List[Dict[str, Any]]:
    """
    Generate 3D conformer ensembles for a list of SMILES strings.

    Implements FR-003:
    - Generates ensembles of size 50 (configurable).
    - Filters conformers within an energy window of 10 kcal/mol (configurable).

    Args:
        smiles_list (List[str]): List of SMILES strings.
        num_conformers (int): Number of conformers to generate per molecule.
        energy_window (float): Energy window in kcal/mol for filtering.

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing conformer data.
            Each dictionary has keys: 'smiles', 'mol' (RDKit Mol with conformers),
            'lowest_energy_conformer_id' (int), 'num_conformers' (int).
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        from rdkit import RDLogger
    except ImportError:
        raise ImportError("RDKit is required for conformer generation. "
                          "Please install it via `pip install rdkit`.")

    # Suppress RDKit warnings
    RDLogger.DisableLog('rdApp.*')

    results = []
    failed_molecules = 0

    for i, smiles in enumerate(smiles_list):
        if not smiles or pd.isna(smiles):
            failed_molecules += 1
            continue

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Invalid SMILES at index {i}: {smiles}")
            failed_molecules += 1
            continue

        # Add hydrogens
        mol = Chem.AddHs(mol)

        # Generate conformers
        # ETKDGv3 is generally more robust for drug-like molecules
        params = AllChem.ETKDGv3()
        params.randomSeed = 42 + i  # Ensure reproducibility
        params.maxAttempts = 200

        try:
            # Generate multiple conformers
            conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_conformers, params=params)

            if not conf_ids:
                logger.warning(f"No conformers generated for SMILES at index {i}: {smiles}")
                failed_molecules += 1
                continue

            # Optimize conformers (MMFF94)
            energies = []
            valid_conf_ids = []

            for cid in conf_ids:
                # Optimize geometry
                AllChem.MMFFOptimizeMolecule(mol, confId=cid)
                ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol), confId=cid)
                if ff is not None:
                    energy = ff.CalcEnergy()
                    energies.append(energy)
                    valid_conf_ids.append(cid)
                else:
                    # If MMFF fails, try UFF
                    try:
                        ff = AllChem.UFFGetMoleculeForceField(mol, confId=cid)
                        energy = ff.CalcEnergy()
                        energies.append(energy)
                        valid_conf_ids.append(cid)
                    except:
                        energies.append(float('inf'))
                        valid_conf_ids.append(cid)

            if not energies:
                logger.warning(f"Could not calculate energies for SMILES at index {i}: {smiles}")
                failed_molecules += 1
                continue

            # Find minimum energy
            min_energy = min(energies)

            # Filter conformers within energy window
            # Keep conformers where E - E_min <= energy_window
            filtered_indices = [
                idx for idx, e in enumerate(energies)
                if (e - min_energy) <= energy_window
            ]

            if not filtered_indices:
                # Should not happen if min_energy is in the list, but safety check
                filtered_indices = [energies.index(min_energy)]

            # Create a list of (energy, conf_id) for the filtered set
            filtered_confs = [
                (energies[idx], valid_conf_ids[idx]) for idx in filtered_indices
            ]
            # Sort by energy
            filtered_confs.sort(key=lambda x: x[0])

            # Store the lowest energy conformer ID
            lowest_energy_conf_id = filtered_confs[0][1]

            # Store results including the mol object with all conformers
            # We keep the mol object to avoid re-generation in the next step
            result_entry = {
                'smiles': smiles,
                'mol': mol,  # RDKit Mol object with all conformers attached
                'all_conformer_ids': valid_conf_ids,
                'all_energies': energies,
                'filtered_conformer_ids': [c[1] for c in filtered_confs],
                'filtered_energies': [c[0] for c in filtered_confs],
                'lowest_energy_conformer_id': lowest_energy_conf_id,
                'num_generated': len(valid_conf_ids),
                'num_filtered': len(filtered_confs)
            }
            results.append(result_entry)

        except Exception as e:
            logger.warning(f"Error processing SMILES at index {i}: {smiles}. Error: {e}")
            failed_molecules += 1
            continue

    logger.info(f"Conformer generation complete. "
                f"Success: {len(results)}, Failed: {failed_molecules}")
    return results


def save_conformers(conformer_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the generated conformer ensembles to a pickle file.

    Args:
        conformer_data (List[Dict[str, Any]]): List of conformer data dictionaries.
        output_path (Path): Path to save the pickle file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'wb') as f:
            pickle.dump(conformer_data, f)
        logger.info(f"Saved {len(conformer_data)} conformer ensembles to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save conformers to {output_path}: {e}")
        raise


def main():
    """
    Main entry point for the conformer generation script.
    """
    configure_root_logger()
    logger.info("Starting conformer generation (T013)...")

    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "conformers.pkl"

    # Load filtered data
    try:
        df = load_filtered_data()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load filtered data: {e}")
        sys.exit(1)

    smiles_list = df['smiles'].tolist()
    logger.info(f"Processing {len(smiles_list)} molecules...")

    # Generate conformers
    # FR-003: size = 50, energy window <= 10 kcal/mol
    conformer_data = generate_conformers(
        smiles_list=smiles_list,
        num_conformers=50,
        energy_window=10.0
    )

    if not conformer_data:
        logger.error("No conformers were generated. Check input data and logs.")
        sys.exit(1)

    # Save conformers
    save_conformers(conformer_data, output_path)

    # Invoke checksum utility
    from utils.checksum import write_checksums_to_pending
    checksum_file = project_root / "state" / "pending" / "checksums.yaml"
    try:
        # We need to call the function that writes to the pending file
        # The API surface shows `write_checksums_to_pending`
        write_checksums_to_pending(str(output_path), str(checksum_file))
        logger.info(f"Checksum written to {checksum_file}")
    except Exception as e:
        logger.warning(f"Could not generate checksum: {e}")

    logger.info("Conformer generation completed successfully.")


if __name__ == "__main__":
    main()