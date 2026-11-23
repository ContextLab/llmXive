import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any, List, Union
import logging
import os
from pathlib import Path

from utils.config import get_project_root, get_data_processed_path
from processing.inertia_tensor import compute_reduced_inertia_tensor, compute_eigenvalues_and_eigenvectors

logger = logging.getLogger(__name__)

def compute_spin_vector(positions: np.ndarray, velocities: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """
    Compute the specific angular momentum vector (spin vector) for a set of particles.
    
    Args:
        positions: (N, 3) array of particle positions relative to halo center.
        velocities: (N, 3) array of particle velocities relative to halo center.
        masses: (N,) array of particle masses.
    
    Returns:
        (3,) array representing the spin vector (specific angular momentum).
    """
    if len(positions) == 0:
        return np.zeros(3)
    
    # Cross product of position and velocity for each particle: r x v
    cross_product = np.cross(positions, velocities)
    
    # Weighted sum by mass: sum(m * (r x v))
    angular_momentum = np.sum(masses[:, np.newaxis] * cross_product, axis=0)
    
    # Normalize by total mass to get specific angular momentum
    total_mass = np.sum(masses)
    if total_mass > 0:
        return angular_momentum / total_mass
    return np.zeros(3)

def compute_major_axis_from_inertia(eigenvalues: np.ndarray, eigenvectors: np.ndarray) -> np.ndarray:
    """
    Compute the major axis vector from inertia tensor eigen decomposition.
    
    The major axis corresponds to the smallest eigenvalue (longest dimension).
    
    Args:
        eigenvalues: (3,) array of eigenvalues sorted in ascending order.
        eigenvectors: (3, 3) array of eigenvectors, columns correspond to eigenvalues.
    
    Returns:
        (3,) array representing the unit vector of the major axis.
    """
    if len(eigenvalues) != 3 or eigenvectors.shape != (3, 3):
        logger.error("Invalid eigen decomposition input")
        return np.zeros(3)
    
    # Eigenvalues should be sorted ascending; the first eigenvector corresponds to the smallest eigenvalue
    # which is the major axis (longest dimension)
    major_axis = eigenvectors[:, 0]
    
    # Ensure unit vector
    norm = np.linalg.norm(major_axis)
    if norm > 0:
        return major_axis / norm
    return np.zeros(3)

def compute_misalignment_angle(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """
    Compute the misalignment angle between two vectors in degrees.
    
    Uses the dot product formula: cos(theta) = (v1 . v2) / (|v1| * |v2|)
    
    Args:
        vector1: (3,) array of the first vector.
        vector2: (3,) array of the second vector.
    
    Returns:
        Float representing the angle in degrees (0 to 180).
    """
    if np.allclose(vector1, 0) or np.allclose(vector2, 0):
        logger.warning("Zero vector detected in misalignment calculation")
        return np.nan
    
    # Normalize vectors
    v1_norm = vector1 / np.linalg.norm(vector1)
    v2_norm = vector2 / np.linalg.norm(vector2)
    
    # Dot product
    dot_product = np.dot(v1_norm, v2_norm)
    
    # Clamp to [-1, 1] to handle floating point errors
    dot_product = np.clip(dot_product, -1.0, 1.0)
    
    # Compute angle in radians, then convert to degrees
    angle_rad = np.arccos(dot_product)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def process_alignment_for_halo(
    halo_id: int,
    positions: np.ndarray,
    velocities: np.ndarray,
    masses: np.ndarray,
    inertia_eigenvalues: np.ndarray,
    inertia_eigenvectors: np.ndarray
) -> Dict[str, Any]:
    """
    Process alignment metrics for a single halo.
    
    Args:
        halo_id: Unique identifier for the halo.
        positions: (N, 3) particle positions relative to halo center.
        velocities: (N, 3) particle velocities relative to halo center.
        masses: (N,) particle masses.
        inertia_eigenvalues: (3,) eigenvalues from reduced inertia tensor.
        inertia_eigenvectors: (3, 3) eigenvectors from reduced inertia tensor.
    
    Returns:
        Dictionary containing halo alignment metrics.
    """
    # Compute spin vector
    spin_vector = compute_spin_vector(positions, velocities, masses)
    
    # Compute major axis from inertia
    major_axis = compute_major_axis_from_inertia(inertia_eigenvalues, inertia_eigenvectors)
    
    # Compute misalignment angle between spin and major axis (intrinsic halo misalignment)
    spin_major_angle = compute_misalignment_angle(spin_vector, major_axis)
    
    return {
        'halo_id': halo_id,
        'spin_vector': spin_vector.tolist(),
        'major_axis': major_axis.tolist(),
        'spin_major_angle_deg': spin_major_angle,
        'num_particles': len(positions)
    }

def align_halo_galaxy_pairs(
    halo_data: pd.DataFrame,
    galaxy_data: pd.DataFrame
) -> pd.DataFrame:
    """
    Compute misalignment angles between halo and galaxy pairs.
    
    This function matches halos and galaxies (assumed to be matched by halo_id or index),
    computes the misalignment angle between the halo's major axis and the galaxy's spin/major axis,
    and returns a DataFrame with the results.
    
    Args:
        halo_data: DataFrame containing halo properties including 'halo_id', 'major_axis_x', 'major_axis_y', 'major_axis_z'.
        galaxy_data: DataFrame containing galaxy properties including 'halo_id', 'spin_x', 'spin_y', 'spin_z' 
                     (or galaxy major axis if computing galaxy-galaxy alignment).
    
    Returns:
        DataFrame with misalignment angles and associated metadata.
    """
    if halo_data.empty or galaxy_data.empty:
        logger.warning("Empty input data for alignment computation")
        return pd.DataFrame()
    
    # Merge on halo_id to pair halos and galaxies
    merged = pd.merge(halo_data, galaxy_data, on='halo_id', suffixes=('_halo', '_gal'))
    
    if merged.empty:
        logger.warning("No matching halo-galaxy pairs found")
        return pd.DataFrame()
    
    results = []
    
    for _, row in merged.iterrows():
        # Extract halo major axis
        halo_major = np.array([
            row.get('major_axis_x', row.get('major_axis_x_halo', np.nan)),
            row.get('major_axis_y', row.get('major_axis_y_halo', np.nan)),
            row.get('major_axis_z', row.get('major_axis_z_halo', np.nan))
        ])
        
        # Extract galaxy spin or major axis (depending on what's available)
        # Prefer spin if available, otherwise major axis
        if 'spin_x' in row or 'spin_x_gal' in row:
            galaxy_vector = np.array([
                row.get('spin_x', row.get('spin_x_gal', np.nan)),
                row.get('spin_y', row.get('spin_y_gal', np.nan)),
                row.get('spin_z', row.get('spin_z_gal', np.nan))
            ])
            vector_type = 'spin'
        elif 'major_axis_x' in row and 'major_axis_x_gal' in row:
            galaxy_vector = np.array([
                row['major_axis_x_gal'],
                row['major_axis_y_gal'],
                row['major_axis_z_gal']
            ])
            vector_type = 'major_axis'
        else:
            logger.warning(f"No galaxy vector found for halo {row['halo_id']}")
            continue
        
        # Compute misalignment angle
        angle = compute_misalignment_angle(halo_major, galaxy_vector)
        
        if not np.isnan(angle):
            results.append({
                'halo_id': row['halo_id'],
                'halo_major_axis': halo_major.tolist(),
                'galaxy_vector': galaxy_vector.tolist(),
                'galaxy_vector_type': vector_type,
                'misalignment_angle_deg': angle
            })
    
    if not results:
        logger.warning("No valid misalignment angles computed")
        return pd.DataFrame()
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for alignment analysis.
    
    This script:
    1. Loads processed halo shape data from data/processed/halo_shapes.csv
    2. Loads galaxy property data (if available) from data/processed/galaxy_properties.csv
    3. Computes misalignment angles between halo and galaxy pairs
    4. Outputs results to data/processed/alignment_angles.csv
    """
    logger.info("Starting alignment angle computation (T037)")
    
    project_root = get_project_root()
    halo_shapes_path = get_data_processed_path() / 'halo_shapes.csv'
    galaxy_props_path = get_data_processed_path() / 'galaxy_properties.csv'
    output_path = get_data_processed_path() / 'alignment_angles.csv'
    
    # Load halo shapes
    if not halo_shapes_path.exists():
        logger.error(f"Halo shapes file not found: {halo_shapes_path}")
        logger.error("Please run the pipeline (T017) to generate halo_shapes.csv first.")
        return
    
    halo_data = pd.read_csv(halo_shapes_path)
    logger.info(f"Loaded {len(halo_data)} halos from {halo_shapes_path}")
    
    # Check for galaxy properties
    if galaxy_props_path.exists():
        galaxy_data = pd.read_csv(galaxy_props_path)
        logger.info(f"Loaded {len(galaxy_data)} galaxies from {galaxy_props_path}")
    else:
        logger.warning(f"Galaxy properties file not found: {galaxy_props_path}")
        logger.warning("Proceeding with intrinsic halo alignment only (spin vs major axis)")
        galaxy_data = pd.DataFrame()
    
    # If galaxy data exists, compute halo-galaxy misalignment
    if not galaxy_data.empty:
        alignment_results = align_halo_galaxy_pairs(halo_data, galaxy_data)
        if not alignment_results.empty:
            alignment_results.to_csv(output_path, index=False)
            logger.info(f"Saved {len(alignment_results)} alignment records to {output_path}")
        else:
            logger.warning("No alignment results to save")
    else:
        # Fallback: compute intrinsic halo alignment (spin vs major axis)
        # This requires loading raw particle data, which is beyond the scope of this simplified script
        # For now, we log a message and exit
        logger.info("Galaxy data not available. Skipping halo-galaxy alignment computation.")
        logger.info("Note: Full alignment analysis requires raw particle data (positions, velocities).")
        logger.info("This script is designed to work with pre-computed halo and galaxy vectors.")
        logger.info("If you have pre-computed spin and major axis vectors in halo_shapes.csv,")
        logger.info("ensure they are named appropriately (e.g., spin_x, spin_y, spin_z, major_axis_x, etc.)")
        
        # Attempt to compute if vectors are present in halo_data
        if all(col in halo_data.columns for col in ['spin_x', 'spin_y', 'spin_z', 'major_axis_x', 'major_axis_y', 'major_axis_z']):
            logger.info("Detected spin and major axis vectors in halo_shapes.csv. Computing intrinsic alignment.")
            alignment_results = []
            for _, row in halo_data.iterrows():
                spin = np.array([row['spin_x'], row['spin_y'], row['spin_z']])
                major = np.array([row['major_axis_x'], row['major_axis_y'], row['major_axis_z']])
                angle = compute_misalignment_angle(spin, major)
                if not np.isnan(angle):
                    alignment_results.append({
                        'halo_id': row['halo_id'],
                        'misalignment_angle_deg': angle,
                        'alignment_type': 'intrinsic_halo'
                    })
            
            if alignment_results:
                results_df = pd.DataFrame(alignment_results)
                results_df.to_csv(output_path, index=False)
                logger.info(f"Saved {len(results_df)} intrinsic alignment records to {output_path}")
            else:
                logger.warning("No valid intrinsic alignment angles computed")
        else:
            logger.warning("No vector data found in halo_shapes.csv for intrinsic alignment")
            logger.warning("Cannot compute alignment without pre-computed vectors or raw particle data")
    
    logger.info("Alignment angle computation (T037) completed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()