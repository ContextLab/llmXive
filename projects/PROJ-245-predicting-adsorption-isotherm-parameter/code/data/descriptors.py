"""
Descriptor calculation and management module for adsorption isotherm prediction.

This module provides functions to calculate molecular descriptors, handle errors,
and manage descriptor logs.
"""

import os
import sys
import math
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdchem

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PI = math.pi

class MissingConsensusDescriptorError(Exception):
    """Exception raised when a consensus descriptor cannot be calculated."""
    pass

def ensure_directories(path: Path) -> None:
    """Ensure that the directory for the given path exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def log_missing_entry(log_path: Path, entry_id: str, descriptor_type: str, reason: str) -> None:
    """Log a missing descriptor entry to a JSON file."""
    ensure_directories(log_path)
    
    # Load existing logs if they exist
    if log_path.exists():
        with open(log_path, 'r') as f:
            logs = json.load(f)
    else:
        logs = []
    
    # Append new entry
    logs.append({
        'entry_id': entry_id,
        'descriptor_type': descriptor_type,
        'reason': reason,
        'timestamp': pd.Timestamp.now().isoformat()
    })
    
    # Write back to file
    with open(log_path, 'w') as f:
        json.dump(logs, f, indent=2)

def calculate_kinetic_diameter(mol: Union[Chem.Mol, str], entry_id: str) -> Optional[float]:
    """
    Calculate kinetic diameter using RDKit.
    
    Args:
        mol: RDKit molecule object or SMILES string
        entry_id: Unique identifier for the entry
        
    Returns:
        Kinetic diameter in Angstroms, or None if calculation fails
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError(f"Could not parse SMILES for entry {entry_id}")
        
        # Use RDKit's calculation of topological polar surface area
        tpsa = Descriptors.TPSA(mol)
        
        # Calculate kinetic diameter using the formula: d = sqrt(4 * TPSA / PI)
        # This is a simplified approximation based on molecular surface area
        kinetic_diameter = math.sqrt(4 * tpsa / PI)
        
        return kinetic_diameter
        
    except Exception as e:
        logger.warning(f"Failed to calculate kinetic diameter for entry {entry_id}: {str(e)}")
        return None

def calculate_lj_epsilon(row: pd.Series, entry_id: str) -> Optional[float]:
    """
    Calculate Lennard-Jones energy parameter.
    
    Args:
        row: DataFrame row containing critical pressure and volume
        entry_id: Unique identifier for the entry
        
    Returns:
        Lennard-Jones epsilon parameter, or None if calculation fails
    """
    try:
        # Extract critical pressure (Pc) and critical volume (Vc)
        pc = row.get('critical_pressure')
        vc = row.get('critical_volume')
        
        if pd.isna(pc) or pd.isna(vc):
            log_missing_entry(
                Path('data/validation/exclusion_log.json'),
                entry_id,
                'lj_epsilon',
                'Missing critical pressure or volume'
            )
            return None
        
        # Constants
        R = 0.08206  # Gas constant in L·atm/(mol·K)
        
        # Estimate critical temperature: Tc = 1.5 * (Pc * Vc / R)
        tc = 1.5 * (pc * vc / R)
        
        # Calculate epsilon: epsilon = 0.75 * Tc
        epsilon = 0.75 * tc
        
        return epsilon
        
    except Exception as e:
        logger.warning(f"Failed to calculate LJ epsilon for entry {entry_id}: {str(e)}")
        log_missing_entry(
            Path('data/validation/exclusion_log.json'),
            entry_id,
            'lj_epsilon',
            str(e)
        )
        return None

