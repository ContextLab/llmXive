import os
import sys
import json
import logging
import hashlib
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors, rdDistGeom, rdForceFieldHelpers
from rdkit import RDLogger

# Project imports based on API surface
from code.config import MAX_MOLECULES, RANDOM_SEED
from code.utils.logging import get_logger, log_errors
from code.utils.validators import count_atoms

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants for conformer generation (default if params file missing)
DEFAULT_CONFORMER_PARAMS = {
    "numThreads": 0,
    "maxAttempts": 20,
    "energyMinimizationSteps": 200,
    "random_seed": RANDOM_SEED
}

def load_conformer_params(params_path: str = "data/processed/conformer_params.json") -> Dict[str, Any]:
    """Load conformer generation parameters from JSON file."""
    path = Path(params_path)
    if not path.exists():
        logger.warning(f"Conformer params file not found at {params_path}. Using defaults.")
        return DEFAULT_CONFORMER_PARAMS
    
    with open(path, 'r') as f:
        params = json.load(f)
    
    # Ensure all required keys exist
    for key in DEFAULT_CONFORMER_PARAMS:
        if key not in params:
            logger.warning(f"Missing key '{key}' in conformer params. Using default.")
            params[key] = DEFAULT_CONFORMER_PARAMS[key]
    
    return params

