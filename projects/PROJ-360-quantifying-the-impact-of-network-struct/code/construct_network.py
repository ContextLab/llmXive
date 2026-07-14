"""
code/construct_network.py

Constructs atomic network graphs from CIF files using pymatgen and networkx.
Implements covalent radius-based bond detection with fallback mechanisms.
Includes validation to ensure graphs meet minimum node/edge requirements.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import covalent_radius

# Constants
MIN_NODES = 2
MIN_EDGES = 1
COVALENT_TOLERANCE = 0.45  # Angstrom tolerance for bond detection
FALLBACK_CUTOFFS = [3.0, 3.5, 4.0, 4.5, 5.0]  # Angstroms, progressive fallback
MANIFEST_PATH = Path("data/processed/network_manifest.json")
NETWORKS_DIR = Path("data/processed/networks")
CIF_DIR = Path("data/raw/cif")

# Setup logging
logger = logging.getLogger(__name__)


def get_element_covalent_radius(symbol: str) -> float:
    """
    Get the covalent radius for a given element symbol.
    
    Args:
        symbol: Element symbol (e.g., 'C', 'O', 'Fe')
        
    Returns:
        Covalent radius in Angstroms, or 0.0 if not found
    """
    try:
        return covalent_radius(symbol)
    except KeyError:
        logger.warning(f"Covalent radius not found for element {symbol}, using default 1.0")
        return 1.0


def detect_bonds_covalent(structure: Structure, tolerance: float = COVALENT_TOLERANCE) -> List[Tuple[int, int]]:
    """
    Detect bonds based on covalent radii summation.
    
    Args:
        structure: Pymatgen Structure object
        tolerance: Tolerance in Angstroms added to the sum of covalent radii
        
    Returns:
        List of bond tuples (site_index_1, site_index_2)
    """
    bonds = []
    sites = structure.sites
    n_sites = len(sites)
    
    for i in range(n_sites):
        for j in range(i + 1, n_sites):
            site_i = sites[i]
            site_j = sites[j]
            
            # Calculate distance
            dist = site_i.distance(site_j)
            
            # Calculate expected bond length
            radius_i = get_element_covalent_radius(site_i.species_string)
            radius_j = get_element_covalent_radius(site_j.species_string)
            expected_bond_length = radius_i + radius_j + tolerance
            
            if dist <= expected_bond_length:
                bonds.append((i, j))
                
    return bonds


def detect_bonds_fallback(structure: Structure, max_cutoffs: List[float] = FALLBACK_CUTOFFS) -> Tuple[List[Tuple[int, int]], float]:
    """
    Fallback bond detection using progressive distance cutoffs.
    
    Args:
        structure: Pymatgen Structure object
        max_cutoffs: List of distance cutoffs in Angstroms to try progressively
        
    Returns:
        Tuple of (bonds_list, cutoff_used) where cutoff_used is the cutoff that produced edges
        or max_cutoffs[-1] if no edges found even with the largest cutoff
    """
    sites = structure.sites
    n_sites = len(sites)
    
    for cutoff in max_cutoffs:
        bonds = []
        for i in range(n_sites):
            for j in range(i + 1, n_sites):
                dist = sites[i].distance(sites[j])
                if dist <= cutoff:
                    bonds.append((i, j))
        
        if bonds:
            logger.info(f"Fallback bond detection succeeded with cutoff {cutoff} Angstroms, found {len(bonds)} bonds")
            return bonds, cutoff
    
    # If we get here, no bonds found even with the largest cutoff
    logger.warning(f"Fallback bond detection failed even with largest cutoff {max_cutoffs[-1]} Angstroms")
    return [], max_cutoffs[-1]


def construct_network_from_structure(structure: Structure, use_fallback: bool = True) -> Optional[nx.Graph]:
    """
    Construct a networkx Graph from a pymatgen Structure.
    
    Args:
        structure: Pymatgen Structure object
        use_fallback: Whether to use fallback detection if primary method fails
        
    Returns:
        networkx.Graph object if successful, None if validation fails
    """
    # Primary bond detection
    bonds = detect_bonds_covalent(structure)
    
    # If no bonds found and fallback is enabled, try fallback
    if not bonds and use_fallback:
        bonds, _ = detect_bonds_fallback(structure)
    
    # Create graph
    G = nx.Graph()
    
    # Add nodes with site information
    for i, site in enumerate(structure.sites):
        G.add_node(
            i,
            species=site.species_string,
            x=site.coords[0],
            y=site.coords[1],
            z=site.coords[2]
        )
    
    # Add edges
    G.add_edges_from(bonds)
    
    # Validation: Check minimum nodes and edges
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    
    if num_nodes < MIN_NODES:
        logger.error(f"Graph has {num_nodes} nodes, which is less than minimum required {MIN_NODES}. Skipping.")
        return None
        
    if num_edges < MIN_EDGES:
        logger.error(f"Graph has {num_edges} edges, which is less than minimum required {MIN_EDGES}. Skipping.")
        return None
    
    logger.info(f"Successfully constructed network with {num_nodes} nodes and {num_edges} edges")
    return G


def process_cif_file(cif_path: Path) -> Optional[nx.Graph]:
    """
    Process a single CIF file and construct a network graph.
    
    Args:
        cif_path: Path to the CIF file
        
    Returns:
        networkx.Graph object if successful, None if processing fails
    """
    try:
        logger.info(f"Processing CIF file: {cif_path}")
        structure = Structure.from_file(str(cif_path))
        
        graph = construct_network_from_structure(structure, use_fallback=True)
        
        if graph is None:
            logger.warning(f"Skipping {cif_path.name}: validation failed")
            return None
            
        return graph
        
    except Exception as e:
        logger.error(f"Failed to process {cif_path}: {str(e)}")
        return None


def save_graph_to_pickle(graph: nx.Graph, material_id: str, output_dir: Path) -> Path:
    """
    Save a networkx graph to a pickle file.
    
    Args:
        graph: networkx Graph object
        material_id: Material ID for the filename
        output_dir: Directory to save the pickle file
        
    Returns:
        Path to the saved pickle file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{material_id}.pkl"
    
    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)
        
    logger.info(f"Saved graph to {output_path}")
    return output_path


