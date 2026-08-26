"""
Conformer generation module for molecular flexibility analysis.

This module implements the generation of 3D conformer ensembles for a list of
SMILES strings using RDKit. It adheres to the requirements of User Story 2,
specifically Task T013.

Traceability:
- FR-003: Generate 3D conformer ensembles for each molecule.
"""
import logging
import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolTransforms
from rdkit import RDLogger

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

# Import project utilities
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root, get_data_path

logger = get_logger(__name__)

def generate_conformers(smiles_list: List[str], 
                        num_conformers: int = 50, 
                        energy_window: float = 10.0) -> Dict[str, Any]:
    """
    Generate 3D conformer ensembles for a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        num_conformers: Number of conformers to generate per molecule (default 50).
        energy_window: Energy window in kcal/mol to filter conformers (default 10.0).

    Returns:
        A dictionary containing:
        - 'conformers': List of dicts with 'smiles', 'conformer_id', 'energy', 'coords'.
        - 'lowest_energy_conformer_id': ID of the lowest energy conformer for each molecule.
        - 'success_rate': Fraction of molecules for which conformers were successfully generated.
        - 'failed_smiles': List of SMILES that failed generation.
    """
    conformers_data = []
    failed_smiles = []
    success_count = 0

    for i, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                logger.warning(f"Failed to parse SMILES at index {i}: {smiles}")
                failed_smiles.append(smiles)
                continue

            # Add hydrogens for better geometry
            mol = Chem.AddHs(mol)

            # Embed multiple conformers
            params = AllChem.ETKDGv3()
            params.numThreads = 1
            params.maxAttempts = 500
            params.useRandomCoords = True
            
            # Generate conformers
            conf_ids = AllChem.EmbedMultipleConfs(mol, numConfs=num_conformers, params=params)
            
            if not conf_ids:
                logger.warning(f"No conformers generated for SMILES at index {i}: {smiles}")
                failed_smiles.append(smiles)
                continue

            # Optimize geometries
            energies = []
            for conf_id in conf_ids:
                result = AllChem.UFFOptimizeMolecule(mol, confId=conf_id, maxIters=200)
                if result == 0:
                  energy = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id).CalcEnergy()
                  energies.append((conf_id, energy))
                else:
                  # Optimization failed, but we still have the initial geometry
                  # Try to get energy anyway
                  try:
                      energy = AllChem.UFFGetMoleculeForceField(mol, confId=conf_id).CalcEnergy()
                      energies.append((conf_id, energy))
                  except:
                      energies.append((conf_id, float('inf')))

            if not energies:
                failed_smiles.append(smiles)
                continue

            # Sort by energy
            energies.sort(key=lambda x: x[1])

            # Filter by energy window
            lowest_energy = energies[0][1]
            filtered_confs = [
                (cid, e) for cid, e in energies 
                if (e - lowest_energy) <= energy_window
            ]

            # If no conformers within window, keep the lowest energy one
            if not filtered_confs:
                filtered_confs = [energies[0]]

            # Extract coordinates for filtered conformers
            for conf_id, energy in filtered_confs:
                conf = mol.GetConformer(conf_id)
                coords = []
                for atom_idx in range(mol.GetNumAtoms()):
                    pos = conf.GetAtomPosition(atom_idx)
                    coords.append([pos.x, pos.y, pos.z])
                
                conformers_data.append({
                    'smiles': smiles,
                    'conformer_id': conf_id,
                    'energy': energy,
                    'coords': coords,
                    'num_atoms': mol.GetNumAtoms()
                })

            success_count += 1

        except Exception as e:
            logger.error(f"Error processing SMILES at index {i} ({smiles}): {str(e)}")
            failed_smiles.append(smiles)

    total_processed = len(smiles_list)
    success_rate = success_count / total_processed if total_processed > 0 else 0.0

    # Identify lowest energy conformer for each unique SMILES
    lowest_energy_map = {}
    for item in conformers_data:
        smiles = item['smiles']
        energy = item['energy']
        conf_id = item['conformer_id']
        
        if smiles not in lowest_energy_map or energy < lowest_energy_map[smiles]['energy']:
            lowest_energy_map[smiles] = {
                'conformer_id': conf_id,
                'energy': energy
            }

    return {
        'conformers': conformers_data,
        'lowest_energy_conformer_id': lowest_energy_map,
        'success_rate': success_rate,
        'failed_smiles': failed_smiles,
        'total_processed': total_processed,
        'total_success': success_count
    }

def save_conformers(conformers_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save conformer data to a pickle file.

    Args:
        conformers_data: Dictionary returned by generate_conformers.
        output_path: Path to save the pickle file.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(conformers_data, f)
    logger.info(f"Conformers saved to {output_path}")

def load_filtered_data() -> pd.DataFrame:
    """
    Load filtered data from the preprocessing step.

    Returns:
        DataFrame with SMILES and logPapp values.
    """
    data_path = get_data_path()
    input_file = data_path / 'processed' / 'filtered_data.csv'
    
    if not input_file.exists():
        raise FileNotFoundError(f"Filtered data file not found: {input_file}")
    
    df = pd.read_csv(input_file)
    return df

def main() -> None:
    """
    Main entry point for conformer generation.
    
    Reads filtered data, generates conformers, and saves the output.
    """
    configure_root_logger()
    
    try:
        # Load filtered data
        logger.info("Loading filtered data...")
        df = load_filtered_data()
        
        if 'smiles' not in df.columns:
            raise ValueError("Input data must contain 'smiles' column")
        
        smiles_list = df['smiles'].dropna().unique().tolist()
        logger.info(f"Processing {len(smiles_list)} unique molecules...")
        
        # Generate conformers
        logger.info("Generating conformers...")
        result = generate_conformers(
            smiles_list, 
            num_conformers=50, 
            energy_window=10.0
        )
        
        # Log results
        logger.info(f"Conformer generation complete:")
        logger.info(f"  - Total molecules processed: {result['total_processed']}")
        logger.info(f"  - Successful: {result['total_success']}")
        logger.info(f"  - Failed: {len(result['failed_smiles'])}")
        logger.info(f"  - Success rate: {result['success_rate']:.2%}")
        
        if result['failed_smiles']:
            logger.warning(f"Failed SMILES: {result['failed_smiles'][:5]}...")
        
        # Save output
        output_dir = get_data_path() / 'processed'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / 'conformers.pkl'
        
        save_conformers(result, output_file)
        
        # Invoke checksum utility
        from utils.checksum import write_checksums_to_pending
        checksums_file = write_checksums_to_pending(output_file)
        logger.info(f"Checksum written to {checksums_file}")
        
        logger.info("Conformer generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Conformer generation failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
