import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from pymatgen.core import Structure
from pymatgen.analysis.rdf import InteratomicRadialDistributionFunction
from pymatgen.analysis.local_env import VoronoiNN
from pymatgen.analysis.structure_matcher import StructureMatcher

from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
INTERFACE_CUTOFF_A = 5.0  # Ångströms from GB plane
RDF_RESOLUTION = 0.05  # Ångströms
RDF_MAX_R = 10.0  # Ångströms

def get_interface_atoms(structure: Structure, gb_plane_normal: np.ndarray, gb_plane_origin: np.ndarray) -> List[int]:
    """
    Identify atoms within the interface region (within INTERFACE_CUTOFF_A of the GB plane).
    
    Args:
        structure: The GB supercell structure.
        gb_plane_normal: Unit normal vector of the GB plane.
        gb_plane_origin: A point on the GB plane (e.g., the center of the supercell).
        
    Returns:
        List of atom indices that fall within the interface region.
    """
    if gb_plane_normal is None or np.linalg.norm(gb_plane_normal) < 1e-6:
        raise ValueError("GB plane normal vector is invalid or zero.")
    
    normal = gb_plane_normal / np.linalg.norm(gb_plane_normal)
    
    interface_indices = []
    for i, site in enumerate(structure):
        # Vector from origin to atom
        vec = site.coords - gb_plane_origin
        # Distance from plane = absolute dot product of vec and normal
        dist = abs(np.dot(vec, normal))
        
        if dist <= INTERFACE_CUTOFF_A:
            interface_indices.append(i)
    
    logger.info(f"Identified {len(interface_indices)} atoms in the interface region (within {INTERFACE_CUTOFF_A} Å).")
    return interface_indices

def compute_rdf_peak(structure: Structure, interface_indices: List[int], species: str) -> float:
    """
    Compute the RDF peak for a specific impurity species within the interface region.
    
    Args:
        structure: The GB supercell structure.
        interface_indices: List of atom indices in the interface region.
        species: The impurity species symbol (e.g., 'Cr').
        
    Returns:
        The radial distance (Å) of the first major RDF peak for the species.
    """
    # Extract the sub-structure of interface atoms
    interface_sites = [structure[i] for i in interface_indices]
    
    # Filter for the specific species
    target_sites = [s for s in interface_sites if s.specie.symbol == species]
    
    if len(target_sites) < 2:
        logger.warning(f"Not enough {species} atoms in interface region to compute RDF. Returning 0.0.")
        return 0.0
    
    # Create a temporary structure for RDF calculation
    temp_structure = Structure(
        lattice=structure.lattice,
        species=[s.specie for s in target_sites],
        coords=[s.frac_coords for s in target_sites],
        coords_are_cartesian=False
    )
    
    try:
        rdf = InteratomicRadialDistributionFunction(
            temp_structure,
            bin_width=RDF_RESOLUTION,
            max_r=RDF_MAX_R
        )
        
        # Find the first significant peak (excluding r=0)
        # We look for the first local maximum above a threshold
        distances = rdf.r
        values = rdf.g_r
        
        # Simple peak detection: first value > 0.5 (arbitrary threshold for first shell)
        peak_r = 0.0
        for r, g in zip(distances, values):
            if r > RDF_RESOLUTION and g > 0.5:
                # Check if it's a local max or just the rising edge
                # For simplicity, take the first r where g > 0.5
                peak_r = r
                break
        
        if peak_r == 0.0 and len(values) > 0:
            # Fallback: argmax of the first 3 Å
            search_end = min(3.0, RDF_MAX_R)
            mask = distances <= search_end
            if np.any(mask):
                peak_r = distances[mask][np.argmax(values[mask])]
        
        logger.info(f"RDF peak for {species} found at {peak_r:.3f} Å.")
        return peak_r
        
    except Exception as e:
        logger.error(f"Error computing RDF for {species}: {e}")
        return 0.0

