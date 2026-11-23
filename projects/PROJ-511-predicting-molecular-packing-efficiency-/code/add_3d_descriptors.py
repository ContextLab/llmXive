import os
import sys
import logging
import time
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

# Import utils for logging and config
from utils import setup_logging
from config import get_data_dir, get_base_dir

# Import error handling utilities
from error_handling import CIFParseError, handle_corrupt_cif

def calculate_radius_of_gyration(atomic_coords: np.ndarray, masses: Optional[np.ndarray] = None) -> float:
    """
    Calculate the radius of gyration (Rg) from a set of atomic coordinates.
    
    Rg = sqrt( sum(m_i * |r_i - r_cm|^2) / sum(m_i) )
    
    If masses are not provided, uniform mass (1.0) is assumed for all atoms.
    
    Args:
        atomic_coords: Array of shape (N, 3) containing Cartesian coordinates.
        masses: Optional array of shape (N,) containing atomic masses.
    
    Returns:
        Radius of gyration in Angstroms.
    """
    if masses is None:
        masses = np.ones(len(atomic_coords))
    
    total_mass = np.sum(masses)
    center_of_mass = np.average(atomic_coords, axis=0, weights=masses)
    
    distances_sq = np.sum((atomic_coords - center_of_mass) ** 2, axis=1)
    weighted_distances_sq = masses * distances_sq
    
    rg_sq = np.sum(weighted_distances_sq) / total_mass
    return np.sqrt(rg_sq)

def calculate_principal_moments(atomic_coords: np.ndarray, masses: Optional[np.ndarray] = None) -> Tuple[float, float, float]:
    """
    Calculate the principal moments of inertia from atomic coordinates.
    
    Returns the three eigenvalues of the inertia tensor, sorted in ascending order.
    
    Args:
        atomic_coords: Array of shape (N, 3) containing Cartesian coordinates.
        masses: Optional array of shape (N,) containing atomic masses.
    
    Returns:
        Tuple of three principal moments (I1, I2, I3) in amu*angstrom^2.
    """
    if masses is None:
        masses = np.ones(len(atomic_coords))
    
    total_mass = np.sum(masses)
    center_of_mass = np.average(atomic_coords, axis=0, weights=masses)
    
    # Shift coordinates to center of mass
    r = atomic_coords - center_of_mass
    
    # Inertia tensor components
    # Ixx = sum(m * (y^2 + z^2))
    # Ixy = -sum(m * x * y)
    # etc.
    
    x, y, z = r[:, 0], r[:, 1], r[:, 2]
    
    Ixx = np.sum(masses * (y**2 + z**2))
    Iyy = np.sum(masses * (x**2 + z**2))
    Izz = np.sum(masses * (x**2 + y**2))
    
    Ixy = -np.sum(masses * x * y)
    Ixz = -np.sum(masses * x * z)
    Iyz = -np.sum(masses * y * z)
    
    inertia_tensor = np.array([
        [Ixx, Ixy, Ixz],
        [Ixy, Iyy, Iyz],
        [Ixz, Iyz, Izz]
    ])
    
    # Calculate eigenvalues (principal moments)
    eigenvalues = np.linalg.eigvalsh(inertia_tensor)
    
    # Sort in ascending order
    eigenvalues = np.sort(eigenvalues)
    
    return tuple(eigenvalues)

def calculate_asphericity(principal_moments: Tuple[float, float, float]) -> float:
    """
    Calculate the asphericity (A) from principal moments of inertia.
    
    A = (3/2) * (I3 - (I1 + I2)/2) / (I1 + I2 + I3)
    
    where I1 <= I2 <= I3 are the principal moments.
    
    Asphericity ranges from 0 (spherical) to 1 (rod-like).
    
    Args:
        principal_moments: Tuple of three principal moments (I1, I2, I3).
    
    Returns:
        Asphericity value between 0 and 1.
    """
    I1, I2, I3 = principal_moments
    total_moment = I1 + I2 + I3
    
    if total_moment == 0:
        return 0.0
    
    asphericity = (3.0 / 2.0) * (I3 - (I1 + I2) / 2.0) / total_moment
    
    # Clamp to [0, 1] to handle numerical errors
    return max(0.0, min(1.0, asphericity))

def compute_3d_descriptors(cif_path: str) -> Dict[str, Any]:
    """
    Compute 3D descriptors (radius of gyration, asphericity, principal moments)
    from a CIF file using pymatgen.
    
    Args:
        cif_path: Path to the CIF file.
    
    Returns:
        Dictionary containing:
            - radius_of_gyration: float
            - asphericity: float
            - principal_moments: list of 3 floats
    
    Raises:
        CIFParseError: If the CIF file cannot be parsed.
        FileNotFoundError: If the CIF file does not exist.
    """
    if not os.path.exists(cif_path):
        raise FileNotFoundError(f"CIF file not found: {cif_path}")
    
    try:
        structure = Structure.from_file(cif_path)
    except Exception as e:
        raise CIFParseError(f"Failed to parse CIF file {cif_path}: {str(e)}")
    
    # Get atomic coordinates and masses
    coords = structure.frac_coords
    lattice = structure.lattice.matrix
    
    # Convert fractional coordinates to Cartesian
    cartesian_coords = np.dot(coords, lattice)
    
    # Get atomic masses (default to 1.0 if not available)
    masses = np.array([atom.specie.mass for atom in structure])
    
    # Calculate descriptors
    rg = calculate_radius_of_gyration(cartesian_coords, masses)
    pm = calculate_principal_moments(cartesian_coords, masses)
    asp = calculate_asphericity(pm)
    
    return {
        'radius_of_gyration': rg,
        'asphericity': asp,
        'principal_moments': list(pm)
    }

