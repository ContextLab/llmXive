"""
TDA Computation Pipeline: Graph Construction and Shortest-Path Filtration.

Implements FR-001: Convert SMILES to molecular graphs and compute persistence diagrams
using shortest-path filtration.

Dependencies:
- code/utils/graph_builder.py (build_graph, validate_graph)
- code/utils/persistence_utils.py (compute_shortest_path_matrix, build_shortest_path_filtration, compute_persistence_diagram)
"""
import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rdkit import RDLogger

# Project imports
# Note: These paths assume the script is run from the project root or code directory
# We add the parent directory to sys.path to ensure relative imports work
_code_dir = Path(__file__).parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

from utils.graph_builder import build_graph, validate_graph, Graph
from utils.persistence_utils import (
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    vectorize,
    handle_empty_diagram
)

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the TDA computation pipeline."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def setup_invalid_smiles_logger(log_file: str) -> logging.Logger:
    """Setup a dedicated logger for invalid SMILES entries."""
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.ERROR)
    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def log_invalid_smiles(logger: logging.Logger, smiles: str, error: str) -> None:
    """Log an invalid SMILES entry to the dedicated logger."""
    logger.error(f"Invalid SMILES: {smiles} | Error: {error}")

def vectorize_diagram_to_image(
    diagram: List[Tuple[float, float]],
    resolution: int = 10
) -> np.ndarray:
    """
    Vectorize a persistence diagram into a persistence image.
    
    Args:
        diagram: List of (death, birth) or (birth, death) tuples.
        resolution: Grid resolution (e.g., 10 for 10x10).
    
    Returns:
        np.ndarray of shape (resolution, resolution).
    """
    if not diagram:
        return handle_empty_diagram(resolution)
    
    # Convert diagram to numpy array
    # Note: Gudhi/Dionysus typically returns (birth, death)
    # We assume input is (birth, death)
    try:
        arr = np.array(diagram)
        if arr.shape[1] != 2:
            # Fallback if format is unexpected
            return handle_empty_diagram(resolution)
    except Exception:
        return handle_empty_diagram(resolution)
    
    birth = arr[:, 0]
    death = arr[:, 1]
    
    # Vectorize using the utility from persistence_utils
    # The utility expects (birth, death) pairs
    return vectorize(list(zip(birth, death)), resolution)

def flatten_image(image: np.ndarray) -> np.ndarray:
    """Flatten a 2D image to a 1D vector."""
    return image.flatten()

def compute_persistence_features(
    diagram: List[Tuple[float, float]],
    resolutions: List[int] = [10, 20, 30]
) -> Dict[str, np.ndarray]:
    """
    Compute persistence images for multiple resolutions.
    
    Args:
        diagram: Persistence diagram (list of (birth, death) tuples).
        resolutions: List of grid resolutions.
    
    Returns:
        Dictionary mapping resolution string to flattened image array.
    """
    features = {}
    for res in resolutions:
        img = vectorize_diagram_to_image(diagram, resolution=res)
        features[f"p_img_{res}"] = flatten_image(img)
    return features

def process_molecule(
    smiles: str,
    molecule_id: str,
    logger: logging.Logger,
    invalid_logger: Optional[logging.Logger] = None
) -> Optional[Dict[str, Any]]:
    """
    Process a single molecule: build graph, compute filtration, generate diagram.
    
    Returns:
        Dictionary with molecule_id and persistence features, or None if failed.
    """
    try:
        # 1. Build Graph
        graph = build_graph(smiles)
        if graph is None:
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Graph build failed")
            logger.warning(f"Failed to build graph for {molecule_id}: {smiles}")
            return None
        
        # 2. Validate Graph
        if not validate_graph(graph):
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Graph validation failed")
            logger.warning(f"Graph validation failed for {molecule_id}: {smiles}")
            return None
        
        # 3. Compute Shortest Path Matrix
        try:
            sp_matrix = compute_shortest_path_matrix(graph)
        except Exception as e:
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, f"Shortest path error: {e}")
            logger.warning(f"Shortest path failed for {molecule_id}: {e}")
            return None
        
        if sp_matrix is None:
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Shortest path matrix is None")
            logger.warning(f"Shortest path matrix is None for {molecule_id}")
            return None

        # 4. Build Filtration
        try:
            filtration = build_shortest_path_filtration(sp_matrix)
        except Exception as e:
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, f"Filtration error: {e}")
            logger.warning(f"Filtration failed for {molecule_id}: {e}")
            return None
        
        if not filtration:
            # Empty filtration is valid, results in empty diagram
            logger.info(f"Empty filtration for {molecule_id}")
            diagram = []
        else:
            # 5. Compute Persistence Diagram
            try:
                diagram = compute_persistence_diagram(filtration)
            except Exception as e:
                if invalid_logger:
                    log_invalid_smiles(invalid_logger, smiles, f"Diagram error: {e}")
                logger.warning(f"Diagram computation failed for {molecule_id}: {e}")
                return None
        
        # 6. Vectorize to Persistence Images (Resolutions 10, 20, 30)
        # Per task T013, we need to generate images for multiple resolutions.
        # We compute them here to support the pipeline flow.
        # Default resolutions for T012/T013 integration
        resolutions = [10, 20, 30]
        features = compute_persistence_features(diagram, resolutions=resolutions)
        
        return {
            "molecule_id": molecule_id,
            "diagram_size": len(diagram),
            "features": features
        }

    except Exception as e:
        if invalid_logger:
            log_invalid_smiles(invalid_logger, smiles, f"Unhandled error: {e}")
        logger.error(f"Unhandled exception for {molecule_id}: {traceback.format_exc()}")
        return None

