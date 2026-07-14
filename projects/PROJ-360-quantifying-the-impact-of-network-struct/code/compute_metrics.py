import os
import json
import pickle
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from pymatgen.core import Structure
from pymatgen.io.cif import CifParser
import networkx as nx

# --- Constants ---
DIAGNOSTICS_COMMENT = "# DIAGNOSTICS: Physical descriptors excluded from regression features"
METRICS_CSV_PATH = Path("data/processed/metrics.csv")
NETWORKS_DIR = Path("data/processed/networks")
CIF_DIR = Path("data/raw/cif")

# --- Logging Setup ---
def setup_metrics_logger(name: str = "metrics_logger") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# --- Physical Descriptor Extraction ---
def load_cif_structures(cif_dir: Path) -> Dict[str, Structure]:
    """
    Loads CIF files from the specified directory into pymatgen Structures.
    Returns a dictionary mapping material_id (filename without extension) to Structure.
    """
    structures = {}
    logger = logging.getLogger("metrics_logger")
    
    if not cif_dir.exists():
        logger.error(f"CIF directory not found: {cif_dir}")
        return structures

    for cif_file in cif_dir.glob("*.cif"):
        material_id = cif_file.stem
        try:
            parser = CifParser(str(cif_file))
            # pymatgen might return multiple structures for some CIFs, we take the first
            struct = parser.get_structures()[0]
            structures[material_id] = struct
            logger.debug(f"Loaded structure for {material_id}")
        except Exception as e:
            logger.warning(f"Failed to parse {cif_file.name}: {e}")
    
    return structures

def extract_physical_descriptors(struct: Structure, material_id: str) -> Dict[str, Any]:
    """
    Extracts physical descriptors from a pymatgen Structure.
    Returns a dictionary with:
      - unit_cell_volume
      - total_atom_count
      - mean_atomic_mass
    """
    volume = struct.volume
    atom_count = len(struct)
    
    # Calculate mean atomic mass
    total_mass = sum(site.species.mass for site in struct)
    mean_mass = total_mass / atom_count if atom_count > 0 else 0.0

    return {
        "material_id": material_id,
        "unit_cell_volume": volume,
        "total_atom_count": atom_count,
        "mean_atomic_mass": mean_mass
    }

# --- Metric Computation (Existing Logic Placeholder for Context) ---
def load_graphs_from_directory(networks_dir: Path) -> Dict[str, nx.Graph]:
    graphs = {}
    logger = logging.getLogger("metrics_logger")
    if not networks_dir.exists():
        logger.error(f"Networks directory not found: {networks_dir}")
        return graphs
    
    for pkl_file in networks_dir.glob("*.pkl"):
        material_id = pkl_file.stem
        try:
            with open(pkl_file, 'rb') as f:
                graphs[material_id] = pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load {pkl_file}: {e}")
    return graphs

def compute_metrics_for_graph(graph: nx.Graph, material_id: str) -> Dict[str, Any]:
    """
    Computes network metrics for a graph.
    Returns dict with: material_id, avg_degree, avg_shortest_path, clustering_coeff, density.
    """
    if graph.number_of_nodes() < 2:
        return {
            "material_id": material_id,
            "avg_degree": 0.0,
            "avg_shortest_path": float('nan'),
            "clustering_coeff": 0.0,
            "density": 0.0
        }

    avg_degree = sum(d for n, d in graph.degree()) / graph.number_of_nodes()
    
    # Largest Connected Component for path length
    try:
        lcc = max(nx.connected_components(graph), key=len)
        subgraph = graph.subgraph(lcc)
        lengths = nx.average_shortest_path_length(subgraph)
    except nx.NetworkXError:
        lengths = float('nan')

    clustering = nx.average_clustering(graph)
    density = nx.density(graph)

    return {
        "material_id": material_id,
        "avg_degree": avg_degree,
        "avg_shortest_path": lengths,
        "clustering_coeff": clustering,
        "density": density
    }

# --- Main Logic ---
def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], physical_list: List[Dict[str, Any]], output_path: Path):
    """
    Saves network metrics and physical descriptors to a single CSV file.
    Physical descriptors are appended as extra columns with a header comment.
    """
    if not metrics_list:
        logging.getLogger("metrics_logger").warning("No metrics to save.")
        return

    # Define columns
    network_cols = ["material_id", "avg_degree", "avg_shortest_path", "clustering_coeff", "density"]
    physical_cols = ["unit_cell_volume", "total_atom_count", "mean_atomic_mass"]
    
    # Create a mapping for physical data by material_id
    phys_map = {p["material_id"]: p for p in physical_list}

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header comment
        writer.writerow([DIAGNOSTICS_COMMENT])
        
        # Write header row
        full_header = network_cols + physical_cols
        writer.writerow(full_header)
        
        # Write data rows
        for m in metrics_list:
            mid = m["material_id"]
            row = [m[col] for col in network_cols]
            
            # Append physical descriptors if available
            if mid in phys_map:
                p = phys_map[mid]
                row.append(p["unit_cell_volume"])
                row.append(p["total_atom_count"])
                row.append(p["mean_atomic_mass"])
            else:
                # Fallback for missing physical data
                row.extend([None, None, None])
            
            writer.writerow(row)

def main():
    logger = setup_metrics_logger()
    logger.info("Starting metric computation and physical descriptor extraction.")

    # Load data
    logger.info(f"Loading graphs from {NETWORKS_DIR}...")
    graphs = load_graphs_from_directory(NETWORKS_DIR)
    
    logger.info(f"Loading structures from {CIF_DIR}...")
    structures = load_cif_structures(CIF_DIR)

    # Compute Network Metrics
    metrics_data = []
    for mid, graph in graphs.items():
        metrics = compute_metrics_for_graph(graph, mid)
        metrics_data.append(metrics)

    # Compute Physical Descriptors
    physical_data = []
    for mid, struct in structures.items():
        # Only compute if we have a corresponding graph or just compute all
        # The task implies appending to the metrics CSV, so we match IDs.
        # If a structure exists but no graph, we might still want the physical data,
        # but the CSV structure relies on the metric rows. We'll process all structures.
        phys = extract_physical_descriptors(struct, mid)
        physical_data.append(phys)

    # Save combined results
    logger.info(f"Saving metrics to {METRICS_CSV_PATH}...")
    save_metrics_to_csv(metrics_data, physical_data, METRICS_CSV_PATH)
    
    logger.info("Task T015b completed: Physical descriptors appended to metrics.csv.")

if __name__ == "__main__":
    main()
