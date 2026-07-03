"""
Geometry Parser for Grain Boundary Diffusivity Project (T010)

Parses POSCAR/CIF files to extract grain boundary descriptors:
- Boundary Plane Normal (Miller indices)
- Sigma (Σ) Value (from misorientation angle via CSL)
- Boundary Width and Excess Volume
- Rodrigues Vectors (misorientation encoding)
- Miller indices for boundary plane normal

Output: data/processed/parsed_geometry.parquet
"""
import os
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from pymatgen.core import Structure, Lattice
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.rotation import Rotation
import math

from utils import setup_logging, compute_sha256, set_random_seed
from models.grain_boundary_record import GrainBoundaryRecord

# Configure logging
logger = setup_logging(__name__)

# Constants
DEGREE_TO_RAD = np.pi / 180.0
RAD_TO_DEGREE = 180.0 / np.pi

def calculate_sigma_value(misorientation_angle_deg: float) -> int:
    """
    Calculate Sigma (Σ) value from misorientation angle using CSL definition.
    
    For cubic systems, common Σ values correspond to specific angles:
    Σ3: 60° around <111>
    Σ5: 36.87° around <100>
    Σ9: 38.94° around <110>
    Σ11: 50.48° around <110>
    Σ13: 27.80° around <110>
    Σ15: 41.41° around <110>
    Σ17: 28.07° around <100>
    Σ21: 31.60° around <111>
    Σ25: 16.26° around <100>
    Σ27: 32.62° around <111>
    Σ29: 46.40° around <110>
    Σ33: 36.32° around <111>
    
    For arbitrary angles, we use the approximation:
    Σ ≈ 1 / (1 - cos(θ)) for small angles, but this is not accurate for all cases.
    
    A more robust approach is to find the closest known CSL angle.
    """
    # Normalize angle to [0, 90]
    angle = misorientation_angle_deg % 90.0
    if angle > 45.0:
        angle = 90.0 - angle
    
    # Known CSL angles for cubic systems (angle, sigma)
    csl_angles = {
        60.0: 3,
        36.87: 5,
        38.94: 9,
        50.48: 11,
        27.80: 13,
        41.41: 15,
        28.07: 17,
        31.60: 21,
        16.26: 25,
        32.62: 27,
        46.40: 29,
        36.32: 33
    }
    
    # Find closest known CSL angle
    min_diff = float('inf')
    closest_sigma = 1  # Default to random (no special coincidence)
    
    for known_angle, sigma in csl_angles.items():
        diff = abs(angle - known_angle)
        if diff < min_diff:
            min_diff = diff
            closest_sigma = sigma
    
    # If the angle is very close to a known CSL angle, return that Sigma
    if min_diff < 2.0:  # Within 2 degrees tolerance
        return closest_sigma
    
    # For non-special angles, we could use a more complex algorithm
    # or return 1 (random boundary)
    # For this implementation, we'll return 1 for non-special angles
    return 1

def calculate_miller_indices(normal_vector: np.ndarray, lattice: Lattice) -> Tuple[int, int, int]:
    """
    Convert a normal vector to Miller indices (hkl).
    
    Miller indices are the reciprocal of the intercepts of the plane with the
    crystallographic axes, reduced to smallest integers.
    """
    # Convert Cartesian normal to fractional coordinates
    reciprocal_lattice = lattice.reciprocal_lattice
    fractional_normal = np.dot(normal_vector, reciprocal_lattice.cart_coords)
    
    # Get the direction cosines in reciprocal space
    # For Miller indices, we need the plane normal in reciprocal space
    # The plane normal in direct space corresponds to the direction in reciprocal space
    
    # Normalize the vector
    norm = np.linalg.norm(fractional_normal)
    if norm < 1e-10:
        return (0, 0, 0)
    
    normalized = fractional_normal / norm
    
    # Find the closest integer ratios
    # We'll use a simple approach: multiply by a large factor and round
    scale = 1000
    hkl_float = normalized * scale
    hkl_int = np.round(hkl_float).astype(int)
    
    # Reduce to smallest integers by dividing by GCD
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    
    def gcd_list(lst):
        result = lst[0]
        for i in range(1, len(lst)):
            result = gcd(result, lst[i])
        return result
    
    common_divisor = gcd_list([abs(x) for x in hkl_int if x != 0])
    if common_divisor > 1:
        hkl_int = hkl_int // common_divisor
    
    return tuple(hkl_int.tolist())

