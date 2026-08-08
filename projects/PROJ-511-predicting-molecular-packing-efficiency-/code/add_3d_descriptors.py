"""
Module: add_3d_descriptors.py
Task: T018 [US1]
Description: Calculate 3D descriptors (radius of gyration, asphericity, principal moments)
             using CIF coordinates. Reads dataset_filtered.csv, re-loads original CIFs,
             computes descriptors, and merges to produce final dataset.csv.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import Optional, Tuple, List, Dict, Any

# Import from existing project modules
from cif_parsing import parse_cif_with_pymatgen, extract_atomic_coordinates
from config import get_data_dir, get_base_dir
from utils import fix_seed, setup_logging

# Setup logging
logger = logging.getLogger(__name__)

def calculate_radius_of_gyration(coordinates: np.ndarray, weights: Optional[np.ndarray] = None) -> float:
    """
    Calculate the radius of gyration (Rg) for a set of atomic coordinates.
    Rg = sqrt( sum(w_i * |r_i - r_cm|^2) / sum(w_i) )
    
    Args:
        coordinates: Array of shape (N, 3) containing atomic coordinates.
        weights: Optional array of shape (N,) containing atomic weights (defaults to 1.0).
    
    Returns:
        Radius of gyration in Angstroms.
    """
    if weights is None:
        weights = np.ones(len(coordinates))
    
    # Calculate center of mass
    total_weight = np.sum(weights)
    center_of_mass = np.sum(weights[:, np.newaxis] * coordinates, axis=0) / total_weight
    
    # Calculate squared distances from center of mass
    diffs = coordinates - center_of_mass
    squared_distances = np.sum(diffs**2, axis=1)
    
    # Weighted mean squared distance
    mean_sq_dist = np.sum(weights * squared_distances) / total_weight
    
    return np.sqrt(mean_sq_dist)

def calculate_principal_moments(coordinates: np.ndarray, weights: Optional[np.ndarray] = None) -> Tuple[float, float, float]:
    """
    Calculate the principal moments of inertia for a set of atomic coordinates.
    Returns the three eigenvalues sorted in ascending order.
    
    Args:
        coordinates: Array of shape (N, 3) containing atomic coordinates.
        weights: Optional array of shape (N,) containing atomic weights (defaults to 1.0).
    
    Returns:
        Tuple of (I1, I2, I3) sorted ascending, in amu*Angstrom^2.
    """
    if weights is None:
        weights = np.ones(len(coordinates))
    
    # Calculate center of mass
    total_weight = np.sum(weights)
    center_of_mass = np.sum(weights[:, np.newaxis] * coordinates, axis=0) / total_weight
    
    # Shift coordinates to center of mass
    centered_coords = coordinates - center_of_mass
    
    # Calculate inertia tensor
    # I_xx = sum(m_i * (y_i^2 + z_i^2))
    # I_yy = sum(m_i * (x_i^2 + z_i^2))
    # I_zz = sum(m_i * (x_i^2 + y_i^2))
    # I_xy = -sum(m_i * x_i * y_i)
    # I_xz = -sum(m_i * x_i * z_i)
    # I_yz = -sum(m_i * y_i * z_i)
    
    x = centered_coords[:, 0]
    y = centered_coords[:, 1]
    z = centered_coords[:, 2]
    
    I_xx = np.sum(weights * (y**2 + z**2))
    I_yy = np.sum(weights * (x**2 + z**2))
    I_zz = np.sum(weights * (x**2 + y**2))
    I_xy = -np.sum(weights * x * y)
    I_xz = -np.sum(weights * x * z)
    I_yz = -np.sum(weights * y * z)
    
    # Construct inertia tensor
    inertia_tensor = np.array([
        [I_xx, I_xy, I_xz],
        [I_xy, I_yy, I_yz],
        [I_xz, I_yz, I_zz]
    ])
    
    # Calculate eigenvalues (principal moments)
    eigenvalues = np.linalg.eigvalsh(inertia_tensor)
    
    # Sort in ascending order
    return tuple(np.sort(eigenvalues))

def calculate_asphericity(principal_moments: Tuple[float, float, float]) -> float:
    """
    Calculate the asphericity parameter from principal moments of inertia.
    Asphericity = (3*I3 - I1 - I2) / (2 * sqrt(I1^2 + I2^2 + I3^2 - I1*I2 - I2*I3 - I3*I1))
    where I1 <= I2 <= I3.
    
    This measures the deviation from spherical symmetry.
    Value ranges from -0.5 (oblate) to 1.0 (prolate).
    
    Args:
        principal_moments: Tuple of (I1, I2, I3) sorted ascending.
    
    Returns:
        Asphericity value.
    """
    I1, I2, I3 = principal_moments
    
    # Avoid division by zero for spherical molecules
    denominator_sq = I1**2 + I2**2 + I3**2 - I1*I2 - I2*I3 - I3*I1
    if denominator_sq < 1e-10:
        return 0.0
    
    numerator = 3*I3 - I1 - I2
    denominator = 2 * np.sqrt(denominator_sq)
    
    return numerator / denominator

def compute_3d_descriptors(cif_path: str) -> Dict[str, float]:
    """
    Compute all 3D descriptors for a single CIF file.
    
    Args:
        cif_path: Path to the CIF file.
    
    Returns:
        Dictionary containing:
            - radius_of_gyration: float
            - asphericity: float
            - principal_moments: tuple of 3 floats (as a list for JSON serialization)
    
    Raises:
        FileNotFoundError: If the CIF file does not exist.
        ValueError: If the CIF file cannot be parsed or has invalid data.
    """
    if not os.path.exists(cif_path):
        raise FileNotFoundError(f"CIF file not found: {cif_path}")
    
    try:
        # Parse CIF using pymatgen via cif_parsing module
        structure = parse_cif_with_pymatgen(cif_path)
        
        if structure is None:
            raise ValueError(f"Failed to parse CIF file: {cif_path}")
        
        # Extract atomic coordinates and atomic numbers (for weights)
        coords = structure.frac_coords
        lattice = structure.lattice.matrix
        atomic_numbers = structure.atomic_numbers
        
        # Convert fractional to Cartesian coordinates
        cartesian_coords = np.dot(coords, lattice)
        
        # Use atomic masses as weights (approximate using atomic numbers for simplicity)
        # More accurate would be to use actual atomic masses
        weights = np.array([float(z) for z in atomic_numbers])
        
        # Calculate descriptors
        rg = calculate_radius_of_gyration(cartesian_coords, weights)
        moments = calculate_principal_moments(cartesian_coords, weights)
        asph = calculate_asphericity(moments)
        
        return {
            'radius_of_gyration': float(rg),
            'asphericity': float(asph),
            'principal_moments': [float(m) for m in moments]
        }
        
    except Exception as e:
        raise ValueError(f"Error computing 3D descriptors for {cif_path}: {str(e)}")

def add_3d_descriptors_to_dataset(
    input_path: str,
    output_path: str,
    raw_cif_dir: Optional[str] = None
) -> pd.DataFrame:
    """
    Read dataset_filtered.csv, compute 3D descriptors for each CIF, and merge.
    
    Args:
        input_path: Path to dataset_filtered.csv.
        output_path: Path to write final dataset.csv.
        raw_cif_dir: Directory containing CIF files (defaults to data/raw_cif/).
    
    Returns:
        DataFrame with added 3D descriptors.
    """
    # Load filtered dataset
    logger.info(f"Loading filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    if raw_cif_dir is None:
        raw_cif_dir = os.path.join(get_data_dir(), "raw_cif")
    
    if not os.path.exists(raw_cif_dir):
        raise FileNotFoundError(f"Raw CIF directory not found: {raw_cif_dir}")
    
    # Prepare lists for new columns
    rg_list = []
    asph_list = []
    moments_list = []
    cod_ids = df['cod_id'].tolist()
    
    logger.info(f"Processing {len(df)} records to compute 3D descriptors...")
    success_count = 0
    error_count = 0
    
    for idx, cod_id in enumerate(cod_ids):
        cif_filename = f"{cod_id}.cif"
        cif_path = os.path.join(raw_cif_dir, cif_filename)
        
        try:
            # Verify file existence explicitly
            if not os.path.exists(cif_path):
                raise FileNotFoundError(f"CIF file missing for cod_id {cod_id}: {cif_path}")
            
            # Compute descriptors
            descriptors = compute_3d_descriptors(cif_path)
            
            rg_list.append(descriptors['radius_of_gyration'])
            asph_list.append(descriptors['asphericity'])
            moments_list.append(descriptors['principal_moments'])
            success_count += 1
            
        except FileNotFoundError as e:
            logger.error(f"Missing CIF for cod_id {cod_id}: {e}")
            rg_list.append(np.nan)
            asph_list.append(np.nan)
            moments_list.append([np.nan, np.nan, np.nan])
            error_count += 1
        except Exception as e:
            logger.error(f"Error processing cod_id {cod_id}: {e}")
            rg_list.append(np.nan)
            asph_list.append(np.nan)
            moments_list.append([np.nan, np.nan, np.nan])
            error_count += 1
        
        # Log progress
        if (idx + 1) % 50 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} records")
    
    # Add columns to dataframe
    df['radius_of_gyration'] = rg_list
    df['asphericity'] = asph_list
    # Convert principal moments list to string for CSV storage, or keep as object
    # For CSV, we'll store as a string representation that can be parsed later
    df['principal_moments'] = [str(m) for m in moments_list]
    
    # Log summary
    logger.info(f"3D descriptor computation complete: {success_count} successful, {error_count} failed")
    
    # Write output
    logger.info(f"Writing final dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    return df

def main():
    """Main entry point for the script."""
    # Setup logging
    setup_logging(level=logging.INFO)
    fix_seed(42)
    
    # Define paths
    data_dir = get_data_dir()
    input_path = os.path.join(data_dir, "dataset_filtered.csv")
    output_path = os.path.join(data_dir, "dataset.csv")
    raw_cif_dir = os.path.join(data_dir, "raw_cif")
    
    # Verify input exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Run the pipeline
    try:
        df = add_3d_descriptors_to_dataset(input_path, output_path, raw_cif_dir)
        
        # Log final columns
        logger.info(f"Final dataset columns: {list(df.columns)}")
        logger.info(f"Final dataset shape: {df.shape}")
        logger.info(f"Sample radius_of_gyration values: {df['radius_of_gyration'].head().tolist()}")
        
        logger.info("Task T018 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T018 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()