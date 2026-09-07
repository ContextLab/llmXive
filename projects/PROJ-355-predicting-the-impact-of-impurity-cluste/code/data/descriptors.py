"""
Descriptor computation module for impurity clustering at grain boundaries.

Computes RDF peaks, pair correlation statistics, and Voronoi-based neighbor counts
specifically within the GB interface region.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.analysis.rdf import RadialDistributionFunction
from pymatgen.analysis.local_env import VoronoiNN
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from config import get_project_root, get_data_paths, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_interface_atoms(
    structure: Structure,
    gb_plane_normal: Tuple[float, float, float] = (0, 0, 1),
    interface_width: float = 5.0
) -> List[int]:
    """
    Identify atoms within the GB interface region.

    Args:
        structure: The GB supercell structure.
        gb_plane_normal: Normal vector of the grain boundary plane.
        interface_width: Width of the interface region in Angstroms (total width).

    Returns:
        List of atom indices within the interface region.
    """
    # Calculate distance of each atom from the GB plane
    # Assuming the GB plane passes through the origin for simplicity
    # In a real implementation, this would use the actual GB plane position
    positions = structure.frac_coords
    lattice = structure.lattice
    cart_coords = lattice.get_cartesian_coords(positions)

    # Project onto the normal vector
    normal = np.array(gb_plane_normal)
    normal = normal / np.linalg.norm(normal)

    # Calculate distances
    distances = np.dot(cart_coords, normal)

    # Find the median distance (approximate GB plane location)
    median_dist = np.median(distances)

    # Select atoms within the interface width
    interface_mask = np.abs(distances - median_dist) <= (interface_width / 2.0)
    interface_indices = np.where(interface_mask)[0].tolist()

    logger.info(f"Identified {len(interface_indices)} interface atoms out of {len(structure)} total atoms")

    return interface_indices

def compute_rdf_peak(
    structure: Structure,
    interface_indices: List[int],
    species: str,
    cutoff: float = 10.0,
    nbins: int = 100
) -> Tuple[float, float]:
    """
    Compute the Radial Distribution Function (RDF) for a specific species
    in the interface region and return the peak position and height.

    Args:
        structure: The full structure.
        interface_indices: Indices of atoms in the interface region.
        species: The impurity species to analyze.
        cutoff: Maximum distance for RDF calculation.
        nbins: Number of bins for RDF.

    Returns:
        Tuple of (peak_position, peak_height).
    """
    if not interface_indices:
        logger.warning("No interface atoms found, returning NaN for RDF")
        return (np.nan, np.nan)

    # Extract interface atoms
    interface_atoms = [structure[i] for i in interface_indices]
    interface_structure = Structure(
        lattice=structure.lattice,
        species=[atom.species for atom in interface_atoms],
        coords=[atom.frac_coords for atom in interface_atoms],
        coords_are_cartesian=False
    )

    # Compute RDF
    try:
        rdf = RadialDistributionFunction()
        rdf.compute_rdf(interface_structure, cutoff, nbins=nbins)

        r_values = rdf.r_values
        g_values = rdf.g_values

        # Find the peak (excluding r=0)
        if len(r_values) > 1:
            peak_idx = np.argmax(g_values[1:]) + 1
            peak_position = r_values[peak_idx]
            peak_height = g_values[peak_idx]
        else:
            peak_position = np.nan
            peak_height = np.nan

        logger.info(f"RDF peak for {species}: position={peak_position:.3f} Å, height={peak_height:.3f}")
        return (peak_position, peak_height)

    except Exception as e:
        logger.error(f"Error computing RDF: {e}")
        return (np.nan, np.nan)

def compute_pair_correlation(
    structure: Structure,
    interface_indices: List[int],
    species: str
) -> float:
    """
    Compute pair correlation statistics for the impurity species in the interface.

    This calculates the fraction of impurity-impurity pairs within a cutoff distance.

    Args:
        structure: The full structure.
        interface_indices: Indices of atoms in the interface region.
        species: The impurity species to analyze.

    Returns:
        Pair correlation coefficient (fraction of impurity pairs).
    """
    if not interface_indices:
        logger.warning("No interface atoms found, returning NaN for pair correlation")
        return np.nan

    interface_atoms = [structure[i] for i in interface_indices]

    # Identify impurity atoms
    impurity_indices = [
        i for i, atom in enumerate(interface_atoms)
        if species in [sp.symbol for sp in atom.species]
    ]

    if len(impurity_indices) < 2:
        logger.info(f"Less than 2 impurity atoms found for {species}, pair correlation = 0")
        return 0.0

    # Calculate distances between all impurity pairs
    impurity_coords = [interface_atoms[i].coords for i in impurity_indices]
    impurity_coords_cart = structure.lattice.get_cartesian_coords(impurity_coords)

    # Count pairs within a cutoff (e.g., 3.5 Å)
    cutoff = 3.5
    pair_count = 0
    total_pairs = len(impurity_indices) * (len(impurity_indices) - 1) / 2

    for i in range(len(impurity_coords_cart)):
        for j in range(i + 1, len(impurity_coords_cart)):
            dist = np.linalg.norm(impurity_coords_cart[i] - impurity_coords_cart[j])
            if dist <= cutoff:
                pair_count += 1

    pair_corr = pair_count / total_pairs if total_pairs > 0 else 0.0
    logger.info(f"Pair correlation for {species}: {pair_corr:.3f} ({pair_count}/{total_pairs} pairs)")

    return pair_corr

def compute_voronoi_neighbor_counts(
    structure: Structure,
    interface_indices: List[int],
    species: str
) -> int:
    """
    Compute Voronoi-based neighbor counts for impurity atoms in the interface.

    Args:
        structure: The full structure.
        interface_indices: Indices of atoms in the interface region.
        species: The impurity species to analyze.

    Returns:
        Average number of neighbors for impurity atoms.
    """
    if not interface_indices:
        logger.warning("No interface atoms found, returning NaN for Voronoi count")
        return np.nan

    interface_atoms = [structure[i] for i in interface_indices]

    # Identify impurity atoms
    impurity_indices = [
        i for i, atom in enumerate(interface_atoms)
        if species in [sp.symbol for sp in atom.species]
    ]

    if not impurity_indices:
        logger.info(f"No impurity atoms found for {species}, Voronoi count = 0")
        return 0

    # Create a local environment analyzer
    voronoi_nn = VoronoiNN()

    neighbor_counts = []
    for idx in impurity_indices:
        atom = interface_atoms[idx]
        try:
            # Get neighbors from the full structure using the atom's position
            # We need to map back to the full structure
            full_idx = interface_indices[idx]
            neighbors = voronoi_nn.get_neighbors(structure, full_idx)
            neighbor_counts.append(len(neighbors))
        except Exception as e:
            logger.warning(f"Error computing Voronoi neighbors for atom {full_idx}: {e}")
            neighbor_counts.append(0)

    avg_neighbors = np.mean(neighbor_counts) if neighbor_counts else 0
    logger.info(f"Average Voronoi neighbors for {species}: {avg_neighbors:.2f}")

    return avg_neighbors

def run_descriptor_computation(
    input_data_path: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main function to run descriptor computation on all GB supercells.

    Args:
        input_data_path: Path to the directory containing GB supercell structures.
        output_path: Path for the output CSV file.

    Returns:
        DataFrame with computed descriptors.
    """
    project_root = get_project_root()
    if input_data_path is None:
        input_data_path = project_root / "data" / "processed" / "gb_supercells"
    if output_path is None:
        output_path = project_root / "data" / "processed" / "descriptors.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get list of structure files
    structure_files = list(input_data_path.glob("*.cif"))
    if not structure_files:
        logger.error(f"No structure files found in {input_data_path}")
        raise FileNotFoundError(f"No structure files found in {input_data_path}")

    logger.info(f"Found {len(structure_files)} structure files to process")

    results = []

    for struct_file in structure_files:
        try:
            # Load structure
            structure = Structure.from_file(struct_file)

            # Extract metadata from filename or structure properties
            # Expected format: bulk_config_id_impurity_species.cif
            filename = struct_file.stem
            parts = filename.rsplit('_', 1)
            if len(parts) == 2:
                bulk_config_id, impurity_species = parts
            else:
                # Fallback: try to extract from structure
                bulk_config_id = filename
                impurity_species = list(set([sp.symbol for atom in structure for sp in atom.species]))[0]

            logger.info(f"Processing {struct_file.name}: bulk_config_id={bulk_config_id}, species={impurity_species}")

            # Get interface atoms
            interface_indices = get_interface_atoms(structure)

            if not interface_indices:
                logger.warning(f"No interface atoms found for {struct_file.name}, skipping")
                continue

            # Compute descriptors
            rdf_peak, _ = compute_rdf_peak(structure, interface_indices, impurity_species)
            pair_corr = compute_pair_correlation(structure, interface_indices, impurity_species)
            voronoi_count = compute_voronoi_neighbor_counts(structure, interface_indices, impurity_species)

            # Store results
            results.append({
                'bulk_config_id': bulk_config_id,
                'species': impurity_species,
                'rdf_peak': rdf_peak,
                'pair_corr': pair_corr,
                'voronoi_count': voronoi_count
            })

        except Exception as e:
            logger.error(f"Error processing {struct_file}: {e}")
            continue

    # Create DataFrame
    df = pd.DataFrame(results)

    if df.empty:
        logger.warning("No descriptors were computed. Creating empty DataFrame.")
        df = pd.DataFrame(columns=['bulk_config_id', 'species', 'rdf_peak', 'pair_corr', 'voronoi_count'])

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")

    return df

def main():
    """Entry point for running descriptor computation."""
    logger.info("Starting descriptor computation...")
    try:
        df = run_descriptor_computation()
        logger.info(f"Successfully computed descriptors for {len(df)} configurations")
        print(f"Descriptors saved to data/processed/descriptors.csv")
        print(df.head())
    except Exception as e:
        logger.error(f"Descriptor computation failed: {e}")
        raise

if __name__ == "__main__":
    main()
