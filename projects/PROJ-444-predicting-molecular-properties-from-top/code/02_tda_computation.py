import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import networkx as nx
from rdkit import Chem
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial.distance import pdist, squareform

# Import from project utilities
from utils.graph_builder import (
    setup_invalid_smiles_logger,
    log_invalid_smiles,
    is_valid_molecule,
    build_molecular_graph,
    get_molecular_weight,
    build_graphs_from_smiles_list,
    validate_graph_structure
)
from utils.persistence_utils import (
    check_memory_requirement,
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    handle_empty_diagram,
    compute_betti_numbers,
    get_topological_features
)

# Constants
MEMORY_THRESHOLD_GB = 4.0
DEFAULT_RESOLUTIONS = [10, 20, 30]

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure logging for the TDA computation pipeline."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def vectorize_diagram_to_image(
    diagram: List[Tuple[float, float]],
    resolution: int = 10,
    birth_limit: float = 10.0,
    death_limit: float = 20.0
) -> np.ndarray:
    """
    Vectorize a persistence diagram into a persistence image.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (resolution x resolution).
        birth_limit: Maximum birth value for grid.
        death_limit: Maximum death value for grid.
        
    Returns:
        2D numpy array representing the persistence image.
    """
    if not diagram:
        return np.zeros((resolution, resolution))
    
    # Convert to numpy array
    points = np.array(diagram)
    births = points[:, 0]
    deaths = points[:, 1]
    persistences = deaths - births
    
    # Create grid
    x_edges = np.linspace(0, birth_limit, resolution + 1)
    y_edges = np.linspace(0, death_limit, resolution + 1)
    
    image = np.zeros((resolution, resolution))
    
    # Gaussian kernel parameters
    sigma = (birth_limit / resolution) * 0.5
    
    for i, (b, d) in enumerate(diagram):
        p = d - b
        if p <= 0:
            continue
        
        # Weight based on persistence
        weight = p
        
        # Find grid cell
        x_idx = np.searchsorted(x_edges, b) - 1
        y_idx = np.searchsorted(y_edges, d) - 1
        
        if 0 <= x_idx < resolution and 0 <= y_idx < resolution:
            # Apply Gaussian weighting
            gaussian_val = np.exp(-((b - x_edges[x_idx])**2 + (d - y_edges[y_idx])**2) / (2 * sigma**2))
            image[y_idx, x_idx] += weight * gaussian_val
    
    # Normalize
    if image.sum() > 0:
        image = image / image.sum()
    
    return image

def flatten_image(image: np.ndarray) -> np.ndarray:
    """Flatten a 2D image to a 1D vector."""
    return image.flatten()

def compute_persistence_features(
    mol: Chem.Mol,
    logger: logging.Logger,
    resolutions: List[int] = DEFAULT_RESOLUTIONS,
    memory_threshold_gb: float = MEMORY_THRESHOLD_GB
) -> Dict[str, Any]:
    """
    Compute persistence features for a single molecule.
    
    Args:
        mol: RDKit molecule object.
        logger: Logger instance.
        resolutions: List of grid resolutions to compute.
        memory_threshold_gb: Memory threshold in GB for sparse matrix check.
        
    Returns:
        Dictionary containing persistence images and topological features.
    """
    try:
        # Build molecular graph
        graph = build_molecular_graph(mol)
        if graph is None:
            return None
        
        # Validate graph structure
        if not validate_graph_structure(graph):
            logger.warning(f"Invalid graph structure for molecule")
            return None
        
        # Check molecular weight and memory requirements
        mw = get_molecular_weight(mol)
        if mw is None:
            logger.warning(f"Could not compute molecular weight")
            return None
        
        # Estimate memory requirement for shortest path matrix
        n_nodes = graph.number_of_nodes()
        mem_estimate_gb = check_memory_requirement(n_nodes)
        
        if mem_estimate_gb > memory_threshold_gb:
            logger.warning(
                f"Molecule with MW={mw:.2f} and {n_nodes} nodes requires "
                f"~{mem_estimate_gb:.2f}GB memory for dense matrix. "
                f"Using sparse matrix computation."
            )
            # Use sparse matrix logic for large molecules
            use_sparse = True
        else:
            use_sparse = False
        
        # Compute shortest path matrix
        if use_sparse:
            # Use sparse matrix computation
            adj_matrix = nx.adjacency_matrix(graph)
            # Convert to CSR for efficient operations
            sparse_adj = csr_matrix(adj_matrix)
            
            # Compute shortest paths using sparse Dijkstra
            try:
                lengths = dijkstra(csgraph=sparse_adj, directed=False, indices=range(n_nodes))
                # Handle disconnected components (set inf to large value)
                lengths = np.where(np.isinf(lengths), n_nodes * 10, lengths)
                shortest_paths = lengths
            except Exception as e:
                logger.warning(f"Sparse shortest path failed: {e}. Skipping molecule.")
                return None
        else:
            # Use standard computation
            shortest_paths = nx.shortest_path_length(graph, weight='weight')
            # Convert to matrix format
            nodes = list(graph.nodes())
            n = len(nodes)
            shortest_paths_matrix = np.zeros((n, n))
            for i, u in enumerate(nodes):
                for j, v in enumerate(nodes):
                    if u in shortest_paths and v in shortest_paths[u]:
                        shortest_paths_matrix[i, j] = shortest_paths[u][v]
        
        # Build filtration
        filtration = build_shortest_path_filtration(shortest_paths)
        
        # Compute persistence diagram
        diagram = compute_persistence_diagram(filtration)
        
        # Handle empty diagram
        if not diagram:
            diagram = handle_empty_diagram()
        
        # Compute topological features
        betti = compute_betti_numbers(diagram)
        topological_features = get_topological_features(diagram)
        
        # Vectorize to persistence images for each resolution
        persistence_images = {}
        flattened_vectors = {}
        
        for res in resolutions:
            img = vectorize_diagram_to_image(diagram, resolution=res)
            persistence_images[res] = img.tolist()
            flattened_vectors[f"image_{res}"] = flatten_image(img).tolist()
        
        return {
            "molecular_weight": mw,
            "num_nodes": n_nodes,
            "num_edges": graph.number_of_edges(),
            "betti_0": betti[0],
            "betti_1": betti[1],
            "persistence_images": persistence_images,
            "flattened_vectors": flattened_vectors,
            **topological_features
        }
        
    except Exception as e:
        logger.error(f"Error computing persistence features: {e}")
        logger.error(traceback.format_exc())
        return None

