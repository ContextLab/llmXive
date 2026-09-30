import os
import sys
import json
import logging
import time
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from rdkit import Chem

# Import from local utils to ensure API surface consistency
from utils.graph_builder import build_graph, is_valid_molecule, log_invalid_smiles
from utils.persistence_utils import (
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    vectorize,
    handle_empty_diagram,
    check_memory_requirement
)

# Constants
RESOLUTION = 10
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXCLUDED_MANIFEST_PATH = DATA_PROCESSED_DIR / "excluded_smiles_manifest.csv"

def setup_logging():
    """Configure logging for the TDA computation pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(DATA_LOGS_DIR / "tda_computation.log")
        ]
    )
    return logging.getLogger(__name__)

def vectorize_diagram_to_image(diagram: List[List[float]], resolution: int = RESOLUTION) -> np.ndarray:
    """
    Convert a persistence diagram to a persistence image (vector).
    
    Args:
        diagram: List of [birth, death] pairs.
        resolution: Grid resolution (e.g., 10 for 10x10).
        
    Returns:
        Flattened numpy array of size resolution*resolution.
    """
    if not diagram:
        return handle_empty_diagram(resolution)
    
    # Ensure diagram is numpy array
    diag_arr = np.array(diagram)
    
    # Use the utility function from persistence_utils
    # Assuming 'vectorize' handles the Gaussian weighting and grid integration
    # If 'vectorize' expects a specific Gudhi format, we adapt here.
    # Here we assume 'vectorize' takes the raw birth/death pairs and returns the image.
    try:
        image = vectorize(diag_arr, resolution)
        return image.flatten()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Vectorization failed for diagram, returning zeros: {e}")
        return np.zeros(resolution * resolution)

def flatten_image(image: np.ndarray) -> List[float]:
    """Flatten a 2D image to a 1D list."""
    return image.flatten().tolist()

def compute_persistence_features(smiles: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Compute TDA features for a single molecule.
    
    1. Validate SMILES and build graph.
    2. Compute shortest-path filtration.
    3. Compute persistence diagram.
    4. Vectorize to persistence image.
    
    Returns:
        Dict with molecule_id and feature vector, or None if invalid.
    """
    # Check validity using the shared graph builder
    if not is_valid_molecule(smiles):
        return None

    try:
        # Build molecular graph
        graph = build_graph(smiles)
        if graph is None:
            return None

        # Check memory before heavy computation
        check_memory_requirement()

        # Compute shortest path matrix
        try:
            # This might raise if graph is disconnected or has issues
            dist_matrix = compute_shortest_path_matrix(graph)
        except Exception as e:
            logger.debug(f"Shortest path computation failed for {smiles}: {e}")
            return None

        # Build filtration
        filtration = build_shortest_path_filtration(graph, dist_matrix)
        
        # Compute persistence diagram
        # Gudhi or Dionysus usually returns a list of (birth, death, dim)
        # We assume the utility returns a list of [birth, death]
        diagram = compute_persistence_diagram(filtration)
        
        # Vectorize
        features = vectorize_diagram_to_image(diagram, RESOLUTION)
        
        return {
            "molecule_id": smiles,
            "features": features,
            "valid": True
        }

    except Exception as e:
        logger.debug(f"Unexpected error processing {smiles}: {e}")
        return None