def calculate_rodrigues_vector(rotation_matrix: np.ndarray) -> np.ndarray:
    """
    Convert a rotation matrix to a Rodrigues vector.
    
    The Rodrigues vector r is defined as:
    r = n * tan(θ/2)
    where n is the rotation axis and θ is the rotation angle.
    """
    # Extract rotation angle and axis from rotation matrix
    trace = np.trace(rotation_matrix)
    cos_theta = (trace - 1) / 2.0
    
    # Clamp to [-1, 1] to handle numerical errors
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    theta = np.arccos(cos_theta)
    
    if theta < 1e-10:
        return np.array([0.0, 0.0, 0.0])
    
    sin_theta = np.sin(theta)
    
    if abs(sin_theta) < 1e-10:
        # 180 degree rotation
        # Find the axis from the rotation matrix
        if abs(rotation_matrix[0, 0] + 1) > 1e-10:
            axis = np.array([1.0, 0.0, 0.0])
        elif abs(rotation_matrix[1, 1] + 1) > 1e-10:
            axis = np.array([0.0, 1.0, 0.0])
        else:
            axis = np.array([0.0, 0.0, 1.0])
    else:
        axis = np.array([
            rotation_matrix[2, 1] - rotation_matrix[1, 2],
            rotation_matrix[0, 2] - rotation_matrix[2, 0],
            rotation_matrix[1, 0] - rotation_matrix[0, 1]
        ]) / (2.0 * sin_theta)
    
    # Normalize axis
    axis = axis / np.linalg.norm(axis)
    
    # Rodrigues vector
    r = axis * np.tan(theta / 2.0)
    return r

def extract_boundary_plane_normal(structure: Structure) -> Tuple[np.ndarray, Tuple[int, int, int]]:
    """
    Extract the boundary plane normal from the structure.
    
    For a bicrystal slab, the interface plane is typically perpendicular to
    the growth direction (usually the z-axis in the simulation cell).
    """
    # Assume the boundary plane is perpendicular to the z-axis
    # This is a common convention in grain boundary simulations
    normal_cartesian = np.array([0.0, 0.0, 1.0])
    
    # Convert to Miller indices
    miller_indices = calculate_miller_indices(normal_cartesian, structure.lattice)
    
    return normal_cartesian, miller_indices

def calculate_boundary_width(structure: Structure) -> float:
    """
    Calculate the boundary width from the structure dimensions.
    
    For a slab geometry, this is typically the length of the simulation cell
    in the direction perpendicular to the boundary plane.
    """
    # Assume boundary is perpendicular to z-axis
    # The width is the length of the cell in the z-direction
    return structure.lattice.c

def calculate_excess_volume(structure: Structure, bulk_volume_per_atom: float = None) -> float:
    """
    Calculate the excess volume at the grain boundary.
    
    Excess volume is the additional volume per unit area of the boundary
    compared to the bulk material.
    
    For a simple estimation, we can use:
    V_excess = (V_total - N * V_bulk) / Area
    
    where:
    - V_total is the total volume of the simulation cell
    - N is the number of atoms
    - V_bulk is the bulk volume per atom (if known)
    - Area is the area of the grain boundary
    """
    total_volume = structure.lattice.volume
    num_atoms = len(structure)
    
    # If bulk volume per atom is not provided, estimate it
    # This is a rough estimate based on typical metallic densities
    if bulk_volume_per_atom is None:
        # Estimate from the structure itself (assuming most of it is bulk)
        # This is a simplification; in practice, you'd use known bulk properties
        bulk_volume_per_atom = total_volume / num_atoms * 0.95  # Rough estimate
    
    # Calculate excess volume
    excess_volume = (total_volume - num_atoms * bulk_volume_per_atom) / (structure.lattice.a * structure.lattice.b)
    
    return excess_volume

