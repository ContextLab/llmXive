import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import get_bonds
import networkx as nx

from utils import setup_logging, pin_seed
from config import get_config

# --- Logging Setup ---
logger = setup_logging("construct_network", "results/construct_network.log")

# --- Constants ---
DEFAULT_TOLERANCE = 0.3  # Angstrom tolerance for covalent bond detection

def get_element_covalent_radius(symbol: str) -> float:
    """
    Retrieve the covalent radius for a given element symbol.
    Uses pymatgen's Element class.
    """
    from pymatgen.core import Element
    try:
        elem = Element(symbol)
        return elem.covalent_radius
    except Exception:
        return 1.5  # Fallback for unknown elements (e.g., organic ligands not in DB)

def detect_bonds_covalent(structure: Structure, tolerance: float = DEFAULT_TOLERANCE) -> List[Tuple[int, int]]:
    """
    Detect bonds based on covalent radii summation.
    Returns a list of (atom_index_1, atom_index_2) tuples.
    """
    bonds = []
    # Use pymatgen's built-in bond detection if available, otherwise implement manual check
    # Note: get_bonds returns a Bond object, but we need indices.
    # Manual implementation for robustness and explicit control:
    for i in range(len(structure)):
        for j in range(i + 1, len(structure)):
            dist = structure.get_distance(i, j)
            r_i = get_element_covalent_radius(structure[i].species_string)
            r_j = get_element_covalent_radius(structure[j].species_string)
            threshold = r_i + r_j + tolerance
            
            if dist < threshold:
                bonds.append((i, j))
    
    return bonds

def detect_bonds_fallback(structure: Structure) -> List[Tuple[int, int]]:
    """
    Fallback bond detection using progressive distance cutoffs if covalent detection fails.
    """
    # Fallback: simple distance cutoff based on average atomic spacing or a fixed large value
    # This is a heuristic to ensure we don't return empty graphs if covalent logic is too strict
    cutoffs = [2.0, 2.5, 3.0, 3.5, 4.0]
    
    for cutoff in cutoffs:
        bonds = []
        for i in range(len(structure)):
            for j in range(i + 1, len(structure)):
                dist = structure.get_distance(i, j)
                if dist < cutoff:
                    bonds.append((i, j))
        if len(bonds) > 0:
            logger.info(f"Fallback bond detection succeeded with cutoff {cutoff}Å. Found {len(bonds)} bonds.")
            return bonds
    
    logger.warning("All fallback bond detection attempts failed. Returning empty bond list.")
    return []

def construct_network_from_structure(structure: Structure) -> nx.Graph:
    """
    Construct a networkx Graph from a pymatgen Structure.
    Nodes are atoms, edges are bonds.
    """
    G = nx.Graph()
    
    # Add nodes with attributes
    for i, site in enumerate(structure):
        G.add_node(i, 
                   species=site.species_string, 
                   coords=site.coords.tolist(),
                   atomic_number=site.species[0].number)
    
    # Detect bonds
    bonds = detect_bonds_covalent(structure)
    
    # If no bonds found, try fallback
    if not bonds:
        bonds = detect_bonds_fallback(structure)
    
    # Add edges
    for i, j in bonds:
        dist = structure.get_distance(i, j)
        G.add_edge(i, j, distance=dist)
    
    return G

def process_cif_file(cif_path: Path, tolerance: float = DEFAULT_TOLERANCE) -> Optional[nx.Graph]:
    """
    Parse a CIF file and construct a network graph.
    Returns None if parsing fails or the structure is invalid.
    """
    try:
        structure = Structure.from_file(cif_path)
        G = construct_network_from_structure(structure)
        
        # Validation: Ensure graph has at least 2 nodes and 1 edge
        if G.number_of_nodes() < 2:
            logger.warning(f"Skipping {cif_path.name}: Graph has fewer than 2 nodes ({G.number_of_nodes()}).")
            return None
        
        if G.number_of_edges() == 0:
            logger.warning(f"Skipping {cif_path.name}: Graph has no edges.")
            return None
        
        return G
    except Exception as e:
        logger.error(f"Failed to process {cif_path.name}: {e}")
        return None

def save_graph_to_pickle(graph: nx.Graph, output_path: Path) -> None:
    """
    Save a networkx graph to a pickle file.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)
    logger.info(f"Saved graph to {output_path}")

def build_network_manifest(graphs_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Build and save the network manifest JSON.
    """
    manifest = {
        "metadata": {
            "generated_at": "dynamic", # Will be replaced by actual timestamp if needed, or left as is for reproducibility
            "source": "construct_network.py",
            "total_graphs": len(graphs_data)
        },
        "graphs": graphs_data
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved network manifest to {output_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Construct atomic networks from CIF files.")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing CIF files.")
    parser.add_argument("--output", type=str, required=True, help="Output directory for pickle files and manifest.")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="Tolerance for covalent bond detection.")
    
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Pin seed for reproducibility
    config = get_config()
    pin_seed(config.seed)
    
    cif_files = list(input_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {input_dir}")
        return
    
    logger.info(f"Found {len(cif_files)} CIF files in {input_dir}")
    
    graphs_data = []
    successful_count = 0
    failed_count = 0
    
    for cif_path in cif_files:
        logger.info(f"Processing {cif_path.name}...")
        graph = process_cif_file(cif_path, args.tolerance)
        
        if graph is not None:
            # Create a safe filename for the pickle
            stem = cif_path.stem
            pickle_path = output_dir / f"{stem}_network.pkl"
            save_graph_to_pickle(graph, pickle_path)
            
            # Record metadata for manifest
            graph_info = {
                "source_file": cif_path.name,
                "output_file": pickle_path.name,
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "is_connected": nx.is_connected(graph) if graph.number_of_nodes() > 0 else False
            }
            graphs_data.append(graph_info)
            successful_count += 1
        else:
            failed_count += 1
    
    # Generate manifest
    manifest_path = output_dir / "network_manifest.json"
    build_network_manifest(graphs_data, manifest_path)
    
    logger.info(f"Completed processing. Success: {successful_count}, Failed: {failed_count}")

if __name__ == "__main__":
    main()
