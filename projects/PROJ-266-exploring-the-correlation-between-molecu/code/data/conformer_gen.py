"""
Conformer Generation Module for Molecular Flexibility Analysis.

Implements FR-003: Generate 3D conformer ensembles for molecules in the filtered dataset.
Uses RDKit to generate conformers with an energy window constraint.
"""

import logging
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root
from utils.checksum import scan_and_register_data_files

# Configure logger
logger = get_logger(__name__)


def load_filtered_data() -> pd.DataFrame:
    """
    Load the filtered dataset from data/processed/filtered_data.csv.

    Returns:
        pd.DataFrame: DataFrame containing SMILES and logPapp columns.

    Raises:
        FileNotFoundError: If the filtered data file does not exist.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "filtered_data.csv"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered data file not found at {input_path}. "
            "Please ensure T010 (preprocessing) has been completed successfully."
        )

    df = pd.read_csv(input_path)
    required_cols = ['smiles', 'logPapp']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in filtered data: {missing_cols}. "
            f"Expected columns: {required_cols}"
        )

    logger.info(f"Loaded {len(df)} records from {input_path}")
    return df


def generate_conformers(smiles_list: List[str], 
                        n_conformers: int = 50, 
                        max_energy_window: float = 10.0) -> Dict[str, Any]:
    """
    Generate 3D conformer ensembles for a list of SMILES strings.

    Implements FR-003: Generate 3D conformer ensembles (size = 50, energy window ≤ 10 kcal/mol).

    Args:
        smiles_list: List of SMILES strings.
        n_conformers: Number of conformers to generate per molecule (default 50).
        max_energy_window: Maximum energy window in kcal/mol (default 10.0).

    Returns:
        Dict mapping molecule index to conformer data:
        {
            "index": {
                "smiles": str,
                "conformers": List[rdkit.Chem.Conformer],
                "energies": List[float],
                "n_generated": int,
                "success": bool
            }
        }

    Raises:
        ValueError: If any SMILES string is invalid.
    """
    results = {}
    failed_indices = []

    for idx, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning(f"Invalid SMILES at index {idx}: {smiles}")
                failed_indices.append(idx)
                continue

            # Add hydrogens
            mol = Chem.AddHs(mol)

            # Generate conformers using ETKDG
            params = AllChem.ETKDGv3()
            params.maxAttempts = 500
            params.useRandomCoords = False
            params.randomSeed = 42

            # Generate conformers
            conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=n_conformers, params=params)
            
            if len(conf_ids) == 0:
                logger.warning(f"Failed to generate conformers for SMILES at index {idx}")
                failed_indices.append(idx)
                continue

            # Optimize conformers with MMFF
            energies = []
            valid_conf_ids = []
            
            for conf_id in conf_ids:
                try:
                    ff = AllChem.MMFFGetMoleculeForceField(mol, AllChem.MMFFGetMoleculeProperties(mol), confId=conf_id)
                    if ff is not None:
                        ff.Minimize(maxIts=200)
                        energy = ff.CalcEnergy()
                        energies.append(energy)
                        valid_conf_ids.append(conf_id)
                    else:
                        logger.debug(f"MMFF optimization failed for conformer {conf_id} at index {idx}")
                except Exception as e:
                    logger.debug(f"Error optimizing conformer {conf_id} at index {idx}: {e}")

            if len(energies) == 0:
                logger.warning(f"No valid conformers after optimization for index {idx}")
                failed_indices.append(idx)
                continue

            # Filter by energy window
            min_energy = min(energies)
            filtered_conf_ids = []
            filtered_energies = []
            
            for conf_id, energy in zip(valid_conf_ids, energies):
                if energy - min_energy <= max_energy_window:
                    filtered_conf_ids.append(conf_id)
                    filtered_energies.append(energy)

            # Sort by energy
            sorted_indices = np.argsort(filtered_energies)
            sorted_conf_ids = [filtered_conf_ids[i] for i in sorted_indices]
            sorted_energies = [filtered_energies[i] for i in sorted_indices]

            # Store result
            results[idx] = {
                "smiles": smiles,
                "conformer_ids": sorted_conf_ids,
                "energies": sorted_energies,
                "n_generated": len(sorted_conf_ids),
                "success": True
            }

            if idx % 100 == 0:
                logger.info(f"Processed {idx}/{len(smiles_list)} molecules")

        except Exception as e:
            logger.error(f"Error processing SMILES at index {idx}: {e}")
            failed_indices.append(idx)

    logger.info(f"Conformer generation complete. Success: {len(results)}/{len(smiles_list)}")
    if failed_indices:
        logger.warning(f"Failed to generate conformers for {len(failed_indices)} molecules: {failed_indices[:10]}...")

    return results


def save_conformers(conformer_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save conformer ensembles to a pickle file.

    Args:
        conformer_data: Dictionary of conformer data from generate_conformers.
        output_path: Path to save the pickle file.
    """
    # Convert to a serializable format
    serializable_data = {}
    
    for idx, data in conformer_data.items():
        if data["success"]:
            mol = Chem.MolFromSmiles(data["smiles"])
            mol = Chem.AddHs(mol)
            
            # Extract conformer coordinates
            conformers_list = []
            for conf_id in data["conformer_ids"]:
                conf = mol.GetConformer(conf_id)
                coords = conf.GetPositions()
                conformers_list.append({
                    "id": conf_id,
                    "energy": data["energies"][data["conformer_ids"].index(conf_id)],
                    "coords": coords.tolist()
                })
            
            serializable_data[idx] = {
                "smiles": data["smiles"],
                "conformers": conformers_list,
                "n_conformers": len(conformers_list),
                "success": True
            }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        pickle.dump(serializable_data, f)
    
    logger.info(f"Saved {len(serializable_data)} conformer ensembles to {output_path}")


def main():
    """Main entry point for conformer generation."""
    configure_root_logger()
    logger.info("Starting conformer generation (T013)")

    try:
        # Load filtered data
        df = load_filtered_data()
        smiles_list = df['smiles'].tolist()
        
        logger.info(f"Processing {len(smiles_list)} molecules")

        # Generate conformers
        conformer_data = generate_conformers(
            smiles_list, 
            n_conformers=50, 
            max_energy_window=10.0
        )

        # Count successes
        success_count = sum(1 for d in conformer_data.values() if d["success"])
        logger.info(f"Successfully generated conformers for {success_count}/{len(smiles_list)} molecules")

        # Save results
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "conformers.pkl"
        save_conformers(conformer_data, output_path)

        # Verify output exists
        if not output_path.exists():
            raise RuntimeError(f"Output file {output_path} was not created")

        logger.info(f"Conformer generation completed. Output: {output_path}")
        
        # Invoke checksum utility
        scan_and_register_data_files()
        logger.info("Checksum registered for output file")

    except Exception as e:
        logger.error(f"Conformer generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()