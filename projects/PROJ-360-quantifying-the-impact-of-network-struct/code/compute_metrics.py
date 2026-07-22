import os
import json
import pickle
import logging
import csv
import math
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx
import numpy as np
from pymatgen.core import Structure
from pymatgen.analysis.structure_analyzer import get_bonding_strategy

# Import shared utilities
from config import Config, get_config
from utils import setup_logging, retry_with_exponential_backoff

def setup_metrics_logger(name: str = "network_metrics") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = setup_metrics_logger()

def load_graphs_from_directory(graph_dir: str) -> Dict[str, nx.Graph]:
    """Load all graph pickles from the specified directory."""
    graphs = {}
    path = Path(graph_dir)
    if not path.exists():
        logger.error(f"Graph directory not found: {graph_dir}")
        return graphs
    
    for p_file in path.glob("*.pkl"):
        try:
            with open(p_file, 'rb') as f:
                graph_data = pickle.load(f)
                # Assuming the file structure stores material_id in the graph object or filename
                # If graph object has 'material_id' attribute or key, use it, otherwise derive from filename
                if isinstance(graph_data, dict) and 'material_id' in graph_data:
                    mat_id = graph_data['material_id']
                    graphs[mat_id] = graph_data['graph']
                else:
                    # Fallback to filename if structure is just the graph
                    mat_id = p_file.stem
                    graphs[mat_id] = graph_data
            logger.info(f"Loaded graph: {mat_id}")
        except Exception as e:
            logger.error(f"Failed to load {p_file}: {e}")
    return graphs

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the manifest JSON containing material metadata."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest not found at {manifest_path}, returning empty dict.")
        return {}
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {}

def get_thermal_conductivity_scalar(material_data: Dict[str, Any]) -> Optional[float]:
    """
    Extract thermal conductivity scalar from material data.
    Calculates mean of k_xx, k_yy, k_zz.
    """
    if not material_data:
        return None
    
    # Try to find thermal conductivity in various expected locations
    thermal_cond = material_data.get('thermal_conductivity', {})
    if not thermal_cond:
        # Check if keys are at top level
        k_xx = material_data.get('k_xx')
        k_yy = material_data.get('k_yy')
        k_zz = material_data.get('k_zz')
    else:
        k_xx = thermal_cond.get('k_xx')
        k_yy = thermal_cond.get('k_yy')
        k_zz = thermal_cond.get('k_zz')
    
    if k_xx is None or k_yy is None or k_zz is None:
        return None
    
    try:
        scalar = float(k_xx + k_yy + k_zz) / 3.0
        # Verify consistency
        if abs(scalar - (float(k_xx) + float(k_yy) + float(k_zz)) / 3.0) > 1e-6:
            logger.warning(f"Thermal conductivity calculation mismatch for {material_data.get('material_id')}")
        return scalar
    except (ValueError, TypeError):
        return None

def compute_physical_descriptors(cif_path: str) -> Dict[str, float]:
    """
    Calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass.
    Logs these values to results/power_analysis.log.
    Returns a dict for logging, NOT for metrics.csv.
    """
    try:
        structure = Structure.from_file(cif_path)
        volume = structure.lattice.volume
        atom_count = len(structure)
        total_mass = sum(site.species.weight for site in structure)
        mean_mass = total_mass / atom_count if atom_count > 0 else 0.0
        
        descriptors = {
            "unit_cell_volume": volume,
            "atom_count": atom_count,
            "mean_atomic_mass": mean_mass
        }
        
        # Log to power_analysis.log
        log_path = Path("results/power_analysis.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(f"Material: {Path(cif_path).stem}\n")
            f.write(f"  Volume: {volume:.4f} Ang^3\n")
            f.write(f"  Atom Count: {atom_count}\n")
            f.write(f"  Mean Atomic Mass: {mean_mass:.4f} amu\n")
            f.write("-" * 40 + "\n")
        
        return descriptors
    except Exception as e:
        logger.warning(f"Could not compute physical descriptors for {cif_path}: {e}")
        return {"unit_cell_volume": 0.0, "atom_count": 0, "mean_atomic_mass": 0.0}

def compute_metrics_for_graph(graph: nx.Graph, material_id: str) -> Dict[str, Any]:
    """
    Compute network metrics for a single graph.
    Handles disconnected graphs by reporting NaN for path length.
    Computes network density as a diagnostic.
    """
    if graph.number_of_nodes() < 2:
        logger.warning(f"Graph {material_id} has fewer than 2 nodes. Skipping metrics.")
        return {
            "material_id": material_id,
            "avg_degree": 0.0,
            "path_length": float('nan'),
            "clustering": 0.0,
            "density": 0.0,
            "is_connected": False,
            "num_nodes": graph.number_of_nodes(),
            "num_edges": graph.number_of_edges()
        }

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()
    
    # Average Degree
    degrees = [d for n, d in graph.degree()]
    avg_degree = sum(degrees) / num_nodes if num_nodes > 0 else 0.0

    # Density
    density = num_edges / (num_nodes * (num_nodes - 1) / 2) if num_nodes > 1 else 0.0

    # Largest Connected Component (LCC) for path length
    if not nx.is_connected(graph):
        try:
            largest_cc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(largest_cc)
            lcc_nodes = len(largest_cc)
            
            if lcc_nodes > 1:
                # Average shortest path length on LCC
                try:
                    path_length = nx.average_shortest_path_length(subgraph)
                except nx.NetworkXError:
                    path_length = float('nan')
            else:
                path_length = float('nan')
        except Exception:
            path_length = float('nan')
        
        is_connected = False
    else:
        try:
            path_length = nx.average_shortest_path_length(graph)
        except nx.NetworkXError:
            path_length = float('nan')
        is_connected = True
        lcc_nodes = num_nodes

    # Clustering Coefficient
    try:
        clustering = nx.average_clustering(graph)
    except Exception:
        clustering = 0.0

    return {
        "material_id": material_id,
        "avg_degree": avg_degree,
        "path_length": path_length,
        "clustering": clustering,
        "density": density,
        "is_connected": is_connected,
        "num_nodes": num_nodes,
        "num_edges": num_edges,
        "lcc_size": lcc_nodes
    }

def update_metadata_yaml(cif_dir: str, graph_dir: str, metadata_path: str):
    """
    Update data/metadata.yaml with checksums for CIFs and graphs.
    This is a simplified version; in a real scenario, we'd load the existing YAML.
    """
    import yaml
    from datetime import datetime

    metadata = {
        "snapshot_timestamp": datetime.now().isoformat(),
        "derivation": "CIF -> Network via covalent radii + fallback",
        "artifacts": {
            "cif_files": [],
            "graph_files": []
        }
    }

    # Compute checksums for CIFs
    cif_path = Path(cif_dir)
    if cif_path.exists():
        for f in cif_path.glob("*.cif"):
            with open(f, 'rb') as file:
                sha256 = hashlib.sha256(file.read()).hexdigest()
            metadata["artifacts"]["cif_files"].append({"file": str(f), "sha256": sha256})

    # Compute checksums for graphs
    graph_path = Path(graph_dir)
    if graph_path.exists():
        for f in graph_path.glob("*.pkl"):
            with open(f, 'rb') as file:
                sha256 = hashlib.sha256(file.read()).hexdigest()
            metadata["artifacts"]["graph_files"].append({"file": str(f), "sha256": sha256})

    # Write to temp file then atomic rename
    temp_path = metadata_path + ".tmp"
    with open(temp_path, 'w') as f:
        yaml.dump(metadata, f)
    os.replace(temp_path, metadata_path)
    logger.info(f"Updated metadata at {metadata_path}")

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str):
    """Save metrics to CSV."""
    if not metrics_list:
        logger.warning("No metrics to save. CSV will be empty.")
        # Ensure file is created even if empty
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["material_id", "avg_degree", "path_length", "clustering", "density", "is_connected", "num_nodes", "num_edges", "lcc_size"])
        return

    fieldnames = ["material_id", "avg_degree", "path_length", "clustering", "density", "is_connected", "num_nodes", "num_edges", "lcc_size"]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in metrics_list:
            # Handle NaN for CSV
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    clean_row[k] = ""
                else:
                    clean_row[k] = v
            writer.writerow(clean_row)
    logger.info(f"Saved {len(metrics_list)} metrics to {output_path}")

