"""
T018: Calculate 3D descriptors (radius of gyration, asphericity, principal moments)
using experimental CIF coordinates.

Reads: data/dataset_filtered.csv
Writes: data/dataset.csv
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

# Import from local project modules
from cif_parsing import parse_cif_with_pymatgen
from config import get_data_dir, get_base_dir
from utils import setup_logging, fix_seed

# Set up logging
logger = setup_logging("add_3d_descriptors")

def calculate_radius_of_gyration(coordinates: np.ndarray, masses: Optional[np.ndarray] = None) -> float:
    """
    Calculate the radius of gyration from atomic coordinates.
    Rg = sqrt( sum(m_i * |r_i - r_cm|^2) / sum(m_i) )
    If masses are not provided, assume uniform mass (m_i = 1).
    """
    if masses is None:
        masses = np.ones(len(coordinates))

    center_of_mass = np.average(coordinates, axis=0, weights=masses)
    diffs = coordinates - center_of_mass
    sq_dist = np.sum(diffs ** 2, axis=1)
    weighted_sq_dist = masses * sq_dist
    return float(np.sqrt(np.sum(weighted_sq_dist) / np.sum(masses)))

def calculate_principal_moments(coordinates: np.ndarray, masses: Optional[np.ndarray] = None) -> Tuple[float, float, float]:
    """
    Calculate the principal moments of inertia.
    Returns sorted tuple (I1, I2, I3) where I1 <= I2 <= I3.
    """
    if masses is None:
        masses = np.ones(len(coordinates))

    center_of_mass = np.average(coordinates, axis=0, weights=masses)
    diffs = coordinates - center_of_mass

    # Inertia tensor calculation
    # I_xx = sum(m * (y^2 + z^2))
    # I_yy = sum(m * (x^2 + z^2))
    # I_zz = sum(m * (x^2 + y^2))
    # I_xy = -sum(m * x * y)
    # etc.
    
    x, y, z = diffs[:, 0], diffs[:, 1], diffs[:, 2]
    
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
    eigenvalues = np.sort(eigenvalues)
    
    # Ensure non-negative (numerical errors might cause tiny negatives)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    
    return tuple(float(ev) for ev in eigenvalues)

def calculate_asphericity(principal_moments: Tuple[float, float, float]) -> float:
    """
    Calculate the asphericity parameter.
    Asphericity = (3/2) * ( (I_zz - I_avg)^2 + (I_yy - I_avg)^2 + (I_xx - I_avg)^2 ) / (I_xx + I_yy + I_zz)^2
    where I_avg = (I_xx + I_yy + I_zz) / 3
    This measures deviation from spherical symmetry.
    Range: 0 (spherical) to 1 (rod-like)
    """
    I1, I2, I3 = principal_moments
    I_total = I1 + I2 + I3
    
    if I_total == 0:
        return 0.0
        
    I_avg = I_total / 3.0
    
    numerator = (3.0/2.0) * ((I3 - I_avg)**2 + (I2 - I_avg)**2 + (I1 - I_avg)**2)
    denominator = I_total**2
    
    return float(numerator / denominator)

def compute_3d_descriptors(structure) -> Dict[str, Any]:
    """
    Compute all 3D descriptors for a pymatgen Structure object.
    """
    # Get fractional coordinates and convert to Cartesian
    coords_cartesian = structure.cartesian_coords
    
    # Get atomic masses (approximate by element)
    masses = np.array([atom.species.weight for atom in structure])
    
    # Calculate descriptors
    rg = calculate_radius_of_gyration(coords_cartesian, masses)
    pm = calculate_principal_moments(coords_cartesian, masses)
    asph = calculate_asphericity(pm)
    
    return {
        'radius_of_gyration': rg,
        'principal_moments': list(pm),
        'asphericity': asph
    }

def add_3d_descriptors_to_dataset(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Read the filtered dataset, load original CIF files, compute 3D descriptors,
    and merge them back into the dataset.
    """
    data_dir = get_data_dir()
    raw_cif_dir = os.path.join(data_dir, "raw_cif")
    
    logger.info(f"Reading input dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Processing {len(df)} records to compute 3D descriptors")
    
    descriptors_list = []
    missing_cif_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        cod_id = row['cod_id']
        
        # Construct CIF file path
        cif_filename = f"{cod_id}.cif"
        cif_path = os.path.join(raw_cif_dir, cif_filename)
        
        if not os.path.exists(cif_path):
            logger.warning(f"CIF file not found for {cod_id}: {cif_path}")
            missing_cif_count += 1
            # Append NaN values for missing data
            descriptors_list.append({
                'cod_id': cod_id,
                'radius_of_gyration': np.nan,
                'asphericity': np.nan,
                'principal_moments': [np.nan, np.nan, np.nan]
            })
            continue
        
        try:
            # Parse CIF using pymatgen
            structure = parse_cif_with_pymatgen(cif_path)
            
            if structure is None:
                logger.error(f"Failed to parse CIF structure for {cod_id}")
                error_count += 1
                descriptors_list.append({
                    'cod_id': cod_id,
                    'radius_of_gyration': np.nan,
                    'asphericity': np.nan,
                    'principal_moments': [np.nan, np.nan, np.nan]
                })
                continue
            
            # Compute descriptors
            desc = compute_3d_descriptors(structure)
            
            descriptors_list.append({
                'cod_id': cod_id,
                'radius_of_gyration': desc['radius_of_gyration'],
                'asphericity': desc['asphericity'],
                'principal_moments': desc['principal_moments']
            })
            
        except Exception as e:
            logger.error(f"Error computing descriptors for {cod_id}: {str(e)}")
            error_count += 1
            descriptors_list.append({
                'cod_id': cod_id,
                'radius_of_gyration': np.nan,
                'asphericity': np.nan,
                'principal_moments': [np.nan, np.nan, np.nan]
            })
    
    # Create DataFrame from descriptors
    desc_df = pd.DataFrame(descriptors_list)
    
    # Merge with original dataset
    final_df = pd.merge(df, desc_df, on='cod_id', how='left')
    
    # Log statistics
    logger.info(f"Processing complete:")
    logger.info(f"  - Total records: {len(df)}")
    logger.info(f"  - Missing CIF files: {missing_cif_count}")
    logger.info(f"  - Parse errors: {error_count}")
    logger.info(f"  - Successfully processed: {len(df) - missing_cif_count - error_count}")
    
    # Write output
    logger.info(f"Writing output to {output_path}")
    final_df.to_csv(output_path, index=False)
    
    return final_df

def main():
    """Main entry point for T018."""
    fix_seed()
    
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir, "dataset_filtered.csv")
    output_path = os.path.join(data_dir, "dataset.csv")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T016 (filter_dataset.py) has been run successfully.")
        sys.exit(1)
    
    try:
        result_df = add_3d_descriptors_to_dataset(input_path, output_path)
        
        # Verification
        required_columns = [
            'cod_id', 'smiles', 'smiles_source', 'unit_cell_volume', 
            'n_atoms', 'lattice_system', 'temperature_K', 'has_solvent',
            'radius_of_gyration', 'asphericity', 'principal_moments', 
            'cape', 'raw_pc'
        ]
        
        missing_cols = [col for col in required_columns if col not in result_df.columns]
        if missing_cols:
            logger.error(f"Output is missing required columns: {missing_cols}")
            sys.exit(1)
        
        logger.info(f"Verification passed: All required columns present.")
        logger.info(f"Output dataset written to {output_path} with {len(result_df)} rows.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()