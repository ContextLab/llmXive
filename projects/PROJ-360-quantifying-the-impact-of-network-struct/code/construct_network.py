"""
Network construction module for crystalline solids.
Parses CIF files and constructs atomic network graphs.
"""

import os
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import networkx as nx
from pymatgen.core import Structure
from pymatgen.analysis.local_env import CovalentBond
from pymatgen.analysis.bond_valence import BVAnalyzer

from utils import setup_logging, retry_with_exponential_backoff

# Configure logger for this module
logger = setup_logging("construct_network", "results/construct_network.log")


def get_element_covalent_radius(element_symbol: str) -> float:
    """
    Retrieve the covalent radius for a given element symbol.
    Uses pymatgen's Element class.
    """
    from pymatgen.core.periodic_table import Element
    try:
        elem = Element(element_symbol)
        return elem.covalent_radius
    except Exception as e:
        logger.warning(f"Could not retrieve covalent radius for {element_symbol}: {e}")
        return 0.0


def detect_bonds_covalent(structure: Structure, tolerance: float = 0.4) -> List[Tuple[int, int]]:
    """
    Detect bonds in a structure based on covalent radii summation.
    
    Args:
        structure: pymatgen Structure object
        tolerance: Tolerance factor added to sum of covalent radii
        
    Returns:
        List of (site_index_1, site_index_2) tuples representing bonds
    """
    bonds = []
    sites = structure.sites
    n_sites = len(sites)
    
    for i in range(n_sites):
        for j in range(i + 1, n_sites):
            site_i = sites[i]
            site_j = sites[j]
            
            dist = structure.get_distance(i, j)
            radius_i = get_element_covalent_radius(site_i.specie.symbol)
            radius_j = get_element_covalent_radius(site_j.specie.symbol)
            
            sum_radii = radius_i + radius_j
            
            # If distance is within tolerance of sum of radii, consider it a bond
            if dist < (sum_radii * (1 + tolerance)) and dist > 0.5: # Avoid zero-distance artifacts
                bonds.append((i, j))
                
    return bonds


def detect_bonds_fallback(structure: Structure, max_cutoff: float = 3.5, step: float = 0.1) -> List[Tuple[int, int]]:
    """
    Fallback bond detection using progressive distance cutoffs.
    Used when covalent radius method fails to produce a connected graph.
    
    Args:
        structure: pymatgen Structure object
        max_cutoff: Maximum distance cutoff to try
        step: Increment step for cutoff
        
    Returns:
        List of (site_index_1, site_index_2) tuples representing bonds
    """
    sites = structure.sites
    n_sites = len(sites)
    
    cutoff = 2.0 # Start with a reasonable lower bound
    bonds = []
    
    while cutoff <= max_cutoff:
        bonds = []
        for i in range(n_sites):
            for j in range(i + 1, n_sites):
                dist = structure.get_distance(i, j)
                if dist < cutoff and dist > 0.5:
                    bonds.append((i, j))
        
        # Check if graph is connected (or has significant edges)
        if len(bonds) > 0:
            # Simple heuristic: if we have enough edges, stop increasing cutoff
            # For a graph with N nodes, a tree has N-1 edges. We want at least that.
            if len(bonds) >= n_sites - 1:
                break
        
        cutoff += step
        
    return bonds


def construct_network_from_structure(structure: Structure, use_fallback: bool = False) -> Optional[nx.Graph]:
    """
    Construct a networkx Graph from a pymatgen Structure.
    
    Args:
        structure: pymatgen Structure object
        use_fallback: Whether to use fallback method if covalent method fails
        
    Returns:
        networkx Graph object or None if construction fails
    """
    try:
        # Try covalent radius method first
        bonds = detect_bonds_covalent(structure)
        
        # Check if we have a valid graph
        if len(bonds) == 0:
            logger.warning(f"No bonds detected with covalent method. Trying fallback...")
            if use_fallback:
                bonds = detect_bonds_fallback(structure)
            else:
                return None
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes with attributes
        for i, site in enumerate(structure.sites):
            G.add_node(i, 
                       element=site.specie.symbol, 
                       coords=site.coords.tolist(),
                       mass=site.specie.mass)
        
        # Add edges
        for u, v in bonds:
            # Calculate distance for edge attribute
            dist = structure.get_distance(u, v)
            G.add_edge(u, v, distance=dist)
        
        # VALIDATION: Ensure graph has at least 2 nodes and 1 edge
        if G.number_of_nodes() < 2:
            logger.warning(f"Graph for {structure.formula} has < 2 nodes ({G.number_of_nodes()}). Skipping.")
            return None
            
        if G.number_of_edges() < 1:
            logger.warning(f"Graph for {structure.formula} has < 1 edge ({G.number_of_edges()}). Skipping.")
            return None
        
        return G
        
    except Exception as e:
        logger.error(f"Failed to construct network from structure: {e}")
        return None


