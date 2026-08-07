import os
import json
import pickle
import logging
import csv
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

try:
    from pymatgen.core import Structure
    from pymatgen.analysis.bond_valence import BVAnalyzer
except ImportError:
    raise ImportError("pymatgen is required for this module. Install with: pip install pymatgen")

import networkx as nx
import pandas as pd

from config import Config
from utils import pin_seed

# Configure logger
logger = logging.getLogger("metrics_logger")

def setup_metrics_logger(log_file: Optional[str] = None) -> logging.Logger:
    """Set up the metrics logger."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    return logger

def load_graphs_from_directory(directory: str) -> List[Tuple[str, nx.Graph]]:
    """Load all graph pickles from a directory."""
    graphs = []
    dir_path = Path(directory)
    if not dir_path.exists():
        logger.warning(f"Directory {directory} does not exist.")
        return graphs
    
    for pkl_file in dir_path.glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                graph = pickle.load(f)
                material_id = pkl_file.stem
                graphs.append((material_id, graph))
        except Exception as e:
            logger.error(f"Failed to load {pkl_file}: {e}")
    return graphs

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """Load the materials manifest JSON."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest file not found: {manifest_path}")
        return {"materials": {}}
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def compute_lcc_metrics(graph: nx.Graph) -> Dict[str, float]:
    """Compute metrics on the Largest Connected Component."""
    if graph.number_of_nodes() == 0:
        return {"average_degree": 0.0, "average_path_length": float('nan'), "clustering_coefficient": 0.0}
    
    if not nx.is_connected(graph):
        try:
            lcc = max(nx.connected_components(graph), key=len)
            subgraph = graph.subgraph(lcc)
        except Exception:
            subgraph = graph
    else:
        subgraph = graph

    num_nodes = subgraph.number_of_nodes()
    num_edges = subgraph.number_of_edges()
    
    if num_nodes == 0:
        return {"average_degree": 0.0, "average_path_length": float('nan'), "clustering_coefficient": 0.0}
        
    avg_degree = 2.0 * num_edges / num_nodes if num_nodes > 0 else 0.0
    
    try:
        lengths = dict(nx.shortest_path_length(subgraph))
        total_length = 0
        count = 0
        for source in lengths:
            for target, dist in lengths[source].items():
                if source != target:
                    total_length += dist
                    count += 1
        avg_path = total_length / count if count > 0 else float('nan')
    except nx.NetworkXError:
        avg_path = float('nan')
        
    clustering = nx.average_clustering(subgraph)
    
    return {
        "average_degree": avg_degree,
        "average_path_length": avg_path,
        "clustering_coefficient": clustering
    }

def compute_physical_descriptors(cif_path: str) -> Dict[str, float]:
    """
    Calculate Unit Cell Volume, Total Atom Count, and Mean Atomic Mass from a CIF file.
    Uses pymatgen to parse the structure.
    """
    try:
        structure = Structure.from_file(cif_path)
    except Exception as e:
        logger.error(f"Failed to parse CIF {cif_path}: {e}")
        return {"unit_cell_volume": 0.0, "total_atom_count": 0, "mean_atomic_mass": 0.0}
    
    volume = structure.lattice.volume
    num_atoms = len(structure)
    
    total_mass = 0.0
    for species in structure.species:
        total_mass += species.atomic_weight
        
    mean_mass = total_mass / num_atoms if num_atoms > 0 else 0.0
    
    return {
        "unit_cell_volume": float(volume),
        "total_atom_count": int(num_atoms),
        "mean_atomic_mass": float(mean_mass)
    }

def extract_thermal_conductivity_scalar(cif_path: str, manifest: Dict[str, Any]) -> Optional[float]:
    """
    Extract thermal conductivity scalar from CIF metadata or manifest.
    
    Strategy:
    1. Check the manifest for pre-calculated thermal conductivity data (k_xx, k_yy, k_zz).
    2. If present, compute the scalar as the arithmetic mean of the diagonal components.
    3. If not in manifest, attempt to parse the CIF file for specific tags (though rare in standard CIFs).
    4. Return None if not found.
    """
    # Try to find material_id in the CIF filename or structure
    # We assume the manifest maps material_id -> data
    # We need to map the cif_path to a material_id. 
    # Usually, the cif file is named <material_id>.cif or similar.
    cif_name = Path(cif_path).stem
    
    # Check manifest for this material_id
    material_data = manifest.get("materials", {}).get(cif_name)
    
    if material_data:
        k_x = material_data.get("k_x")
        k_y = material_data.get("k_y")
        k_z = material_data.get("k_z")
        
        if k_x is not None and k_y is not None and k_z is not None:
            scalar = (float(k_x) + float(k_y) + float(k_z)) / 3.0
            logger.info(f"Extracted thermal conductivity scalar {scalar:.4f} for {cif_name} from manifest.")
            return scalar
        
        # Fallback: check for a single scalar key
        if "thermal_conductivity" in material_data:
            val = material_data["thermal_conductivity"]
            if isinstance(val, (int, float)):
                logger.info(f"Extracted thermal conductivity scalar {val} for {cif_name} from manifest (single value).")
                return float(val)

    # Fallback 2: Try to read from CIF headers if pymatgen exposes them
    try:
        structure = Structure.from_file(cif_path)
        # Check for custom tags in the CIF (pymatgen stores them in structure.properties)
        # This is highly dependent on the CIF content, but we check common keys
        props = structure.properties
        
        if "k_xx" in props and "k_yy" in props and "k_zz" in props:
            scalar = (float(props["k_xx"]) + float(props["k_yy"]) + float(props["k_zz"])) / 3.0
            logger.info(f"Extracted thermal conductivity scalar {scalar:.4f} for {cif_name} from CIF properties.")
            return scalar
    except Exception as e:
        logger.debug(f"Could not extract thermal conductivity from CIF properties for {cif_path}: {e}")
    
    logger.warning(f"Thermal conductivity not found for {cif_name} in manifest or CIF properties.")
    return None