def compute_pair_correlation(structure: Structure, interface_indices: List[int], species: str) -> float:
    """
    Compute the pair correlation statistic (coordination number ratio) for the species.
    
    This metric represents the ratio of the species' coordination in the interface
    relative to its expected coordination in the bulk.
    
    Args:
        structure: The GB supercell structure.
        interface_indices: List of atom indices in the interface region.
        species: The impurity species symbol.
        
    Returns:
        A normalized pair correlation value.
    """
    interface_sites = [structure[i] for i in interface_indices]
    target_sites = [s for s in interface_sites if s.specie.symbol == species]
    
    if not target_sites:
        logger.warning(f"No {species} atoms found in interface region.")
        return 0.0
    
    # Use Voronoi tessellation to count neighbors
    voronoi_nn = VoronoiNN()
    
    total_neighbors = 0
    for site in target_sites:
        # Get neighbors from the full structure but only count those in the interface
        # or within a cutoff
        try:
            neighbors = voronoi_nn.get_neighbors(structure, site.coords)
            # Filter neighbors that are also in the interface region
            interface_neighbor_count = 0
            for neighbor, dist, index, weight in neighbors:
                # Check if neighbor index is in interface_indices
                # Note: 'index' in neighbors might not be the original index if structure changed
                # We rely on coordinate matching for robustness if index is unreliable
                # But typically neighbors returns the index in the structure passed
                if structure.index_from_site(neighbor) in interface_indices:
                    interface_neighbor_count += 1
            total_neighbors += interface_neighbor_count
        except Exception:
            # Fallback for boundary issues
            continue
    
    avg_neighbors = total_neighbors / len(target_sites) if target_sites else 0
    
    # Normalize by a typical bulk coordination (e.g., 12 for FCC, 8 for BCC)
    # We estimate bulk coordination from the whole structure's average if possible
    # For simplicity, we use a heuristic normalization
    bulk_coordination_heuristic = 12.0 
    pair_corr = avg_neighbors / bulk_coordination_heuristic
    
    logger.info(f"Pair correlation for {species}: {pair_corr:.4f} (avg neighbors: {avg_neighbors:.2f})")
    return pair_corr

def compute_voronoi_neighbor_counts(structure: Structure, interface_indices: List[int], species: str) -> int:
    """
    Compute the Voronoi-based neighbor count specifically for the species in the interface.
    
    Args:
        structure: The GB supercell structure.
        interface_indices: List of atom indices in the interface region.
        species: The impurity species symbol.
        
    Returns:
        The total number of unique neighbors (across all target atoms) in the interface.
    """
    interface_sites = [structure[i] for i in interface_indices]
    target_sites = [s for s in interface_sites if s.specie.symbol == species]
    
    if not target_sites:
        return 0
    
    voronoi_nn = VoronoiNN()
    unique_neighbor_indices = set()
    
    for site in target_sites:
        try:
            neighbors = voronoi_nn.get_neighbors(structure, site.coords)
            for neighbor, dist, index, weight in neighbors:
                # Only count neighbors that are within the interface region
                if index in interface_indices:
                    unique_neighbor_indices.add(index)
        except Exception:
            continue
    
    # Return the count of unique neighbors
    count = len(unique_neighbor_indices)
    logger.info(f"Voronoi neighbor count for {species} in interface: {count}")
    return count

