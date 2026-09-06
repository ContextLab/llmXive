"""
Descriptor calculation and management module for adsorption isotherm prediction.
Implements calculation of molecular descriptors and management of missing data logs.
"""
import os
import sys
import math
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdchem
from rdkit import RDLogger

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MissingConsensusDescriptorError(Exception):
    """Custom exception for missing descriptor calculations."""
    pass

def ensure_directories(base_path: str = "data") -> None:
    """Ensure required directories exist."""
    dirs = [
        os.path.join(base_path, "processed"),
        os.path.join(base_path, "validation"),
        os.path.join(base_path, "results")
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def log_missing_entry(log_file: str, entry: Dict[str, Any]) -> None:
    """Append a missing entry to a JSON log file."""
    ensure_directories()
    log_path = Path(log_file)
    
    # Load existing entries if file exists
    entries = []
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                entries = json.load(f)
        except (json.JSONDecodeError, IOError):
            entries = []
    
    entries.append(entry)
    
    with open(log_path, 'w') as f:
        json.dump(entries, f, indent=2)

def calculate_kinetic_diameter(mol: Union[str, Chem.Mol]) -> float:
    """
    Calculate kinetic diameter using RDKit.
    
    Args:
        mol: RDKit Mol object or SMILES string.
        
    Returns:
        Kinetic diameter in Angstroms.
        
    Raises:
        MissingConsensusDescriptorError: If calculation fails.
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError("Invalid SMILES string")
        
        # Calculate Topological Polar Surface Area (TPSA)
        tpsa = Descriptors.TPSA(mol)
        
        # Estimate kinetic diameter using the formula: d = sqrt(4 * TPSA / PI)
        # This is an approximation based on the relationship between polar surface area and molecular size
        kinetic_diameter = math.sqrt(4 * tpsa / math.pi)
        
        return float(kinetic_diameter)
    except Exception as e:
        raise MissingConsensusDescriptorError(f"Failed to calculate kinetic diameter: {str(e)}")

def calculate_lj_epsilon(df: pd.DataFrame, index: int) -> float:
    """
    Calculate Lennard-Jones energy parameter.
    
    Args:
        df: DataFrame containing critical pressure and volume.
        index: Row index to process.
        
    Returns:
        LJ epsilon parameter in Kelvin.
        
    Raises:
        MissingConsensusDescriptorError: If required data is missing.
    """
    try:
        row = df.iloc[index]
        
        # Extract critical pressure (Pc) and critical volume (Vc)
        # Assuming columns exist after imputation
        if 'critical_pressure' not in row or 'critical_volume' not in row:
            raise MissingConsensusDescriptorError("Missing critical_pressure or critical_volume")
        
        pc = row['critical_pressure']
        vc = row['critical_volume']
        
        if pd.isna(pc) or pd.isna(vc):
            raise MissingConsensusDescriptorError("NaN values in critical_pressure or critical_volume")
        
        # Gas constant in appropriate units
        R = 8.314  # J/(mol*K)
        
        # Estimate Tc using Tc = 1.5 * (Pc * Vc / R)
        # Note: Units need to be consistent. Assuming Pc in Pa, Vc in m3/mol
        # If units are different, conversion factors would be needed
        tc = 1.5 * (pc * vc / R)
        
        # Calculate epsilon = 0.75 * Tc
        epsilon = 0.75 * tc
        
        return float(epsilon)
    except Exception as e:
        raise MissingConsensusDescriptorError(f"Failed to calculate LJ epsilon: {str(e)}")

def calculate_quadrupole_moment(mol: Union[str, Chem.Mol], coordinates: Optional[np.ndarray] = None) -> float:
    """
    Calculate quadrupole moment using psi4.
    
    Args:
        mol: RDKit Mol object or SMILES string.
        coordinates: Optional 3D coordinates array.
        
    Returns:
        Quadrupole moment component (Qxx).
        
    Raises:
        MissingConsensusDescriptorError: If calculation fails.
    """
    try:
        # This is a placeholder for psi4 calculation
        # In a real implementation, psi4 would be called here
        # For now, we return a placeholder value or raise an error
        # since psi4 is not available in all environments
        
        # If coordinates are provided, we could attempt a calculation
        if coordinates is not None:
            # Placeholder: In real implementation, call psi4
            # For now, raise error indicating psi4 is required
            raise MissingConsensusDescriptorError("psi4 calculation not implemented in this environment")
        
        # If no coordinates, try to embed 3D structure
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError("Invalid SMILES string")
        
        # Generate 3D coordinates if not provided
        if coordinates is None:
            mol_3d = Chem.AddHs(mol)
            if not rdchem.EmbedMolecule(mol_3d):
                raise MissingConsensusDescriptorError("Failed to generate 3D coordinates")
            coordinates = np.array(mol_3d.GetConformer().GetPositions())
        
        # Placeholder for psi4 calculation
        # In real implementation:
        # import psi4
        # psi4.set_options({'basis': 'def2-svp', 'scf_type': 'df'})
        # energy, wfn = psi4.energy('b3lyp', return_wfn=True)
        # quadrupole = wfn.properties()['quadrupole_moment']
        # return quadrupole[0, 0]
        
        raise MissingConsensusDescriptorError("psi4 calculation not available")
        
    except Exception as e:
        raise MissingConsensusDescriptorError(f"Failed to calculate quadrupole moment: {str(e)}")

def calculate_polarizability(mol: Union[str, Chem.Mol]) -> float:
    """
    Calculate polarizability using RDKit.
    
    Args:
        mol: RDKit Mol object or SMILES string.
        
    Returns:
        Polarizability in cubic Angstroms.
        
    Raises:
        MissingConsensusDescriptorError: If calculation fails.
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError("Invalid SMILES string")
        
        # Use RDKit's polarizability descriptor
        # This is an approximation based on molecular volume
        polarizability = Descriptors.Polarizability(mol)
        
        return float(polarizability)
    except Exception as e:
        raise MissingConsensusDescriptorError(f"Failed to calculate polarizability: {str(e)}")

def calculate_vdw_volume(mol: Union[str, Chem.Mol]) -> float:
    """
    Calculate van der Waals volume using RDKit.
    
    Args:
        mol: RDKit Mol object or SMILES string.
        
    Returns:
        VdW volume in cubic Angstroms.
        
    Raises:
        MissingConsensusDescriptorError: If calculation fails.
    """
    try:
        if isinstance(mol, str):
            mol = Chem.MolFromSmiles(mol)
            if mol is None:
                raise ValueError("Invalid SMILES string")
        
        # Calculate VdW volume using RDKit
        vdw_volume = rdMolDescriptors.CalcCrippenDescriptors(mol)[1]  # Crippen's VdW volume
        
        return float(vdw_volume)
    except Exception as e:
        raise MissingConsensusDescriptorError(f"Failed to calculate VdW volume: {str(e)}")

def generate_descriptor_hash(descriptor_values: Tuple[float, ...]) -> str:
    """
    Generate a hash of descriptor values.
    
    Args:
        descriptor_values: Tuple of descriptor values.
        
    Returns:
        SHA256 hash string.
    """
    # Convert to string and hash
    values_str = str(sorted(descriptor_values))
    return hashlib.sha256(values_str.encode()).hexdigest()

def calculate_descriptors_batch(df: pd.DataFrame, log_dir: str = "data/validation") -> pd.DataFrame:
    """
    Calculate all descriptors for a batch of molecules.
    
    Args:
        df: DataFrame with molecular data.
        log_dir: Directory for logging missing descriptors.
        
    Returns:
        DataFrame with calculated descriptors.
    """
    ensure_directories()
    
    # Initialize descriptor columns
    df['kinetic_diameter'] = np.nan
    df['lj_epsilon'] = np.nan
    df['quadrupole_moment'] = np.nan
    df['polarizability'] = np.nan
    df['vdw_volume'] = np.nan
    
    # Log files for missing descriptors
    kinetic_log = os.path.join(log_dir, "missing_descriptors_kinetic.json")
    lj_log = os.path.join(log_dir, "missing_descriptors_lj.json")
    quadrupole_log = os.path.join(log_dir, "missing_descriptors_quadrupole.json")
    
    for idx, row in df.iterrows():
        try:
            # Calculate kinetic diameter
            if 'smiles' in row:
                try:
                    mol = Chem.MolFromSmiles(row['smiles'])
                    if mol:
                        df.at[idx, 'kinetic_diameter'] = calculate_kinetic_diameter(mol)
                    else:
                        log_missing_entry(kinetic_log, {
                            'index': idx,
                            'reason': 'invalid_smiles',
                            'smiles': row['smiles']
                        })
                except Exception as e:
                    log_missing_entry(kinetic_log, {
                        'index': idx,
                        'reason': str(e),
                        'smiles': row.get('smiles', 'N/A')
                    })
        except Exception as e:
            logger.warning(f"Error calculating kinetic diameter for index {idx}: {e}")
        
        # Calculate LJ epsilon
        try:
            df.at[idx, 'lj_epsilon'] = calculate_lj_epsilon(df, idx)
        except Exception as e:
            log_missing_entry(lj_log, {
                'index': idx,
                'reason': str(e)
            })
        
        # Calculate quadrupole moment
        try:
            if 'smiles' in row:
                try:
                    mol = Chem.MolFromSmiles(row['smiles'])
                    if mol:
                        coords = row.get('coordinates', None)
                        if isinstance(coords, str):
                            coords = eval(coords)  # Safe eval for numpy arrays
                        df.at[idx, 'quadrupole_moment'] = calculate_quadrupole_moment(mol, coords)
                    else:
                        log_missing_entry(quadrupole_log, {
                            'index': idx,
                            'reason': 'invalid_smiles',
                            'smiles': row['smiles']
                        })
                except Exception as e:
                    log_missing_entry(quadrupole_log, {
                        'index': idx,
                        'reason': str(e),
                        'smiles': row.get('smiles', 'N/A')
                    })
        except Exception as e:
            logger.warning(f"Error calculating quadrupole moment for index {idx}: {e}")
        
        # Calculate polarizability
        try:
            if 'smiles' in row:
                try:
                    mol = Chem.MolFromSmiles(row['smiles'])
                    if mol:
                        df.at[idx, 'polarizability'] = calculate_polarizability(mol)
                    else:
                        log_missing_entry(kinetic_log, {
                            'index': idx,
                            'reason': 'invalid_smiles',
                            'smiles': row['smiles']
                        })
                except Exception as e:
                    log_missing_entry(kinetic_log, {
                        'index': idx,
                        'reason': str(e),
                        'smiles': row.get('smiles', 'N/A')
                    })
        except Exception as e:
            logger.warning(f"Error calculating polarizability for index {idx}: {e}")
        
        # Calculate VdW volume
        try:
            if 'smiles' in row:
                try:
                    mol = Chem.MolFromSmiles(row['smiles'])
                    if mol:
                        df.at[idx, 'vdw_volume'] = calculate_vdw_volume(mol)
                    else:
                        log_missing_entry(kinetic_log, {
                            'index': idx,
                            'reason': 'invalid_smiles',
                            'smiles': row['smiles']
                        })
                except Exception as e:
                    log_missing_entry(kinetic_log, {
                        'index': idx,
                        'reason': str(e),
                        'smiles': row.get('smiles', 'N/A')
                    })
        except Exception as e:
            logger.warning(f"Error calculating VdW volume for index {idx}: {e}")
    
    return df

def cache_descriptors(df: pd.DataFrame, cache_path: str = "data/processed/descriptors_cache.parquet") -> None:
    """
    Cache calculated descriptors to a parquet file.
    
    Args:
        df: DataFrame with calculated descriptors.
        cache_path: Path to save cache.
    """
    ensure_directories()
    df.to_parquet(cache_path, index=False)
    logger.info(f"Descriptors cached to {cache_path}")

def load_cached_descriptors(cache_path: str = "data/processed/descriptors_cache.parquet") -> pd.DataFrame:
    """
    Load cached descriptors from a parquet file.
    
    Args:
        cache_path: Path to load cache from.
        
    Returns:
        DataFrame with cached descriptors.
    """
    if os.path.exists(cache_path):
        return pd.read_parquet(cache_path)
    else:
        raise FileNotFoundError(f"Cache file not found: {cache_path}")

def merge_descriptor_logs(base_path: str = "data/validation", output_path: str = "data/validation/missing_descriptors_report.json") -> Dict[str, Any]:
    """
    Merge individual descriptor logs into a single report.
    
    Args:
        base_path: Base directory for log files.
        output_path: Path for the merged report.
        
    Returns:
        Dictionary containing the merged report.
    """
    ensure_directories()
    
    log_files = [
        os.path.join(base_path, "missing_descriptors_kinetic.json"),
        os.path.join(base_path, "missing_descriptors_lj.json"),
        os.path.join(base_path, "missing_descriptors_quadrupole.json")
    ]
    
    merged_report = {
        "kinetic_diameter_failures": [],
        "lj_epsilon_failures": [],
        "quadrupole_moment_failures": [],
        "total_failures": 0,
        "summary": {}
    }
    
    # Load and merge kinetic diameter failures
    kinetic_path = log_files[0]
    if os.path.exists(kinetic_path):
        try:
            with open(kinetic_path, 'r') as f:
                merged_report["kinetic_diameter_failures"] = json.load(f)
        except (json.JSONDecodeError, IOError):
            merged_report["kinetic_diameter_failures"] = []
    
    # Load and merge LJ epsilon failures
    lj_path = log_files[1]
    if os.path.exists(lj_path):
        try:
            with open(lj_path, 'r') as f:
                merged_report["lj_epsilon_failures"] = json.load(f)
        except (json.JSONDecodeError, IOError):
            merged_report["lj_epsilon_failures"] = []
    
    # Load and merge quadrupole moment failures
    quadrupole_path = log_files[2]
    if os.path.exists(quadrupole_path):
        try:
            with open(quadrupole_path, 'r') as f:
                merged_report["quadrupole_moment_failures"] = json.load(f)
        except (json.JSONDecodeError, IOError):
            merged_report["quadrupole_moment_failures"] = []
    
    # Calculate summary statistics
    merged_report["total_failures"] = (
        len(merged_report["kinetic_diameter_failures"]) +
        len(merged_report["lj_epsilon_failures"]) +
        len(merged_report["quadrupole_moment_failures"])
    )
    
    merged_report["summary"] = {
        "kinetic_diameter_failures": len(merged_report["kinetic_diameter_failures"]),
        "lj_epsilon_failures": len(merged_report["lj_epsilon_failures"]),
        "quadrupole_moment_failures": len(merged_report["quadrupole_moment_failures"]),
        "total_failures": merged_report["total_failures"]
    }
    
    # Write merged report
    with open(output_path, 'w') as f:
        json.dump(merged_report, f, indent=2)
    
    logger.info(f"Merged descriptor logs saved to {output_path}")
    return merged_report

def main():
    """Main entry point for descriptor calculation and logging."""
    logger.info("Starting descriptor calculation and logging pipeline")
    
    # Example usage:
    # 1. Load data
    # 2. Calculate descriptors
    # 3. Merge logs
    
    # This would typically be called from the main orchestrator
    # with actual data paths and parameters
    pass

if __name__ == "__main__":
    main()