def calculate_quadrupole_moment(mol: Union[Chem.Mol, str], entry_id: str) -> Optional[float]:
    """
    Calculate quadrupole moment using psi4.
    
    Args:
        mol: RDKit molecule object or SMILES string
        entry_id: Unique identifier for the entry
        
    Returns:
        Quadrupole moment component, or None if calculation fails
    """
    try:
        # Check if psi4 is available
        try:
            import psi4
        except ImportError:
            logger.warning(f"psi4 not available for entry {entry_id}")
            return None
        
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError(f"Could not parse SMILES for entry {entry_id}")
        
        # Generate 3D coordinates if not present
        mol = Chem.AddHs(mol)
        Chem.EmbedMolecule(mol, randomSeed=42)
        Chem.MMFFOptimizeMolecule(mol)
        
        # Get atomic coordinates and symbols
        coords = mol.GetConformer().GetPositions()
        symbols = [atom.GetSymbol() for atom in mol.GetAtoms()]
        
        # Create psi4 molecule object
        psi4_mol = psi4.geometry("""
        {0}
        """.format('\n'.join([f"{sym} {x} {y} {z}" for sym, (x, y, z) in zip(symbols, coords)])))
        
        # Set calculation parameters
        psi4.set_options({
            'basis': 'def2-svp',
            'df_scf': True
        })
        
        # Run calculation
        energy, wfn = psi4.energy('b3lyp', return_wfn=True, molecule=psi4_mol)
        
        # Extract quadrupole moment
        quadrupole = wfn.properties()['quadrupole_moment']
        
        # Return the xx component (or first component)
        return quadrupole[0, 0]
        
    except Exception as e:
        logger.warning(f"Failed to calculate quadrupole moment for entry {entry_id}: {str(e)}")
        log_missing_entry(
            Path('data/validation/missing_descriptors_quadrupole.json'),
            entry_id,
            'quadrupole_moment',
            str(e)
        )
        return None

def calculate_polarizability(mol: Union[Chem.Mol, str], entry_id: str) -> Optional[float]:
    """
    Calculate polarizability using RDKit.
    
    Args:
        mol: RDKit molecule object or SMILES string
        entry_id: Unique identifier for the entry
        
    Returns:
        Polarizability value, or None if calculation fails
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError(f"Could not parse SMILES for entry {entry_id}")
        
        # Use RDKit's polarizability calculation
        polarizability = rdMolDescriptors.CalcPolarizability(mol)
        
        return polarizability
        
    except Exception as e:
        logger.warning(f"Failed to calculate polarizability for entry {entry_id}: {str(e)}")
        log_missing_entry(
            Path('data/validation/missing_descriptors_polarizability.json'),
            entry_id,
            'polarizability',
            str(e)
        )
        return None

def calculate_vdw_volume(mol: Union[Chem.Mol, str], entry_id: str) -> Optional[float]:
    """
    Calculate van der Waals volume using RDKit.
    
    Args:
        mol: RDKit molecule object or SMILES string
        entry_id: Unique identifier for the entry
        
    Returns:
        van der Waals volume, or None if calculation fails
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError(f"Could not parse SMILES for entry {entry_id}")
        
        # Use RDKit's van der Waals volume calculation
        vdw_volume = rdMolDescriptors.CalcMolVolume(mol)
        
        return vdw_volume
        
    except Exception as e:
        logger.warning(f"Failed to calculate VdW volume for entry {entry_id}: {str(e)}")
        log_missing_entry(
            Path('data/validation/missing_descriptors_vdw.json'),
            entry_id,
            'vdw_volume',
            str(e)
        )
        return None

def generate_descriptor_hash(descriptors: Dict[str, float]) -> str:
    """
    Generate a hash of sorted descriptor values.
    
    Args:
        descriptors: Dictionary of descriptor name to value
        
    Returns:
        Hash string
    """
    # Sort descriptors by name and create a tuple of values
    sorted_values = tuple(sorted(descriptors.items()))
    
    # Create hash
    hash_obj = hashlib.md5(str(sorted_values).encode())
    return hash_obj.hexdigest()