def process_cif_file(cif_path: Path) -> Optional[Tuple[nx.Graph, Dict[str, Any]]]:
    """
    Process a single CIF file and construct its network.
    
    Args:
        cif_path: Path to the CIF file
        
    Returns:
        Tuple of (Graph, metadata_dict) or None if processing fails
    """
    try:
        structure = Structure.from_file(str(cif_path))
        
        # Construct network
        G = construct_network_from_structure(structure, use_fallback=True)
        
        if G is None:
            return None
        
        # Create metadata
        metadata = {
            "material_id": cif_path.stem,
            "formula": structure.formula,
            "num_sites": len(structure.sites),
            "num_bonds": G.number_of_edges(),
            "num_nodes": G.number_of_nodes(),
            "lattice_params": structure.lattice.parameters,
            "source_file": str(cif_path)
        }
        
        return G, metadata
        
    except Exception as e:
        logger.error(f"Error processing CIF file {cif_path}: {e}")
        return None


def save_graph_to_pickle(graph: nx.Graph, metadata: Dict[str, Any], output_path: Path) -> bool:
    """
    Save a graph and its metadata to a pickle file.
    
    Args:
        graph: networkx Graph object
        metadata: Dictionary of metadata
        output_path: Path to save the pickle file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "graph": graph,
            "metadata": metadata
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Saved graph to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save graph to {output_path}: {e}")
        return False


def build_network_manifest(graphs_data: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Build a manifest JSON file containing metadata for all processed graphs.
    
    Args:
        graphs_data: List of dictionaries containing graph metadata
        output_path: Path to save the manifest JSON
        
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "version": "1.0",
            "generated_at": str(Path(output_path).parent), # Placeholder for timestamp
            "total_graphs": len(graphs_data),
            "graphs": graphs_data
        }
        
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Saved manifest to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save manifest to {output_path}: {e}")
        return False


def main():
    """
    Main entry point for constructing networks from CIF files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Construct atomic networks from CIF files")
    parser.add_argument("--input", type=str, required=True, help="Input directory containing CIF files")
    parser.add_argument("--output", type=str, required=True, help="Output directory for graph pickle files")
    args = parser.parse_args()
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1
    
    # Find all CIF files
    cif_files = list(input_dir.glob("*.cif"))
    if not cif_files:
        logger.error(f"No CIF files found in {input_dir}")
        return 1
    
    logger.info(f"Found {len(cif_files)} CIF files to process")
    
    graphs_data = []
    success_count = 0
    skip_count = 0
    
    for cif_file in cif_files:
        logger.info(f"Processing {cif_file.name}...")
        
        result = process_cif_file(cif_file)
        
        if result is None:
            skip_count += 1
            continue
        
        graph, metadata = result
        
        # Save graph
        output_file = output_dir / f"{cif_file.stem}.pkl"
        if save_graph_to_pickle(graph, metadata, output_file):
            graphs_data.append(metadata)
            success_count += 1
        else:
            skip_count += 1
    
    # Build manifest
    manifest_path = output_dir / "network_manifest.json"
    if graphs_data:
        build_network_manifest(graphs_data, manifest_path)
    else:
        logger.warning("No graphs were successfully processed. Manifest not created.")
    
    logger.info(f"Processing complete. Success: {success_count}, Skipped: {skip_count}")
    
    return 0


if __name__ == "__main__":
    exit(main())