def build_network_manifest(network_files: List[Path], output_path: Path = MANIFEST_PATH) -> None:
    """
    Build a manifest JSON file listing all processed networks.
    
    Args:
        network_files: List of paths to processed network pickle files
        output_path: Path to save the manifest JSON
    """
    manifest = {
        "version": "1.0",
        "created_at": str(Path.cwd()),
        "networks": []
    }
    
    for file_path in network_files:
        manifest["networks"].append({
            "filename": file_path.name,
            "material_id": file_path.stem,
            "path": str(file_path)
        })
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Created network manifest at {output_path}")


def main():
    """
    Main entry point for network construction pipeline.
    
    Processes all CIF files in data/raw/cif/ and constructs network graphs.
    Saves graphs to data/processed/networks/ and generates a manifest.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ensure directories exist
    CIF_DIR.mkdir(parents=True, exist_ok=True)
    NETWORKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Find all CIF files
    cif_files = list(CIF_DIR.glob("*.cif"))
    
    if not cif_files:
        logger.warning(f"No CIF files found in {CIF_DIR}")
        return
    
    logger.info(f"Found {len(cif_files)} CIF files to process")
    
    processed_count = 0
    skipped_count = 0
    processed_paths = []
    
    for cif_file in cif_files:
        graph = process_cif_file(cif_file)
        
        if graph is not None:
            material_id = cif_file.stem
            output_path = save_graph_to_pickle(graph, material_id, NETWORKS_DIR)
            processed_paths.append(output_path)
            processed_count += 1
        else:
            skipped_count += 1
    
    # Build manifest
    if processed_paths:
        build_network_manifest(processed_paths)
    
    logger.info(f"Processing complete. Success: {processed_count}, Skipped: {skipped_count}")


if __name__ == "__main__":
    main()