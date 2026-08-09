"""
Descriptors computation module for grain boundary impurity clustering analysis.

Computes:
1. Radial Distribution Function (RDF) peaks within the interface region
2. Pair correlation statistics
3. Voronoi-based neighbor counts in the interface region

Output: data/processed/descriptors.csv
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd

from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import voronoi_volume
from pymatgen.analysis.rdf import InterRDF
from pymatgen.analysis.local_env import VoronoiNN

from config import get_project_root, get_data_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INTERFACE_CUTOFF_A = 5.0  # Ångströms from GB plane to define interface region
RDF_MAX_R = 10.0  # Maximum distance for RDF calculation
RDF_BIN_WIDTH = 0.1  # Bin width for RDF histogram

def get_interface_atoms(structure: Structure, gb_plane_normal: np.ndarray, gb_plane_dist: float) -> List[int]:
    """
    Identify atoms within the interface region of a grain boundary supercell.

    Args:
        structure: The GB supercell structure
        gb_plane_normal: Normal vector of the GB plane
        gb_plane_dist: Distance of the GB plane from origin

    Returns:
        List of atom indices that fall within the interface region
    """
    interface_indices = []
    coords = structure.frac_coords
    lattice = structure.lattice

    # Calculate Cartesian coordinates
    cart_coords = lattice.get_cartesian_coords(coords)

    for i, pos in enumerate(cart_coords):
        # Project position onto the normal vector
        projection = np.dot(pos, gb_plane_normal)
        distance = abs(projection - gb_plane_dist)

        if distance <= INTERFACE_CUTOFF_A:
            interface_indices.append(i)

    return interface_indices

def compute_rdf_peak(structure: Structure, interface_indices: List[int], species: str) -> float:
    """
    Compute the Radial Distribution Function (RDF) peak for a specific species
    within the interface region.

    Args:
        structure: The GB supercell structure
        interface_indices: Indices of atoms in the interface region
        species: The impurity species to analyze (e.g., 'Cr')

    Returns:
        The distance (in Å) of the first major RDF peak
    """
    if not interface_indices:
        logger.warning("No interface atoms found, returning 0.0 for RDF peak")
        return 0.0

    # Get structure subset for interface atoms
    interface_atoms = [structure[i] for i in interface_indices]

    # Filter for the specific species
    target_atoms = [atom for atom in interface_atoms if atom.species_string == species]

    if not target_atoms:
        # If no target species in interface, compute RDF for all interface atoms
        # against the whole structure to find clustering
        ref_atoms = [structure[i] for i in interface_indices]
        rdf = InterRDF(structure, ref_atoms,
                       query_species=[species],
                       nbins=int(RDF_MAX_R / RDF_BIN_WIDTH),
                       r_max=RDF_MAX_R)
    else:
        # Compute RDF of target atoms against all atoms
        rdf = InterRDF(structure, target_atoms,
                       query_species=[species],
                       nbins=int(RDF_MAX_R / RDF_BIN_WIDTH),
                       r_max=RDF_MAX_R)

    rdf.compute()

    # Find the first significant peak (excluding the first bin if it's noise)
    # RDF data is in rdf.rdf array, distances in rdf.r
    rdf_values = rdf.rdf
    distances = rdf.r

    # Skip the first few bins to avoid self-correlation artifacts
    start_idx = max(1, int(1.0 / RDF_BIN_WIDTH))

    if len(rdf_values) <= start_idx:
        logger.warning("RDF data too short to find peak")
        return 0.0

    # Find the first local maximum after the start index
    peak_distance = 0.0
    for i in range(start_idx + 1, len(rdf_values) - 1):
        if rdf_values[i] > rdf_values[i-1] and rdf_values[i] > rdf_values[i+1]:
            # Check if it's a significant peak (above 1.0 or 10% of max)
            if rdf_values[i] > 1.0 or rdf_values[i] > 0.1 * np.max(rdf_values):
                peak_distance = distances[i]
                break

    if peak_distance == 0.0:
        # Fallback to the global maximum if no clear local peak found
        max_idx = np.argmax(rdf_values[start_idx:]) + start_idx
        peak_distance = distances[max_idx]

    return float(peak_distance)

def compute_pair_correlation(structure: Structure, interface_indices: List[int], species: str) -> float:
    """
    Compute pair correlation statistics for the impurity species in the interface region.
    This measures the clustering tendency by calculating the average number of
    impurity-impurity pairs within a defined cutoff.

    Args:
        structure: The GB supercell structure
        interface_indices: Indices of atoms in the interface region
        species: The impurity species to analyze

    Returns:
        Pair correlation coefficient (normalized count of impurity pairs)
    """
    if not interface_indices:
        return 0.0

    interface_atoms = [structure[i] for i in interface_indices]
    target_atoms = [atom for atom in interface_atoms if atom.species_string == species]

    if len(target_atoms) < 2:
        return 0.0

    # Calculate distances between all pairs of target atoms
    cart_coords = [atom.coords for atom in target_atoms]
    n = len(cart_coords)

    # Use a cutoff based on typical bond lengths (e.g., 3.5 Å)
    cutoff = 3.5
    pair_count = 0

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.linalg.norm(np.array(cart_coords[i]) - np.array(cart_coords[j]))
            # Use minimum image convention for periodic boundaries
            dist = structure.lattice.get_distance_and_image(cart_coords[i], cart_coords[j])[0]
            if dist < cutoff:
                pair_count += 1

    # Normalize by the number of possible pairs
    max_pairs = n * (n - 1) / 2
    if max_pairs == 0:
        return 0.0

    return float(pair_count / max_pairs)

def compute_voronoi_neighbor_counts(structure: Structure, interface_indices: List[int], species: str) -> int:
    """
    Compute Voronoi-based neighbor counts for the impurity species in the interface region.
    This counts the average number of neighbors for each impurity atom.

    Args:
        structure: The GB supercell structure
        interface_indices: Indices of atoms in the interface region
        species: The impurity species to analyze

    Returns:
        Average Voronoi neighbor count for the impurity species
    """
    if not interface_indices:
        return 0

    voronoi_nn = VoronoiNN()
    target_indices = [i for i, idx in enumerate(interface_indices)
                     if structure[idx].species_string == species]

    if not target_indices:
        return 0

    neighbor_counts = []

    for idx in target_indices:
        # Get the site index in the full structure
        site_idx = interface_indices[idx]
        site = structure[site_idx]

        try:
            # Get Voronoi neighbors
            neighbors = voronoi_nn.get_nn(structure, site_idx)
            neighbor_counts.append(len(neighbors))
        except Exception as e:
            logger.warning(f"Could not compute Voronoi neighbors for atom {site_idx}: {e}")
            neighbor_counts.append(0)

    if not neighbor_counts:
        return 0

    return int(np.mean(neighbor_counts))

def run_descriptor_computation(structure: Structure, impurity_species: str,
                               gb_plane_normal: np.ndarray, gb_plane_dist: float,
                               alloy_system_id: str) -> Dict[str, Any]:
    """
    Run the full descriptor computation pipeline for a single GB supercell.

    Args:
        structure: The GB supercell structure
        impurity_species: The impurity species (e.g., 'Cr')
        gb_plane_normal: Normal vector of the GB plane
        gb_plane_dist: Distance of the GB plane from origin
        alloy_system_id: Identifier for the alloy system

    Returns:
        Dictionary containing computed descriptors
    """
    logger.info(f"Computing descriptors for {alloy_system_id}")

    # 1. Identify interface atoms
    interface_indices = get_interface_atoms(structure, gb_plane_normal, gb_plane_dist)
    logger.info(f"Found {len(interface_indices)} interface atoms")

    # 2. Compute RDF peak
    rdf_peak = compute_rdf_peak(structure, interface_indices, impurity_species)
    logger.info(f"RDF peak: {rdf_peak:.3f} Å")

    # 3. Compute pair correlation
    pair_corr = compute_pair_correlation(structure, interface_indices, impurity_species)
    logger.info(f"Pair correlation: {pair_corr:.3f}")

    # 4. Compute Voronoi neighbor counts
    voronoi_count = compute_voronoi_neighbor_counts(structure, interface_indices, impurity_species)
    logger.info(f"Voronoi neighbor count: {voronoi_count}")

    return {
        'species': impurity_species,
        'alloy_system_id': alloy_system_id,
        'rdf_peak': rdf_peak,
        'pair_corr': pair_corr,
        'voronoi_count': voronoi_count
    }

def main():
    """
    Main entry point for descriptor computation.
    Reads processed GB supercells from data/processed/, computes descriptors,
    and writes results to data/processed/descriptors.csv.
    """
    project_root = get_project_root()
    data_paths = get_data_paths()

    processed_dir = data_paths['processed']
    output_path = processed_dir / 'descriptors.csv'

    logger.info(f"Starting descriptor computation. Output: {output_path}")

    # Find all GB supercell files
    gb_files = list(processed_dir.glob('gb_supercell_*.cif'))
    if not gb_files:
        logger.error("No GB supercell files found in data/processed/")
        # Create empty output file with headers
        pd.DataFrame(columns=['species', 'alloy_system_id', 'rdf_peak', 'pair_corr', 'voronoi_count']).to_csv(output_path, index=False)
        return

    results = []
    impurity_species = "Cr"  # Default, can be parameterized

    # GB plane parameters (assumed to be along z-axis for simplicity)
    # In a real implementation, these would be read from metadata
    gb_plane_normal = np.array([0, 0, 1])
    gb_plane_dist = 0.0

    for gb_file in gb_files:
        try:
            # Extract alloy system ID from filename
            # Expected format: gb_supercell_<alloy_system_id>.cif
            alloy_id = gb_file.stem.replace('gb_supercell_', '')

            structure = Structure.from_file(gb_file)

            descriptor = run_descriptor_computation(
                structure=structure,
                impurity_species=impurity_species,
                gb_plane_normal=gb_plane_normal,
                gb_plane_dist=gb_plane_dist,
                alloy_system_id=alloy_id
            )
            results.append(descriptor)

        except Exception as e:
            logger.error(f"Failed to process {gb_file}: {e}")
            continue

    if results:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(results)} descriptor records to {output_path}")
    else:
        logger.warning("No descriptors computed. Creating empty output file.")
        pd.DataFrame(columns=['species', 'alloy_system_id', 'rdf_peak', 'pair_corr', 'voronoi_count']).to_csv(output_path, index=False)

if __name__ == "__main__":
    main()