def generate_tda_features_csv(
    data_path: Path,
    output_dir: Path,
    resolutions: List[int] = DEFAULT_RESOLUTIONS,
    memory_threshold_gb: float = MEMORY_THRESHOLD_GB
) -> Path:
    """
    Generate TDA features CSV for all molecules in the dataset.
    
    Args:
        data_path: Path to the input CSV with SMILES.
        output_dir: Directory to save output files.
        resolutions: List of grid resolutions.
        memory_threshold_gb: Memory threshold for sparse matrix logic.
        
    Returns:
        Path to the generated CSV file.
    """
    logger = setup_logging(output_dir / "tda_computation.log")
    
    # Setup invalid SMILES logger
    invalid_log_path = output_dir.parent / "logs" / "invalid_smiles.log"
    invalid_log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_invalid_smiles_logger(str(invalid_log_path))
    
    # Load dataset
    logger.info(f"Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    
    if "smiles" not in df.columns:
        raise ValueError("Dataset must contain 'smiles' column")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    skipped_count = 0
    total_count = len(df)
    
    logger.info(f"Processing {total_count} molecules...")
    
    for idx, row in df.iterrows():
        smiles = row["smiles"]
        mol_id = row.get("id", f"mol_{idx}")
        
        # Validate SMILES
        if not is_valid_molecule(smiles):
            log_invalid_smiles(smiles, f"Invalid SMILES at index {idx}")
            skipped_count += 1
            continue
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            log_invalid_smiles(smiles, f"Failed to parse molecule at index {idx}")
            skipped_count += 1
            continue
        
        # Compute features
        features = compute_persistence_features(
            mol, 
            logger, 
            resolutions=resolutions,
            memory_threshold_gb=memory_threshold_gb
        )
        
        if features is None:
            skipped_count += 1
            continue
        
        # Flatten features for CSV
        row_data = {
            "id": mol_id,
            "smiles": smiles,
            "molecular_weight": features["molecular_weight"],
            "num_nodes": features["num_nodes"],
            "num_edges": features["num_edges"],
            "betti_0": features["betti_0"],
            "betti_1": features["betti_1"],
        }
        
        # Add flattened vectors
        for key, values in features["flattened_vectors"].items():
            for i, val in enumerate(values):
                row_data[f"{key}_{i}"] = val
        
        # Add other topological features
        for key, val in features.items():
            if key not in ["molecular_weight", "num_nodes", "num_edges", 
                           "betti_0", "betti_1", "persistence_images", 
                           "flattened_vectors"]:
                row_data[key] = val
        
        results.append(row_data)
        
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{total_count} molecules")
    
    # Create DataFrame
    if not results:
        logger.warning("No valid molecules processed")
        output_path = output_dir / "tda_features.csv"
        pd.DataFrame(columns=["id", "smiles"]).to_csv(output_path, index=False)
        return output_path
    
    output_df = pd.DataFrame(results)
    
    # Save main features file
    output_path = output_dir / "tda_features.csv"
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved TDA features to {output_path}")
    
    # Save individual persistence images for each resolution
    for res in resolutions:
        image_path = output_dir / f"persistence_images_{res}x{res}.csv"
        image_data = []
        
        for result in results:
            row = {
                "id": result["id"],
                "smiles": result["smiles"]
            }
            # Extract image vectors for this resolution
            img_key = f"image_{res}"
            if img_key in result:
                for i, val in enumerate(result[img_key]):
                    row[f"pixel_{i}"] = val
            image_data.append(row)
        
        pd.DataFrame(image_data).to_csv(image_path, index=False)
        logger.info(f"Saved persistence images ({res}x{res}) to {image_path}")
    
    logger.info(f"Skipped {skipped_count} invalid molecules")
    logger.info(f"Successfully processed {len(results)} molecules")
    
    return output_path

def main():
    """Main entry point for TDA computation."""
    # Default paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    processed_dir = data_dir / "processed"
    raw_dir = data_dir / "raw"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find input file
    input_files = list(raw_dir.glob("*.csv"))
    if not input_files:
        # Try processed directory as fallback
        input_files = list(processed_dir.glob("esol*.csv"))
    
    if not input_files:
        print("No input CSV found in data/raw/ or data/processed/")
        sys.exit(1)
    
    input_path = input_files[0]
    logger = setup_logging(processed_dir / "tda_computation.log")
    logger.info(f"Using input file: {input_path}")
    
    # Generate TDA features
    output_path = generate_tda_features_csv(
        input_path,
        processed_dir,
        resolutions=[10, 20, 30],
        memory_threshold_gb=MEMORY_THRESHOLD_GB
    )
    
    print(f"TDA computation complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()