def calculate_descriptors_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules.
    
    Args:
        df: DataFrame with molecular data
        
    Returns:
        DataFrame with calculated descriptors
    """
    # Initialize descriptor columns
    descriptor_cols = [
        'kinetic_diameter',
        'lj_epsilon',
        'quadrupole_moment',
        'polarizability',
        'vdw_volume'
    ]
    
    for col in descriptor_cols:
        df[col] = np.nan
    
    # Calculate descriptors for each row
    for idx, row in df.iterrows():
        entry_id = row.get('material_id', f'row_{idx}')
        mol = row.get('mol')
        
        if mol is None:
            continue
        
        # Calculate kinetic diameter
        df.at[idx, 'kinetic_diameter'] = calculate_kinetic_diameter(mol, entry_id)
        
        # Calculate LJ epsilon
        df.at[idx, 'lj_epsilon'] = calculate_lj_epsilon(row, entry_id)
        
        # Calculate quadrupole moment
        df.at[idx, 'quadrupole_moment'] = calculate_quadrupole_moment(mol, entry_id)
        
        # Calculate polarizability
        df.at[idx, 'polarizability'] = calculate_polarizability(mol, entry_id)
        
        # Calculate VdW volume
        df.at[idx, 'vdw_volume'] = calculate_vdw_volume(mol, entry_id)
    
    return df

def cache_descriptors(df: pd.DataFrame, cache_path: Path) -> None:
    """
    Cache calculated descriptors to a Parquet file.
    
    Args:
        df: DataFrame with descriptors
        cache_path: Path to save the cache
    """
    ensure_directories(cache_path)
    df.to_parquet(cache_path, index=False)
    logger.info(f"Descriptors cached to {cache_path}")

def load_cached_descriptors(cache_path: Path) -> pd.DataFrame:
    """
    Load cached descriptors from a Parquet file.
    
    Args:
        cache_path: Path to the cache file
        
    Returns:
        DataFrame with descriptors
    """
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_path}")
    
    return pd.read_parquet(cache_path)

def merge_descriptor_logs() -> None:
    """
    Merge missing descriptor logs into a single report.
    
    This function reads individual missing descriptor logs and combines them
    into a comprehensive report.
    """
    # Define log files
    log_files = [
        'data/validation/missing_descriptors_kinetic.json',
        'data/validation/missing_descriptors_lj.json',
        'data/validation/missing_descriptors_quadrupole.json',
        'data/validation/missing_descriptors_polarizability.json',
        'data/validation/missing_descriptors_vdw.json'
    ]
    
    # Initialize merged report
    merged_report = {
        'summary': {
            'total_missing_entries': 0,
            'missing_by_type': {}
        },
        'entries': []
    }
    
    # Process each log file
    for log_file in log_files:
        log_path = Path(log_file)
        
        if not log_path.exists():
            logger.info(f"No missing descriptors log found at {log_file}")
            continue
        
        try:
            with open(log_path, 'r') as f:
                entries = json.load(f)
            
            # Add entries to merged report
            for entry in entries:
                entry['source_file'] = log_file
                merged_report['entries'].append(entry)
            
            # Update summary
            descriptor_type = Path(log_file).stem.replace('missing_descriptors_', '')
            merged_report['summary']['missing_by_type'][descriptor_type] = len(entries)
            merged_report['summary']['total_missing_entries'] += len(entries)
            
            logger.info(f"Processed {len(entries)} entries from {log_file}")
            
        except Exception as e:
            logger.error(f"Error processing {log_file}: {str(e)}")
    
    # Write merged report
    report_path = Path('data/validation/missing_descriptors_report.json')
    ensure_directories(report_path)
    
    with open(report_path, 'w') as f:
        json.dump(merged_report, f, indent=2)
    
    logger.info(f"Merged descriptor report saved to {report_path}")

def main() -> None:
    """Main function to run descriptor calculations and logging."""
    logger.info("Starting descriptor calculation and logging pipeline")
    
    # Merge descriptor logs
    merge_descriptor_logs()
    
    logger.info("Descriptor calculation and logging pipeline completed")

if __name__ == '__main__':
    main()