def add_3d_descriptors_to_dataset(input_path: str, output_path: str, cif_dir: str) -> None:
    """
    Read a filtered dataset CSV, compute 3D descriptors for each CIF file,
    and merge the results into a final dataset CSV.
    
    Args:
        input_path: Path to the input CSV (data/dataset_filtered.csv).
        output_path: Path to the output CSV (data/dataset.csv).
        cif_dir: Directory containing the CIF files (data/raw_cif/).
    """
    logger = logging.getLogger(__name__)
    
    # Read the input dataset
    logger.info(f"Reading input dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    if 'cod_id' not in df.columns:
        raise ValueError("Input dataset must contain 'cod_id' column")
    
    logger.info(f"Processing {len(df)} records")
    
    descriptors_list = []
    success_count = 0
    failure_count = 0
    
    for idx, row in df.iterrows():
        cod_id = row['cod_id']
        cif_filename = f"{cod_id}.cif"
        cif_path = os.path.join(cif_dir, cif_filename)
        
        try:
            desc = compute_3d_descriptors(cif_path)
            descriptors_list.append(desc)
            success_count += 1
            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} records (success: {success_count}, failure: {failure_count})")
        except FileNotFoundError as e:
            logger.error(f"CIF file missing for {cod_id}: {str(e)}")
            failure_count += 1
            # Still append a row with NaN values to maintain row count
            descriptors_list.append({
                'radius_of_gyration': np.nan,
                'asphericity': np.nan,
                'principal_moments': [np.nan, np.nan, np.nan]
            })
        except CIFParseError as e:
            logger.error(f"Failed to parse CIF for {cod_id}: {str(e)}")
            failure_count += 1
            descriptors_list.append({
                'radius_of_gyration': np.nan,
                'asphericity': np.nan,
                'principal_moments': [np.nan, np.nan, np.nan]
            })
        except Exception as e:
            logger.error(f"Unexpected error processing {cod_id}: {str(e)}")
            failure_count += 1
            descriptors_list.append({
                'radius_of_gyration': np.nan,
                'asphericity': np.nan,
                'principal_moments': [np.nan, np.nan, np.nan]
            })
    
    # Create DataFrame from descriptors
    desc_df = pd.DataFrame(descriptors_list)
    
    # Flatten principal_moments into separate columns
    if 'principal_moments' in desc_df.columns:
        pm_list = desc_df['principal_moments'].tolist()
        pm_df = pd.DataFrame(pm_list, columns=['principal_moment_1', 'principal_moment_2', 'principal_moment_3'])
        desc_df = desc_df.drop('principal_moments', axis=1)
        desc_df = pd.concat([desc_df, pm_df], axis=1)
    
    # Merge with original dataset
    result_df = pd.concat([df, desc_df], axis=1)
    
    # Reorder columns to match expected output
    expected_columns = [
        'cod_id', 'smiles', 'smiles_source', 'unit_cell_volume', 'n_atoms',
        'lattice_system', 'temperature_K', 'has_solvent',
        'radius_of_gyration', 'asphericity', 'principal_moment_1', 
        'principal_moment_2', 'principal_moment_3', 'cape', 'raw_pc'
    ]
    
    # Check if all expected columns exist
    missing_cols = [col for col in expected_columns if col not in result_df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in result: {missing_cols}")
    
    # Select only columns that exist in result_df
    available_cols = [col for col in expected_columns if col in result_df.columns]
    result_df = result_df[available_cols]
    
    # Write output
    logger.info(f"Writing output dataset to {output_path}")
    result_df.to_csv(output_path, index=False)
    
    logger.info(f"Completed. Success: {success_count}, Failure: {failure_count}")
    
    # Verify output
    if os.path.exists(output_path):
        output_df = pd.read_csv(output_path)
        logger.info(f"Output verification: {len(output_df)} rows, columns: {list(output_df.columns)}")
    else:
        raise RuntimeError(f"Failed to write output file: {output_path}")

def main():
    """Main entry point for the add_3d_descriptors script."""
    logger = setup_logging("add_3d_descriptors")
    
    start_time = time.time()
    
    # Get paths
    data_dir = get_data_dir()
    cif_dir = os.path.join(data_dir, "raw_cif")
    input_path = os.path.join(data_dir, "dataset_filtered.csv")
    output_path = os.path.join(data_dir, "dataset.csv")
    
    logger.info(f"Starting 3D descriptor computation")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"CIF directory: {cif_dir}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if not os.path.exists(cif_dir):
        raise FileNotFoundError(f"CIF directory not found: {cif_dir}")
    
    try:
        add_3d_descriptors_to_dataset(input_path, output_path, cif_dir)
    except Exception as e:
        logger.error(f"Error during descriptor computation: {str(e)}")
        raise
    
    end_time = time.time()
    logger.info(f"Completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