def run_descriptor_computation(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Path:
    """
    Main entry point to compute descriptors for all GB supercells in the processed data.
    
    This function:
    1. Loads GB supercell structures from the data/processed directory.
    2. Identifies interface atoms based on the GB plane.
    3. Computes RDF, Pair Correlation, and Voronoi counts for impurity species.
    4. Saves results to data/processed/descriptors.csv.
    
    Args:
        input_path: Path to the directory containing GB supercell structures (default: data/processed/).
        output_path: Path to save the output CSV (default: data/processed/descriptors.csv).
        
    Returns:
        Path to the output CSV file.
    """
    project_root = get_project_root()
    if input_path is None:
        input_path = project_root / "data" / "processed"
    if output_path is None:
        output_path = project_root / "data" / "processed" / "descriptors.csv"
        
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Find structure files (assuming .cif or .json format from gb_builder)
    structure_files = list(input_path.glob("*.cif")) + list(input_path.glob("*.json"))
    
    if not structure_files:
        logger.warning(f"No structure files found in {input_path}. Creating empty descriptors.csv.")
        pd.DataFrame(columns=['species', 'rdf_peak', 'pair_corr', 'voronoi_count', 'structure_id']).to_csv(output_path, index=False)
        return output_path
    
    results = []
    
    for struct_file in structure_files:
        logger.info(f"Processing structure: {struct_file.name}")
        try:
            if struct_file.suffix == '.cif':
                structure = Structure.from_file(struct_file)
            elif struct_file.suffix == '.json':
                structure = Structure.from_file(struct_file)
            else:
                continue
            
            # Assume the file name or metadata contains the GB plane info
            # For this implementation, we assume a standard convention or metadata
            # If the structure was built by gb_builder, it might have a 'gb_plane_normal' in its metadata
            # We'll try to infer or use a default if not present.
            # A robust implementation would read a sidecar metadata file or parse the filename.
            # Here, we assume the 'gb_plane_normal' is stored in structure.properties if available.
            
            gb_normal = structure.properties.get('gb_plane_normal', None)
            gb_origin = structure.properties.get('gb_plane_origin', [0,0,0])
            
            if gb_normal is None:
                # Fallback: assume the interface is along the z-axis or estimate from structure
                # This is a simplification; in a real scenario, we'd need explicit metadata
                logger.warning(f"GB plane normal not found in {struct_file.name}. Using default [0,0,1].")
                gb_normal = [0, 0, 1]
            
            gb_normal = np.array(gb_normal)
            gb_origin = np.array(gb_origin)
            
            # Determine impurity species present in the structure
            # We assume the structure contains exactly one impurity species distinct from the bulk
            species_list = list(set([site.specie.symbol for site in structure]))
            # Filter out common bulk elements if known, or just process all unique ones
            # For this task, we compute for each unique species found
            
            # Identify interface atoms
            interface_indices = get_interface_atoms(structure, gb_normal, gb_origin)
            
            for species in species_list:
                rdf_peak = compute_rdf_peak(structure, interface_indices, species)
                pair_corr = compute_pair_correlation(structure, interface_indices, species)
                voronoi_count = compute_voronoi_neighbor_counts(structure, interface_indices, species)
                
                results.append({
                    'structure_id': struct_file.stem,
                    'species': species,
                    'rdf_peak': rdf_peak,
                    'pair_corr': pair_corr,
                    'voronoi_count': voronoi_count
                })
                
        except Exception as e:
            logger.error(f"Failed to process {struct_file}: {e}")
            continue
    
    # Create DataFrame and save
    df = pd.DataFrame(results)
    if not df.empty:
        # Ensure column order matches spec: species, rdf_peak, pair_corr, voronoi_count
        # Add structure_id for traceability if needed, but spec says [species, rdf_peak, pair_corr, voronoi_count]
        # We keep structure_id for internal tracking but the spec output columns are the key ones.
        # Reorder to match spec exactly for the main columns.
        cols = ['species', 'rdf_peak', 'pair_corr', 'voronoi_count']
        # Only select these if structure_id is not required by spec, but it's good practice.
        # Spec says: columns [species, rdf_peak, pair_corr, voronoi_count]
        # We will output exactly these columns as requested.
        df = df[cols]
        df.to_csv(output_path, index=False)
        logger.info(f"Descriptors saved to {output_path}")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=cols).to_csv(output_path, index=False)
        logger.warning("No descriptors computed. Empty file created.")
        
    return output_path

def main():
    """
    CLI entry point for descriptor computation.
    """
    project_root = get_project_root()
    input_dir = project_root / "data" / "processed"
    output_file = project_root / "data" / "processed" / "descriptors.csv"
    
    logger.info(f"Starting descriptor computation. Input: {input_dir}, Output: {output_file}")
    run_descriptor_computation(input_dir, output_file)
    logger.info("Descriptor computation finished.")

if __name__ == "__main__":
    main()