def save_conformer_params(params: Dict[str, Any], params_path: str = "data/processed/conformer_params.json") -> None:
    """Save conformer generation parameters to JSON file."""
    path = Path(params_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Saved conformer params to {params_path}")

def map_rdkit_exception_to_reason(exception: Exception) -> str:
    """Map RDKit exceptions to standardized failure reasons."""
    exc_type = type(exception).__name__
    msg = str(exception).lower()
    
    if 'valence' in msg or exc_type == 'ValueError':
        return 'INVALID_VALENCE'
    elif 'etkdg' in msg or exc_type == 'RuntimeError':
        return 'ETKDG_FAIL'
    elif 'minimize' in msg or 'minimization' in msg:
        return 'MINIMIZATION_FAIL'
    else:
        return 'CONFORMER_GENERATION_FAIL'

def generate_conformer_for_molecule(mol: Chem.Mol, params: Dict[str, Any]) -> Optional[Chem.Mol]:
    """Generate a 3D conformer for a molecule using ETKDG."""
    try:
        # Embed conformer
        pid = rdDistGeom.EmbedMolecule(
            mol,
            rdDistGeom.ETKDGv3(),
            useRandomCoords=True,
            randomSeed=params['random_seed'],
            numThreads=params['numThreads']
        )
        
        if pid == -1:
            raise RuntimeError("ETKDG embedding failed")
        
        # Minimize
        ff = rdForceFieldHelpers.MMFFGetMoleculeForceField(
            mol,
            rdForceFieldHelpers.MMFFGetMoleculeProperties(mol)
        )
        
        if ff is None:
            raise RuntimeError("MMFF force field generation failed")
        
        status = ff.Minimize(maxIts=params['energyMinimizationSteps'])
        
        if status != 0:
            raise RuntimeError("Energy minimization failed")
        
        return mol
    except Exception as e:
        logger.debug(f"Conformer generation failed: {e}")
        return None

def calculate_sasa(mol: Chem.Mol) -> float:
    """Calculate Solvent Accessible Surface Area (SASA) using RDKit."""
    try:
        # Ensure conformer exists
        if mol.GetNumConformers() == 0:
            raise ValueError("No conformer found in molecule")
        
        # Calculate SASA
        sasa = rdMolDescriptors.CalcSASA(mol)
        return float(sasa)
    except Exception as e:
        logger.error(f"SASA calculation failed: {e}")
        raise

def calculate_3d_descriptors(mol: Chem.Mol) -> Dict[str, float]:
    """Calculate 3D geometric descriptors from a conformer."""
    try:
        if mol.GetNumConformers() == 0:
            raise ValueError("No conformer found in molecule")
        
        conf = mol.GetConformer()
        coords = np.array(conf.GetPositions())
        
        # Radius of gyration
        center_of_mass = np.mean(coords, axis=0)
        r_gyr_sq = np.mean(np.sum((coords - center_of_mass) ** 2, axis=1))
        radius_of_gyration = float(np.sqrt(r_gyr_sq))
        
        # Principal moments of inertia
        # Calculate inertia tensor
        mass = np.ones(len(coords))  # Equal mass for geometric calculation
        com = np.average(coords, axis=0, weights=mass)
        
        inertia_tensor = np.zeros((3, 3))
        for i in range(3):
            for j in range(3):
                inertia_tensor[i, j] = np.sum(
                    mass * (np.sum((coords - com) ** 2, axis=1) * (i == j) - (coords[:, i] - com[i]) * (coords[:, j] - com[j]))
                )
        
        # Eigenvalues of inertia tensor
        eigenvalues = np.linalg.eigvalsh(inertia_tensor)
        eigenvalues = eigenvalues[eigenvalues > 0]  # Filter numerical noise
        
        if len(eigenvalues) < 3:
            # Pad with zeros if needed
            eigenvalues = np.pad(eigenvalues, (0, 3 - len(eigenvalues)), mode='constant')
        
        principal_moments = sorted(eigenvalues, reverse=True)
        
        # SASA components (approximated by atom contributions)
        # RDKit doesn't provide per-atom SASA directly, so we use a proxy
        # Calculate surface area contributions based on atom radii
        atom_radii = []
        for atom in mol.GetAtoms():
            atomic_num = atom.GetAtomicNum()
            # Approximate van der Waals radii
            if atomic_num == 1:  # H
                atom_radii.append(1.2)
            elif atomic_num == 6:  # C
                atom_radii.append(1.7)
            elif atomic_num == 7:  # N
                atom_radii.append(1.55)
            elif atomic_num == 8:  # O
                atom_radii.append(1.52)
            elif atomic_num == 16:  # S
                atom_radii.append(1.8)
            else:
                atom_radii.append(1.7)  # Default
        
        # Calculate component areas (simplified)
        sasa_components = [float(r ** 2 * 4 * np.pi) for r in atom_radii]
        
        return {
            'radius_of_gyration': radius_of_gyration,
            'principal_moment_1': float(principal_moments[0]),
            'principal_moment_2': float(principal_moments[1]),
            'principal_moment_3': float(principal_moments[2]),
            'sasa_components': sasa_components
        }
    except Exception as e:
        logger.error(f"3D descriptor calculation failed: {e}")
        raise

def process_molecule_for_descriptors(mol: Chem.Mol, smiles: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single molecule to calculate SASA and 3D descriptors."""
    try:
        # Calculate SASA
        sasa = calculate_sasa(mol)
        
        # Calculate 3D descriptors
        descriptors = calculate_3d_descriptors(mol)
        
        return {
            'smiles': smiles,
            'surface_area': sasa,
            'radius_of_gyration': descriptors['radius_of_gyration'],
            'principal_moment_1': descriptors['principal_moment_1'],
            'principal_moment_2': descriptors['principal_moment_2'],
            'principal_moment_3': descriptors['principal_moment_3'],
            'sasa_components': descriptors['sasa_components']
        }
    except Exception as e:
        logger.error(f"Failed to process molecule {smiles[:20]}...: {e}")
        return None

def process_conformers_chunk(chunk: pd.DataFrame, params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Process a chunk of conformers and calculate descriptors."""
    results = []
    failures = []
    
    for idx, row in chunk.iterrows():
        smiles = row['smiles']
        try:
            # Deserialize molecule from saved conformer data
            # Assuming the conformer data is stored as a serialized format
            # For this implementation, we assume the molecule is already in 3D form
            # If it's stored as coordinates, we need to reconstruct the molecule
            
            # Check if 'conformer_coords' or similar exists
            if 'conformer_coords' in row:
                # Reconstruct molecule from coordinates
                # This is a simplified reconstruction
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    raise ValueError("Invalid SMILES")
                
                # Add conformer
                conf = Chem.Conformer(mol.GetNumAtoms())
                coords = json.loads(row['conformer_coords'])
                for i, coord in enumerate(coords):
                    conf.SetAtomPosition(i, (coord[0], coord[1], coord[2]))
                mol.AddConformer(conf)
            else:
                # Assume molecule is already in 3D form in the dataframe
                # This would require a different serialization format
                raise ValueError("Conformer coordinates not found")
            
            # Process molecule
            result = process_molecule_for_descriptors(mol, smiles, params)
            if result:
                results.append(result)
            else:
                failures.append({
                    'smiles': smiles,
                    'failure_reason': 'PROCESSING_FAIL',
                    'atom_count': count_atoms(smiles),
                    **params
                })
                
        except Exception as e:
            failures.append({
                'smiles': smiles,
                'failure_reason': map_rdkit_exception_to_reason(e),
                'atom_count': count_atoms(smiles),
                **params
            })
            logger.warning(f"Failed to process molecule {smiles[:20]}...: {e}")
    
    return results, failures

def main():
    """Main function to calculate SASA and 3D descriptors."""
    logger.info("Starting SASA and 3D descriptor calculation (T015b)")
    
    # Load conformer params
    params_path = "data/processed/conformer_params.json"
    params = load_conformer_params(params_path)
    logger.info(f"Using conformer params: {params}")
    
    # Load conformers from T015a
    conformers_path = "data/processed/conformers.parquet"
    if not os.path.exists(conformers_path):
        raise FileNotFoundError(f"Conformers file not found at {conformers_path}. Run T015a first.")
    
    logger.info(f"Loading conformers from {conformers_path}")
    conformers_df = pd.read_parquet(conformers_path)
    logger.info(f"Loaded {len(conformers_df)} conformers")
    
    # Process in chunks to manage memory
    chunk_size = 100
    all_results = []
    all_failures = []
    
    for i in range(0, len(conformers_df), chunk_size):
        chunk = conformers_df.iloc[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} molecules)")
        
        results, failures = process_conformers_chunk(chunk, params)
        all_results.extend(results)
        all_failures.extend(failures)
        
        logger.info(f"Chunk {i//chunk_size + 1}: {len(results)} success, {len(failures)} failures")
    
    # Create output dataframe
    if not all_results:
        raise RuntimeError("No successful descriptor calculations. Check input data.")
    
    output_df = pd.DataFrame(all_results)
    
    # Ensure required columns exist
    required_cols = ['smiles', 'surface_area', 'radius_of_gyration', 
                    'principal_moment_1', 'principal_moment_2', 'principal_moment_3',
                    'sasa_components']
    for col in required_cols:
        if col not in output_df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Save to parquet
    output_path = "data/processed/descriptors.parquet"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    output_df.to_parquet(output_path, index=False)
    logger.info(f"Saved descriptors to {output_path}")
    
    # Save failure report if any
    if all_failures:
        failure_df = pd.DataFrame(all_failures)
        failure_path = "data/processed/descriptor_failures.csv"
        failure_df.to_csv(failure_path, index=False)
        logger.info(f"Saved {len(all_failures)} failures to {failure_path}")
    
    # Summary
    logger.info(f"Successfully processed {len(all_results)} molecules")
    logger.info(f"Failed to process {len(all_failures)} molecules")
    logger.info(f"Success rate: {len(all_results) / len(conformers_df) * 100:.2f}%")
    
    return output_path

if __name__ == "__main__":
    main()