def compute_metrics_for_graph(material_id: str, graph: nx.Graph, cif_path: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Compute all metrics for a single graph and its associated CIF."""
    lcc_metrics = compute_lcc_metrics(graph)
    physical_metrics = compute_physical_descriptors(cif_path)
    
    thermal_scalar = extract_thermal_conductivity_scalar(cif_path, manifest)
    
    return {
        "material_id": material_id,
        "average_degree": lcc_metrics["average_degree"],
        "average_path_length": lcc_metrics["average_path_length"],
        "clustering_coefficient": lcc_metrics["clustering_coefficient"],
        "unit_cell_volume": physical_metrics["unit_cell_volume"],
        "total_atom_count": physical_metrics["total_atom_count"],
        "mean_atomic_mass": physical_metrics["mean_atomic_mass"],
        "thermal_conductivity_scalar": thermal_scalar
    }

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str):
    """Save the computed metrics to a CSV file."""
    if not metrics_list:
        logger.warning("No metrics to save.")
        # Ensure the file is created even if empty, but with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            headers = ["material_id", "average_degree", "average_path_length", "clustering_coefficient", 
                       "unit_cell_volume", "total_atom_count", "mean_atomic_mass", "thermal_conductivity_scalar"]
            writer.writerow(headers)
        return

    headers = ["material_id", "average_degree", "average_path_length", "clustering_coefficient", 
               "unit_cell_volume", "total_atom_count", "mean_atomic_mass", "thermal_conductivity_scalar"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in metrics_list:
            writer.writerow(row)
    
    logger.info(f"Saved {len(metrics_list)} metrics to {output_path}")

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_artifact_hash(state_path: str, artifact_path: str, hash_value: str):
    """Update the state YAML file with the new artifact hash."""
    # Simple implementation to append or update state
    state = {"artifacts": {}}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as f:
                import yaml
                state = yaml.safe_load(f) or {"artifacts": {}}
        except Exception:
            pass
    
    state["artifacts"][artifact_path] = {"sha256": hash_value}
    
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, 'w') as f:
        import yaml
        yaml.dump(state, f)

def main():
    """Main entry point for computing metrics."""
    pin_seed(42)
    setup_metrics_logger()
    
    # Paths
    graphs_dir = "data/processed/networks"
    cif_dir = "data/raw/cif"
    manifest_path = "data/processed/manifest.json"
    output_csv = "data/processed/metrics.csv"
    state_path = "state/projects/PROJ-360-quantifying-the-impact-of-network-struct.yaml"
    
    # Load manifest
    manifest = load_manifest(manifest_path)
    
    # Load graphs
    graphs = load_graphs_from_directory(graphs_dir)
    logger.info(f"Loaded {len(graphs)} graphs.")
    
    if len(graphs) == 0:
        logger.error("No graphs found. Cannot compute metrics.")
        # Create empty CSV with headers
        save_metrics_to_csv([], output_csv)
        return
    
    metrics_list = []
    for material_id, graph in graphs:
        # Construct CIF path based on material_id
        cif_path = os.path.join(cif_dir, f"{material_id}.cif")
        if not os.path.exists(cif_path):
            # Try to find it if naming convention differs, but usually it's exact
            # Fallback: search directory
            found = False
            for f in Path(cif_dir).glob("*.cif"):
                if f.stem == material_id:
                    cif_path = str(f)
                    found = True
                    break
            if not found:
                logger.warning(f"CIF file not found for {material_id}, skipping.")
                continue
        
        try:
            metrics = compute_metrics_for_graph(material_id, graph, cif_path, manifest)
            metrics_list.append(metrics)
        except Exception as e:
            logger.error(f"Error processing {material_id}: {e}")
    
    save_metrics_to_csv(metrics_list, output_csv)
    
    # Update state
    if os.path.exists(output_csv):
        checksum = compute_sha256(output_csv)
        update_state_artifact_hash(state_path, output_csv, checksum)

if __name__ == "__main__":
    main()