def generate_tda_features_csv(
    input_df: pd.DataFrame,
    output_path: str,
    invalid_log_path: str,
    resolutions: List[int] = [10, 20, 30]
) -> Tuple[int, int]:
    """
    Process the entire dataset and generate TDA feature CSVs.
    
    Args:
        input_df: DataFrame with 'smiles' and 'molecule_id' (or index).
        output_path: Path to save the CSV.
        invalid_log_path: Path to log invalid SMILES.
        resolutions: List of grid resolutions.
    
    Returns:
        Tuple of (processed_count, failed_count).
    """
    logger = setup_logging()
    invalid_logger = setup_invalid_smiles_logger(invalid_log_path)
    
    logger.info(f"Starting TDA computation on {len(input_df)} molecules...")
    
    processed_count = 0
    failed_count = 0
    results = []
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    for idx, row in input_df.iterrows():
        smiles = row['smiles']
        # Use index or a specific ID column if available
        mol_id = row.get('molecule_id', f"mol_{idx}")
        
        result = process_molecule(smiles, mol_id, logger, invalid_logger)
        
        if result is not None:
            processed_count += 1
            # Expand features into columns
            row_data = {
                "molecule_id": result["molecule_id"],
                "diagram_size": result["diagram_size"]
            }
            for res_key, feature_vec in result["features"].items():
                # Create columns for each pixel in the image
                for i, val in enumerate(feature_vec):
                    col_name = f"{res_key}_{i}"
                    row_data[col_name] = val
            results.append(row_data)
        else:
            failed_count += 1
          
        if processed_count % 100 == 0:
            logger.info(f"Processed {processed_count} molecules, {failed_count} failed so far...")
    
    # Create DataFrame and save
    if results:
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(output_df)} records to {output_path}")
    else:
        logger.warning("No valid molecules processed. Output file will be empty.")
        # Create empty file with headers if possible, or just touch
        Path(output_path).touch()
    
    return processed_count, failed_count

def main():
    """Main entry point for TDA computation."""
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    raw_data = data_dir / "raw"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Input: Check for existing raw data or processed splits
    # We expect the data ingestion script (T008a/b) to have prepared the data.
    # We look for the ESOL dataset in raw or the processed splits.
    # For T012, we assume we are processing the raw ESOL data or a subset.
    
    # Check for raw ESOL data
    esol_file = raw_data / "esol.csv"
    if not esol_file.exists():
        # Check for processed splits as a fallback if raw is missing
        # But strictly, T012 needs raw SMILES. If raw is missing, we must fail.
        # However, T008a/b might have saved a processed subset.
        # Let's look for a standard processed file from ingestion if raw is gone.
        # If data ingestion failed, we can't proceed.
        print("Error: Raw ESOL data not found in data/raw/esol.csv")
        print("Ensure T008a/b has successfully ingested the data.")
        sys.exit(1)
    
    logger = setup_logging()
    logger.info(f"Loading data from {esol_file}")
    
    try:
        df = pd.read_csv(esol_file)
    except Exception as e:
        logger.error(f"Failed to load ESOL data: {e}")
        sys.exit(1)
    
    # Validate required columns
    if 'smiles' not in df.columns:
        logger.error("Input data missing 'smiles' column.")
        sys.exit(1)
    
    # Add molecule_id if not present
    if 'molecule_id' not in df.columns:
        df['molecule_id'] = df.index.map(lambda x: f"mol_{x}")
    
    # Run computation
    output_csv = processed_dir / "tda_features_raw.csv" # Intermediate
    # Per T013, we need specific filenames. T012 focuses on the computation logic.
    # We generate the raw features here. T013 will filter/format them.
    # However, to satisfy T013's requirement for "persistence_images_10x10.csv",
    # we will generate the full set here and T013 can be seen as a post-processing
    # step or we generate all here.
    # The task T012 says "Pipeline to convert SMILES to graphs and compute persistence diagrams".
    # We will generate the full features for 10, 20, 30 resolutions.
    
    invalid_log = logs_dir / "invalid_smiles.log"
    
    logger.info("Starting TDA computation...")
    start = time.time()
    
    proc_count, fail_count = generate_tda_features_csv(
        df, 
        output_csv, 
        invalid_log, 
        resolutions=[10, 20, 30]
    )
    
    elapsed = time.time() - start
    logger.info(f"Completed in {elapsed:.2f}s. Processed: {proc_count}, Failed: {fail_count}")
    
    if proc_count == 0:
        logger.error("No molecules processed. Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()