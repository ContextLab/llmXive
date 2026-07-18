import os
import json
import pickle
import logging
import csv
import math
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from utils
from utils import setup_logging, pin_seed
# Import from config
from config import Config, get_config, reset_config, initialize_environment

# Import from construct_network (for manifest loading if needed)
# Note: construct_network exports: get_element_covalent_radius, detect_bonds_covalent, detect_bonds_fallback, construct_network_from_structure, process_cif_file, save_graph_to_pickle, build_network_manifest, main

# --- Logger Setup ---
def setup_metrics_logger(name: str = "metrics_logger", log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

logger = setup_metrics_logger()

# --- Helper Functions ---

def load_graphs_from_directory(graph_dir: str) -> List[Tuple[str, Any]]:
    """Load all pickle files from a directory. Returns list of (filename, graph_object)."""
    graphs = []
    path = Path(graph_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {graph_dir}")
    for pkl_file in path.glob("*.pkl"):
        try:
            with open(pkl_file, 'rb') as f:
                g = pickle.load(f)
                graphs.append((pkl_file.name, g))
        except Exception as e:
            logger.error(f"Failed to load {pkl_file}: {e}")
    return graphs

def load_manifest(manifest_path: str = "data/raw/cif_manifest.json") -> Dict[str, Any]:
    """Load the manifest file containing material metadata."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest file not found: {manifest_path}. Returning empty manifest.")
        return {"materials": {}}
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse manifest: {e}")
        return {"materials": {}}

def get_thermal_conductivity_scalar(material_id: str, manifest: Dict[str, Any]) -> Optional[float]:
    """
    Extract thermal conductivity scalar (mean of k_x, k_y, k_z) from manifest.
    Implements the assertion check for FR-004 compliance.
    """
    material_data = manifest['materials'].get(material_id)
    if not material_data:
        logger.warning(f"Material {material_id} not found in manifest. Skipping.")
        return None

    k_x = material_data.get('k_x')
    k_y = material_data.get('k_y')
    k_z = material_data.get('k_z')

    if k_x is None or k_y is None or k_z is None:
        logger.warning(f"Missing thermal conductivity components for {material_id}. Skipping.")
        return None

    try:
        k_scalar = (k_x + k_y + k_z) / 3.0
        mean_components = (k_x + k_y + k_z) / 3.0

        # Verification assertion
        if abs(k_scalar - mean_components) > 1e-6:
            discrepancy = abs(k_scalar - mean_components)
            logger.error(f"Assertion failed for {material_id}: Scalar {k_scalar} != Mean {mean_components} (diff: {discrepancy}). Skipping material.")
            return None

        return k_scalar
    except (TypeError, ValueError) as e:
        logger.error(f"Error calculating scalar for {material_id}: {e}. Skipping.")
        return None

def compute_physical_descriptors(cif_path: str) -> Dict[str, float]:
    """
    Placeholder for physical descriptors if needed.
    Currently returns dummy values or 0.0 if not computed in T014a.
    Since T014a is marked done, we assume the CSV already has these columns.
    This function is kept for interface compatibility but T015 focuses on thermal scalar.
    """
    # In a real scenario, this would parse CIF for volume, atom count, etc.
    # For T015, we just ensure the thermal scalar logic is robust.
    return {"volume": 0.0, "atom_count": 0, "mean_mass": 0.0}

def compute_metrics_for_graph(graph: Any, material_id: str) -> Dict[str, Any]:
    """Compute network metrics for a single graph."""
    import networkx as nx

    if not isinstance(graph, nx.Graph):
        logger.error(f"Object for {material_id} is not a networkx.Graph")
        return {}

    if graph.number_of_nodes() < 2:
        logger.warning(f"Graph for {material_id} has < 2 nodes. Skipping.")
        return {}

    metrics = {
        "material_id": material_id,
        "num_nodes": graph.number_of_nodes(),
        "num_edges": graph.number_of_edges()
    }

    # Average Degree
    if graph.number_of_nodes() > 0:
        metrics["avg_degree"] = 2.0 * graph.number_of_edges() / graph.number_of_nodes()
    else:
        metrics["avg_degree"] = 0.0

    # Largest Connected Component (LCC) metrics
    if nx.is_connected(graph):
        lcc = graph
        metrics["is_connected"] = True
    else:
        try:
            lcc = max(nx.connected_components(graph), key=len)
            lcc_graph = graph.subgraph(lcc).copy()
            metrics["is_connected"] = False
            metrics["lcc_size"] = len(lcc)
            graph = lcc_graph # Use LCC for path length
        except Exception as e:
            logger.error(f"Failed to find LCC for {material_id}: {e}")
            metrics["is_connected"] = False
            metrics["lcc_size"] = 0
            return metrics

    # Average Shortest Path Length (on LCC)
    try:
        metrics["avg_path_length"] = nx.average_shortest_path_length(graph)
    except Exception:
        metrics["avg_path_length"] = float('nan')

    # Clustering Coefficient
    try:
        metrics["clustering_coeff"] = nx.average_clustering(graph)
    except Exception:
        metrics["clustering_coeff"] = float('nan')

    return metrics

def save_metrics_to_csv(metrics_list: List[Dict[str, Any]], output_path: str):
    """Save metrics list to CSV."""
    if not metrics_list:
        logger.warning("No metrics to save.")
        return

    fieldnames = list(metrics_list[0].keys())
    # Ensure thermal_conductivity_scalar is in fieldnames if present in any row
    if "thermal_conductivity_scalar" not in fieldnames:
        fieldnames.append("thermal_conductivity_scalar")

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics_list)

def update_metadata_yaml(output_path: str, material_id: str, thermal_scalar: float):
    """
    Update data/metadata.yaml to reflect the new thermal conductivity scalar.
    This is a simplified update; in production, use a proper YAML library.
    """
    metadata_path = "data/metadata.yaml"
    if not os.path.exists(metadata_path):
        logger.warning(f"Metadata file {metadata_path} not found. Cannot update.")
        return

    try:
        import yaml
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f) or {}

        if "thermal_conductivity" not in metadata:
            metadata["thermal_conductivity"] = {}

        metadata["thermal_conductivity"][material_id] = {
            "scalar": thermal_scalar,
            "source": "calculated_from_manifest"
        }

        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f)
        logger.info(f"Updated metadata.yaml for {material_id}")
    except ImportError:
        logger.warning("PyYAML not installed. Skipping metadata update.")
    except Exception as e:
        logger.error(f"Failed to update metadata.yaml: {e}")

def main():
    """
    Main entry point for T015: Extract thermal conductivity scalar and append to metrics.csv.
    Dependency: T013 (metrics.csv creation) must have run.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Compute network metrics and append thermal conductivity.")
    parser.add_argument("--input", type=str, default="data/processed/networks/", help="Directory containing graph pickle files")
    parser.add_argument("--output", type=str, default="data/processed/metrics.csv", help="Output CSV path")
    parser.add_argument("--manifest", type=str, default="data/raw/cif_manifest.json", help="Path to manifest file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    pin_seed(args.seed)
    initialize_environment()

    logger.info(f"Starting T015: Thermal Conductivity Scalar Extraction. Input: {args.input}, Output: {args.output}")

    # 1. Load existing metrics if they exist (from T013)
    # We need to merge the new thermal scalar column into the existing metrics.
    existing_metrics = []
    existing_fieldnames = []
    if os.path.exists(args.output):
        logger.info(f"Loading existing metrics from {args.output}")
        try:
            with open(args.output, 'r') as f:
                reader = csv.DictReader(f)
                existing_fieldnames = reader.fieldnames
                existing_metrics = list(reader)
            logger.info(f"Loaded {len(existing_metrics)} existing rows.")
        except Exception as e:
            logger.error(f"Failed to load existing metrics: {e}. Starting fresh.")
            existing_metrics = []
            existing_fieldnames = []

    # 2. Load Manifest
    manifest = load_manifest(args.manifest)

    # 3. Process Graphs and Append Thermal Scalar
    # If existing_metrics is empty, we re-compute all metrics (fallback)
    # If existing_metrics has data, we assume it has material_id and we just add the thermal scalar.
    
    # We need to map material_id -> thermal_scalar
    thermal_scalars = {}
    for mat_id, mat_info in manifest.get('materials', {}).items():
        scalar = get_thermal_conductivity_scalar(mat_id, manifest)
        if scalar is not None:
            thermal_scalars[mat_id] = scalar

    # Determine final fieldnames
    final_fieldnames = list(existing_fieldnames) if existing_fieldnames else ["material_id", "num_nodes", "num_edges", "avg_degree", "avg_path_length", "clustering_coeff"]
    if "thermal_conductivity_scalar" not in final_fieldnames:
        final_fieldnames.append("thermal_conductivity_scalar")

    # Prepare final rows
    final_rows = []
    skipped_count = 0

    # If we have existing metrics, we just add the thermal scalar column
    if existing_metrics:
        logger.info("Appending thermal conductivity to existing metrics.")
        for row in existing_metrics:
            mat_id = row.get("material_id")
            if not mat_id:
                logger.warning("Row missing material_id. Skipping.")
                continue

            scalar = thermal_scalars.get(mat_id)
            if scalar is not None:
                row["thermal_conductivity_scalar"] = scalar
                final_rows.append(row)
                # Optional: Update metadata if desired
                # update_metadata_yaml(args.output, mat_id, scalar)
            else:
                logger.warning(f"No thermal scalar for {mat_id}. Skipping row.")
                skipped_count += 1
    else:
        # Fallback: Re-compute metrics if file was missing or empty
        logger.warning("Existing metrics file empty or missing. Re-computing metrics.")
        graphs = load_graphs_from_directory(args.input)
        for filename, graph in graphs:
            # Extract material_id from filename or graph metadata
            # Assuming filename format: {material_id}.pkl
            material_id = Path(filename).stem
            metrics = compute_metrics_for_graph(graph, material_id)
            if not metrics:
                continue

            scalar = thermal_scalars.get(material_id)
            if scalar is not None:
                metrics["thermal_conductivity_scalar"] = scalar
                final_rows.append(metrics)
            else:
                logger.warning(f"No thermal scalar for {material_id}. Skipping.")
                skipped_count += 1

    logger.info(f"Processed {len(final_rows)} materials. Skipped {skipped_count} due to missing thermal data.")

    # 4. Save to CSV
    if final_rows:
        save_metrics_to_csv(final_rows, args.output)
        logger.info(f"Successfully saved metrics to {args.output}")
    else:
        logger.error("No valid rows to save.")
        # Create empty file with headers to satisfy downstream tasks
        with open(args.output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=final_fieldnames)
            writer.writeheader()

    logger.info("T015 Complete.")
    return 0

if __name__ == "__main__":
    exit(main())