def generate_tda_features_csv(input_path: str, output_path: str):
    """
    Main pipeline to process a CSV of SMILES and generate TDA features.
    
    Args:
        input_path: Path to input CSV with 'smiles' column.
        output_path: Path to output CSV for features.
    """
    logger = setup_logging()
    logger.info(f"Starting TDA computation for {input_path}")

    # Ensure directories exist
    DATA_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Load input data
    try:
        df = pd.read_csv(input_path)
        if 'smiles' not in df.columns:
            logger.error("Input CSV must contain 'smiles' column")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} molecules")

    results = []
    invalid_entries = []
    excluded_count = 0

    # Setup the invalid smiles logger specifically for this task
    # This ensures we write to data/logs/invalid_smiles.log
    invalid_logger = setup_invalid_smiles_logger()

    for idx, row in df.iterrows():
        smiles = str(row['smiles'])
        molecule_id = row.get('molecule_id', f"mol_{idx}")
        
        # Check validity first
        if not is_valid_molecule(smiles):
            # Log to invalid_smiles.log
            log_invalid_smiles(invalid_logger, smiles, "Invalid RDKit molecule")
            # Add to manifest
            invalid_entries.append({
                "molecule_id": molecule_id,
                "smiles": smiles,
                "reason": "Invalid RDKit molecule"
            })
            excluded_count += 1
            continue

        # Try to compute features
        result = compute_persistence_features(smiles, logger)
        
        if result is None:
            # Log to invalid_smiles.log if computation failed
            log_invalid_smiles(invalid_logger, smiles, "Computation failed")
            invalid_entries.append({
                "molecule_id": molecule_id,
                "smiles": smiles,
                "reason": "Computation failed"
            })
            excluded_count += 1
            continue
        
        # Flatten features and create row
        feature_cols = {f"p_img_{i}": val for i, val in enumerate(result['features'])}
        feature_cols['molecule_id'] = molecule_id
        results.append(feature_cols)

    logger.info(f"Processed {len(results)} valid molecules, excluded {excluded_count}")

    # Write main output
    if results:
        out_df = pd.DataFrame(results)
        out_df.to_csv(output_path, index=False)
        logger.info(f"Wrote {len(results)} rows to {output_path}")
    else:
        logger.warning("No valid molecules found. Output file will be empty.")
        # Create empty file with headers if possible, or just touch it
        pd.DataFrame(columns=['molecule_id'] + [f"p_img_{i}" for i in range(RESOLUTION*RESOLUTION)]).to_csv(output_path, index=False)

    # Write excluded manifest (Constitution VI Compliance)
    if invalid_entries:
        manifest_df = pd.DataFrame(invalid_entries)
        manifest_df.to_csv(EXCLUDED_MANIFEST_PATH, index=False)
        logger.info(f"Wrote {len(invalid_entries)} exclusions to {EXCLUDED_MANIFEST_PATH}")
    else:
        # Ensure the manifest exists even if empty
        pd.DataFrame(columns=['molecule_id', 'smiles', 'reason']).to_csv(EXCLUDED_MANIFEST_PATH, index=False)
        logger.info("No exclusions to write, but manifest file created.")

    # Ensure the log file exists even if no errors occurred (touch it)
    # The log_invalid_smiles function handles writing, but we ensure the file path is valid
    log_file_path = DATA_LOGS_DIR / "invalid_smiles.log"
    if not log_file_path.exists():
        log_file_path.touch()
        logger.info(f"Created empty log file at {log_file_path}")

def main():
    """Entry point for the script."""
    # Default paths based on project structure
    input_file = DATA_PROCESSED_DIR / "raw_data.csv" # Assuming this is the source from T008b
    if not input_file.exists():
        # Fallback to common name if raw_data.csv isn't there, or check data/raw
        input_file = PROJECT_ROOT / "data" / "raw" / "esol.csv"
    
    if not input_file.exists():
        logger = setup_logging()
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    output_file = DATA_PROCESSED_DIR / "persistence_images_10x10.csv"
    
    generate_tda_features_csv(str(input_file), str(output_file))

def setup_invalid_smiles_logger():
    """
    Setup a dedicated logger for invalid SMILES to write to data/logs/invalid_smiles.log.
    Returns the logger instance.
    """
    logger = logging.getLogger("invalid_smiles")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(DATA_LOGS_DIR / "invalid_smiles.log")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_invalid_smiles(logger: logging.Logger, smiles: str, reason: str):
    """Log an invalid SMILES entry to the specific logger."""
    logger.info(f"SMILES: {smiles} | Reason: {reason}")

if __name__ == "__main__":
    main()