def log_physical_descriptors(descriptors: Dict[str, float], material_id: str):
    """Log physical descriptors to power_analysis.log."""
    log_path = Path("results/power_analysis.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"Material: {material_id}\n")
        f.write(f"  Volume: {descriptors.get('unit_cell_volume', 0):.4f}\n")
        f.write(f"  Atom Count: {descriptors.get('atom_count', 0)}\n")
        f.write(f"  Mean Atomic Mass: {descriptors.get('mean_atomic_mass', 0):.4f}\n")
        f.write("-" * 40 + "\n")

def main():
    """Main entry point for computing metrics."""
    # Configuration
    config = get_config()
    graph_dir = config.get('GRAPH_DIR', 'data/processed/networks')
    manifest_path = config.get('MANIFEST_PATH', 'data/processed/networks/manifest.json')
    output_csv = config.get('METRICS_CSV', 'data/processed/metrics.csv')
    cif_dir = config.get('CIF_DIR', 'data/raw/cif')
    metadata_path = config.get('METADATA_PATH', 'data/metadata.yaml')

    logger.info(f"Starting metrics computation from {graph_dir}")

    # Load graphs
    graphs = load_graphs_from_directory(graph_dir)
    if not graphs:
        logger.error("No graphs found. Exiting.")
        return

    # Load manifest for thermal conductivity
    manifest = load_manifest(manifest_path)
    
    # Process each graph
    metrics_list = []
    skipped_count = 0

    for mat_id, graph in graphs.items():
        # Compute network metrics
        metrics = compute_metrics_for_graph(graph, mat_id)
        
        # Compute physical descriptors (logging only)
        cif_file = Path(cif_dir) / f"{mat_id}.cif"
        if cif_file.exists():
            phys_desc = compute_physical_descriptors(str(cif_file))
            log_physical_descriptors(phys_desc, mat_id)
        else:
            logger.warning(f"CIF file not found for {mat_id}, skipping physical descriptors.")

        # Append thermal conductivity scalar if available
        material_data = manifest.get('materials', {}).get(mat_id, {})
        if not material_data:
            # Fallback: check if manifest is structured differently
            # Some manifests might be a list or have different keys
            pass 
        
        thermal_scalar = get_thermal_conductivity_scalar(material_data)
        if thermal_scalar is not None:
            metrics['thermal_conductivity_scalar'] = thermal_scalar
        else:
            # If missing, we still save the row but without the thermal column (or with NaN)
            # The task T015 handles appending the column to the CSV, but we prepare the data here.
            # For T014, we just ensure the network metrics are correct.
            pass

        metrics_list.append(metrics)
        logger.info(f"Processed {mat_id}: nodes={metrics['num_nodes']}, edges={metrics['num_edges']}")

    # Save metrics
    save_metrics_to_csv(metrics_list, output_csv)

    # Update metadata
    update_metadata_yaml(cif_dir, graph_dir, metadata_path)

    logger.info("Metrics computation complete.")

if __name__ == "__main__":
    main()