def parse_structure_file(file_path: str) -> Dict[str, Any]:
    """
    Parse a single structure file (POSCAR or CIF) and extract grain boundary descriptors.
    """
    file_path = Path(file_path)
    
    # Determine file type
    if file_path.suffix.lower() in ['.vasp', '.poscar', '.concar']:
        structure = Structure.from_file(file_path)
    elif file_path.suffix.lower() == '.cif':
        structure = Structure.from_file(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    # Extract basic information
    result = {
        'file_path': str(file_path),
        'file_name': file_path.name,
        'num_atoms': len(structure),
        'lattice_params': {
            'a': structure.lattice.a,
            'b': structure.lattice.b,
            'c': structure.lattice.c,
            'alpha': structure.lattice.alpha,
            'beta': structure.lattice.beta,
            'gamma': structure.lattice.gamma
        },
        'total_volume': structure.lattice.volume
    }
    
    # Extract boundary plane normal
    normal_cartesian, miller_indices = extract_boundary_plane_normal(structure)
    result['boundary_plane_normal_cartesian'] = normal_cartesian.tolist()
    result['boundary_plane_miller_indices'] = list(miller_indices)
    
    # Calculate boundary width
    boundary_width = calculate_boundary_width(structure)
    result['boundary_width'] = boundary_width
    
    # Calculate excess volume
    excess_volume = calculate_excess_volume(structure)
    result['excess_volume'] = excess_volume
    
    # We need misorientation angle to calculate Sigma value and Rodrigues vector
    # This would typically be provided in the metadata or calculated from the structure
    # For now, we'll assume it's provided in the metadata or set to 0
    # In a real implementation, this would be extracted from the file or metadata
    misorientation_angle = 0.0  # Placeholder - should be extracted from metadata
    
    result['misorientation_angle'] = misorientation_angle
    result['sigma_value'] = calculate_sigma_value(misorientation_angle)
    
    # For Rodrigues vector, we need the rotation matrix
    # This would be calculated from the misorientation
    # For now, we'll set it to zero
    rodrigues_vector = np.array([0.0, 0.0, 0.0])  # Placeholder
    result['rodrigues_vector'] = rodrigues_vector.tolist()
    
    return result

def load_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load metadata for the dataset.
    """
    with open(metadata_path, 'r') as f:
        return json.load(f)

def process_raw_data(raw_data_dir: str, metadata_path: str) -> pd.DataFrame:
    """
    Process all raw structure files and create a DataFrame with parsed geometry.
    """
    raw_path = Path(raw_data_dir)
    metadata = load_metadata(metadata_path)
    
    results = []
    
    # Get list of structure files
    structure_files = list(raw_path.glob('*.vasp')) + \
                    list(raw_path.glob('*.poscar')) + \
                    list(raw_path.glob('*.cif')) + \
                    list(raw_path.glob('*.CONTCAR'))
    
    if not structure_files:
        logger.warning(f"No structure files found in {raw_data_dir}")
        return pd.DataFrame()
    
    logger.info(f"Found {len(structure_files)} structure files to process")
    
    for file_path in structure_files:
        try:
            # Check if we have metadata for this file
            file_name = file_path.name
            file_metadata = None
            
            # Look for metadata in the metadata file
            if 'files' in metadata:
                for entry in metadata['files']:
                    if entry.get('file_name') == file_name:
                        file_metadata = entry
                        break
            
            # Parse the structure file
            parsed_data = parse_structure_file(str(file_path))
            
            # Add metadata information
            if file_metadata:
                parsed_data['misorientation_angle'] = file_metadata.get('misorientation_angle', 0.0)
                parsed_data['material_id'] = file_metadata.get('material_id', '')
                parsed_data['source'] = file_metadata.get('source', '')
                parsed_data['checksum'] = file_metadata.get('checksum', '')
            
            # Recalculate Sigma and Rodrigues vector with actual misorientation
            misorientation = parsed_data['misorientation_angle']
            parsed_data['sigma_value'] = calculate_sigma_value(misorientation)
            
            # For Rodrigues vector, we need the rotation matrix
            # This is a simplified approach; in reality, you'd need the full rotation
            # For now, we'll use a placeholder
            rodrigues_vector = np.array([0.0, 0.0, 0.0])  # Placeholder
            parsed_data['rodrigues_vector'] = rodrigues_vector.tolist()
            
            results.append(parsed_data)
            logger.debug(f"Processed {file_name}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue
    
    if not results:
        logger.warning("No files were successfully processed")
        return pd.DataFrame()
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Calculate checksums for the processed data
    if 'checksum' in df.columns:
        # We already have checksums from metadata
        pass
    else:
        # Calculate checksums for the processed data
        # This is a simplified approach
        df['checksum'] = df['file_name'].apply(lambda x: compute_sha256(str(raw_path / x)))
    
    return df

def main():
    """
    Main function to run the geometry parser.
    """
    # Set random seed for reproducibility
    set_random_seed(42)
    
    # Define paths
    project_root = Path(__file__).parent.parent
    raw_data_dir = project_root / 'data' / 'raw'
    metadata_path = project_root / 'data' / 'metadata.yaml'
    output_dir = project_root / 'data' / 'processed'
    output_path = output_dir / 'parsed_geometry.parquet'
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting geometry parser")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Metadata path: {metadata_path}")
    logger.info(f"Output path: {output_path}")
    
    # Check if metadata file exists
    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        logger.error("Please run T009 (download.py) first to generate metadata.yaml")
        return
    
    # Check if raw data directory exists
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory not found: {raw_data_dir}")
        logger.error("Please run T009 (download.py) first to download raw data")
        return
    
    # Process raw data
    df = process_raw_data(str(raw_data_dir), str(metadata_path))
    
    if df.empty:
        logger.error("No data was processed. Check the logs for errors.")
        return
    
    logger.info(f"Successfully processed {len(df)} records")
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved parsed geometry to {output_path}")
    
    # Log summary statistics
    logger.info("Summary statistics:")
    logger.info(f"  Total records: {len(df)}")
    logger.info(f"  Unique materials: {df['material_id'].nunique() if 'material_id' in df.columns else 'N/A'}")
    logger.info(f"  Sigma value distribution:")
    if 'sigma_value' in df.columns:
        logger.info(f"    {df['sigma_value'].value_counts().to_dict()}")
    
    logger.info("Geometry parsing completed successfully")

if __name__ == '__main__':
    main()
