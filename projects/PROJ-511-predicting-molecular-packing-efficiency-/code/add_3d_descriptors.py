"""
T018: Add 3D descriptors to the filtered dataset.

Reads `data/dataset_filtered.csv`, re-loads original CIFs from `data/raw_cif/`,
computes radius of gyration, asphericity, and principal moments using pymatgen,
and merges them into `data/dataset.csv`.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

# Local imports matching the API surface
from config import get_data_dir, get_base_dir
from cif_parsing import parse_cif_with_pymatgen

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def calculate_radius_of_gyration(coordinates: np.ndarray, masses: Optional[np.ndarray] = None) -> float:
    """
    Calculate the radius of gyration (Rg) from atomic coordinates.
    
    Rg = sqrt( sum_i (m_i * |r_i - r_cm|^2) / sum_i (m_i) )
    If masses are None, uniform mass is assumed.
    
    Args:
        coordinates: (N, 3) array of atomic coordinates in Angstroms.
        masses: (N,) array of atomic masses. If None, uniform mass is used.
    
    Returns:
        Radius of gyration in Angstroms.
    """
    if coordinates.shape[0] == 0:
        return 0.0
    
    if masses is None:
        masses = np.ones(coordinates.shape[0])
    
    # Center of mass
    total_mass = np.sum(masses)
    center_of_mass = np.sum(masses[:, np.newaxis] * coordinates, axis=0) / total_mass
    
    # Squared distances from center of mass
    diff = coordinates - center_of_mass
    sq_dist = np.sum(diff**2, axis=1)
    
    # Weighted sum
    rg_sq = np.sum(masses * sq_dist) / total_mass
    
    return np.sqrt(rg_sq)

def calculate_principal_moments(coordinates: np.ndarray, masses: Optional[np.ndarray] = None) -> Tuple[float, float, float]:
    """
    Calculate the principal moments of inertia (I1, I2, I3).
    
    Args:
        coordinates: (N, 3) array of atomic coordinates in Angstroms.
        masses: (N,) array of atomic masses. If None, uniform mass is used.
    
    Returns:
        Tuple of (I1, I2, I3) sorted in ascending order. Units: amu * Angstrom^2.
    """
    if coordinates.shape[0] == 0:
        return (0.0, 0.0, 0.0)
    
    if masses is None:
        masses = np.ones(coordinates.shape[0])
    
    total_mass = np.sum(masses)
    center_of_mass = np.sum(masses[:, np.newaxis] * coordinates, axis=0) / total_mass
    
    # Shift coordinates to center of mass
    coords_centered = coordinates - center_of_mass
    
    # Inertia tensor calculation
    # I_xx = sum m_i (y_i^2 + z_i^2)
    # I_yy = sum m_i (x_i^2 + z_i^2)
    # I_zz = sum m_i (x_i^2 + y_i^2)
    # I_xy = - sum m_i x_i y_i
    # etc.
    
    x = coords_centered[:, 0]
    y = coords_centered[:, 1]
    z = coords_centered[:, 2]
    
    I_xx = np.sum(masses * (y**2 + z**2))
    I_yy = np.sum(masses * (x**2 + z**2))
    I_zz = np.sum(masses * (x**2 + y**2))
    I_xy = -np.sum(masses * x * y)
    I_xz = -np.sum(masses * x * z)
    I_yz = -np.sum(masses * y * z)
    
    inertia_tensor = np.array([
        [I_xx, I_xy, I_xz],
        [I_xy, I_yy, I_yz],
        [I_xz, I_yz, I_zz]
    ])
    
    # Eigenvalues are the principal moments
    eigenvalues = np.linalg.eigvalsh(inertia_tensor)
    
    # Sort ascending
    eigenvalues.sort()
    
    return (float(eigenvalues[0]), float(eigenvalues[1]), float(eigenvalues[2]))

def calculate_asphericity(principal_moments: Tuple[float, float, float]) -> float:
    """
    Calculate the asphericity (b) from principal moments of inertia.
    
    b = (3/2) * [ I_zz - (I_xx + I_yy)/2 ] / (I_xx + I_yy + I_zz)
    where I_xx <= I_yy <= I_zz (sorted).
    
    Asphericity ranges from 0 (sphere) to 1 (rod-like).
    
    Args:
        principal_moments: Tuple (I1, I2, I3) sorted ascending.
    
    Returns:
        Asphericity value between 0 and 1.
    """
    I1, I2, I3 = principal_moments
    total = I1 + I2 + I3
    
    if total == 0:
        return 0.0
    
    # Asphericity formula
    numerator = I3 - (I1 + I2) / 2.0
    asphericity = (3.0 / 2.0) * (numerator / total)
    
    # Clamp to [0, 1] to handle numerical issues
    return float(np.clip(asphericity, 0.0, 1.0))

def compute_3d_descriptors(structure) -> Dict[str, Any]:
    """
    Compute 3D descriptors from a pymatgen Structure object.
    
    Args:
        structure: pymatgen.core.Structure object.
    
    Returns:
        Dictionary with keys:
            - radius_of_gyration: float (Angstroms)
            - asphericity: float (0-1)
            - principal_moments: tuple of 3 floats (amu*Angstrom^2)
    """
    coords = structure.frac_coords
    lattice = structure.lattice
    
    # Convert fractional to cartesian coordinates
    cart_coords = lattice.get_cartesian_coords(coords)
    
    # Get atomic masses
    masses = np.array([structure[i].species.weight for i in range(len(structure))])
    
    # Calculate descriptors
    rg = calculate_radius_of_gyration(cart_coords, masses)
    moments = calculate_principal_moments(cart_coords, masses)
    asp = calculate_asphericity(moments)
    
    return {
        "radius_of_gyration": rg,
        "asphericity": asp,
        "principal_moments": list(moments)
    }

def add_3d_descriptors_to_dataset(df: pd.DataFrame, cif_dir: str) -> pd.DataFrame:
    """
    Add 3D descriptors to a dataframe by re-loading CIFs.
    
    Args:
        df: DataFrame with columns including 'cod_id'.
        cif_dir: Path to directory containing CIF files.
    
    Returns:
        DataFrame with added columns: radius_of_gyration, asphericity, principal_moments.
    """
    logger.info(f"Starting 3D descriptor computation for {len(df)} structures...")
    
    descriptors_list = []
    failed_ids = []
    
    for idx, row in df.iterrows():
        cod_id = row['cod_id']
        cif_filename = f"{cod_id}.cif"
        cif_path = os.path.join(cif_dir, cif_filename)
        
        if not os.path.exists(cif_path):
            logger.warning(f"CIF file missing for {cod_id}: {cif_path}")
            failed_ids.append(cod_id)
            # Add null values for failed entries
            descriptors_list.append({
                "cod_id": cod_id,
                "radius_of_gyration": np.nan,
                "asphericity": np.nan,
                "principal_moments": [np.nan, np.nan, np.nan]
            })
            continue
        
        try:
            # Parse CIF using pymatgen (from cif_parsing module)
            structure = parse_cif_with_pymatgen(cif_path)
            
            if structure is None:
                logger.error(f"Failed to parse CIF for {cod_id}")
                failed_ids.append(cod_id)
                descriptors_list.append({
                    "cod_id": cod_id,
                    "radius_of_gyration": np.nan,
                    "asphericity": np.nan,
                    "principal_moments": [np.nan, np.nan, np.nan]
                })
                continue
            
            # Compute descriptors
            desc = compute_3d_descriptors(structure)
            descriptors_list.append({
                "cod_id": cod_id,
                "radius_of_gyration": desc["radius_of_gyration"],
                "asphericity": desc["asphericity"],
                "principal_moments": desc["principal_moments"]
            })
            
            if (idx + 1) % 50 == 0:
                logger.info(f"Processed {idx + 1}/{len(df)} structures...")
                
        except Exception as e:
            logger.error(f"Error processing {cod_id}: {e}")
            failed_ids.append(cod_id)
            descriptors_list.append({
                "cod_id": cod_id,
                "radius_of_gyration": np.nan,
                "asphericity": np.nan,
                "principal_moments": [np.nan, np.nan, np.nan]
            })
    
    if failed_ids:
        logger.warning(f"Failed to compute descriptors for {len(failed_ids)} structures: {failed_ids[:5]}...")
    
    # Create descriptors DataFrame
    desc_df = pd.DataFrame(descriptors_list)
    
    # Merge with original dataframe
    # Ensure principal_moments is expanded into 3 columns or kept as list
    # For schema compliance, we'll keep it as a list in one column, 
    # but the schema expects an array. We'll store as list and let validation handle it.
    
    result_df = pd.merge(df, desc_df, on='cod_id', how='left')
    
    # Ensure column order matches spec
    expected_cols = [
        'cod_id', 'smiles', 'smiles_source', 'unit_cell_volume', 'n_atoms',
        'lattice_system', 'temperature_K', 'has_solvent',
        'radius_of_gyration', 'asphericity', 'principal_moments',
        'cape', 'raw_pc'
    ]
    
    # Reorder columns if they exist
    existing_cols = [c for c in expected_cols if c in result_df.columns]
    other_cols = [c for c in result_df.columns if c not in expected_cols]
    result_df = result_df[existing_cols + other_cols]
    
    return result_df

def main():
    """Main entry point for T018."""
    logger.info("Starting T018: Add 3D descriptors to dataset")
    
    # Paths
    data_dir = get_data_dir()
    filtered_path = os.path.join(data_dir, "dataset_filtered.csv")
    output_path = os.path.join(data_dir, "dataset.csv")
    cif_dir = os.path.join(data_dir, "raw_cif")
    
    # Verify input exists
    if not os.path.exists(filtered_path):
        raise FileNotFoundError(f"Input file not found: {filtered_path}. Run T016 first.")
    
    if not os.path.exists(cif_dir):
        raise FileNotFoundError(f"CIF directory not found: {cif_dir}. Run T012 first.")
    
    # Load filtered dataset
    logger.info(f"Loading filtered dataset from {filtered_path}")
    df_filtered = pd.read_csv(filtered_path)
    logger.info(f"Loaded {len(df_filtered)} records")
    
    # Add 3D descriptors
    logger.info(f"Computing 3D descriptors from CIFs in {cif_dir}")
    df_final = add_3d_descriptors_to_dataset(df_filtered, cif_dir)
    
    # Save final dataset
    logger.info(f"Saving final dataset to {output_path}")
    df_final.to_csv(output_path, index=False)
    
    logger.info(f"Successfully created {output_path} with {len(df_final)} records")
    logger.info("T018 completed successfully")
    
    return df_final

if __name__ == "__main__":
    main()
