import os
import sys
import json
import logging
import time
import traceback
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import networkx as nx
from rdkit import Chem
from rdkit.Chem import AllChem
from scipy.spatial.distance import pdist, squareform

# Import from local utils
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
    compute_shortest_path_matrix,
    build_shortest_path_filtration,
    compute_persistence_diagram,
    handle_empty_diagram,
    compute_betti_numbers,
    get_topological_features
)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging for the TDA computation pipeline."""
    logger = logging.getLogger("tda_computation")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def vectorize_diagram_to_image(
    diagram: List[tuple],
    resolution: int = 10,
    xlim: tuple = (0, 10),
    ylim: tuple = (0, 10)
) -> np.ndarray:
    """
    Convert a persistence diagram to a persistence image.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Grid resolution (resolution x resolution).
        xlim: X-axis limits (birth).
        ylim: Y-axis limits (death).
        
    Returns:
        2D numpy array representing the persistence image.
    """
    if not diagram:
        return np.zeros((resolution, resolution))
    
    births = np.array([d[0] for d in diagram])
    deaths = np.array([d[1] for d in diagram])
    
    # Create grid
    x_edges = np.linspace(xlim[0], xlim[1], resolution + 1)
    y_edges = np.linspace(ylim[0], ylim[1], resolution + 1)
    
    image = np.zeros((resolution, resolution))
    
    for birth, death in diagram:
        if death <= birth:
            continue
        
        # Find bin indices
        x_idx = np.searchsorted(x_edges, birth) - 1
        y_idx = np.searchsorted(y_edges, death) - 1
        
        if 0 <= x_idx < resolution and 0 <= y_idx < resolution:
            # Weight by persistence
            persistence = death - birth
            image[y_idx, x_idx] += persistence
    
    return image

def flatten_image(image: np.ndarray) -> np.ndarray:
    """Flatten a 2D persistence image to a 1D feature vector."""
    return image.flatten()

def compute_persistence_features(
    diagram: List[tuple],
    resolution: int = 10
) -> Dict[str, float]:
    """
    Compute topological features from a persistence diagram.
    
    Args:
        diagram: List of (birth, death) tuples.
        resolution: Resolution for persistence image.
        
    Returns:
        Dictionary of topological features.
    """
    features = {}
    
    if not diagram:
        features['num_features'] = 0
        features['total_persistence'] = 0.0
        features['max_persistence'] = 0.0
        features['mean_persistence'] = 0.0
        features['image_features'] = []
        return features
    
    births = np.array([d[0] for d in diagram])
    deaths = np.array([d[1] for d in diagram])
    persistences = deaths - births
    
    features['num_features'] = len(diagram)
    features['total_persistence'] = float(np.sum(persistences))
    features['max_persistence'] = float(np.max(persistences))
    features['mean_persistence'] = float(np.mean(persistences))
    
    # Generate persistence image
    image = vectorize_diagram_to_image(diagram, resolution=resolution)
    features['image_features'] = flatten_image(image).tolist()
    
    return features

def generate_tda_features_csv(
    smiles_list: List[str],
    output_path: Path,
    resolutions: List[int] = [10, 20, 30],
    log_path: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    state_path: Optional[Path] = None
) -> None:
    """
    Generate TDA features CSV for a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings.
        output_path: Path to output CSV file.
        resolutions: List of grid resolutions for persistence images.
        log_path: Path to invalid SMILES log file.
        manifest_path: Path to excluded SMILES manifest CSV.
        state_path: Path to project state YAML file.
    """
    logger = setup_logging(log_path)
    
    # Setup invalid SMILES logger if log_path provided
    invalid_logger = None
    if log_path:
        invalid_logger = setup_invalid_smiles_logger(log_path)
    
    # Track invalid SMILES for manifest
    invalid_smiles_records = []
    
    # Prepare data structures for output
    all_features = []
    
    logger.info(f"Processing {len(smiles_list)} molecules...")
    
    for idx, smiles in enumerate(smiles_list):
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(smiles_list)} molecules")
        
        # Check if molecule is valid
        if not is_valid_molecule(smiles):
            # Log the invalid SMILES
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, "Invalid RDKit molecule")
            
            # Record for manifest
            invalid_smiles_records.append({
                'index': idx,
                'smiles': smiles,
                'reason': 'Invalid RDKit molecule'
            })
            continue
        
        try:
            # Build molecular graph
            mol = Chem.MolFromSmiles(smiles)
            graph = build_molecular_graph(mol)
            
            if graph is None or not validate_graph_structure(graph):
                if invalid_logger:
                    log_invalid_smiles(invalid_logger, smiles, "Invalid graph structure")
                invalid_smiles_records.append({
                    'index': idx,
                    'smiles': smiles,
                    'reason': 'Invalid graph structure'
                })
                continue
            
            # Compute shortest path matrix
            try:
                dist_matrix = compute_shortest_path_matrix(graph)
            except Exception as e:
                if invalid_logger:
                    log_invalid_smiles(invalid_logger, smiles, f"Shortest path computation failed: {str(e)}")
                invalid_smiles_records.append({
                    'index': idx,
                    'smiles': smiles,
                    'reason': f'Shortest path computation failed: {str(e)}'
                })
                continue
            
            # Build filtration and compute diagram
            filtration = build_shortest_path_filtration(dist_matrix)
            diagram = compute_persistence_diagram(filtration)
            
            # Handle empty diagram
            if not diagram:
                diagram = handle_empty_diagram()
            
            # Compute features for each resolution
            row_data = {
                'smiles': smiles,
                'num_nodes': graph.number_of_nodes(),
                'num_edges': graph.number_of_edges()
            }
            
            for res in resolutions:
                features = compute_persistence_features(diagram, resolution=res)
                
                # Add scalar features
                row_data[f'num_features_{res}'] = features['num_features']
                row_data[f'total_persistence_{res}'] = features['total_persistence']
                row_data[f'max_persistence_{res}'] = features['max_persistence']
                row_data[f'mean_persistence_{res}'] = features['mean_persistence']
                
                # Add image features (flattened)
                for i, val in enumerate(features['image_features']):
                    row_data[f'img_{res}_{i}'] = val
            
            all_features.append(row_data)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            if invalid_logger:
                log_invalid_smiles(invalid_logger, smiles, error_msg)
            invalid_smiles_records.append({
                'index': idx,
                'smiles': smiles,
                'reason': error_msg
            })
            logger.error(f"Error processing molecule {idx}: {error_msg}")
            continue
    
    # Write main features CSV
    if all_features:
        df = pd.DataFrame(all_features)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(all_features)} valid molecules to {output_path}")
    else:
        logger.warning("No valid molecules processed. Output CSV will be empty.")
        pd.DataFrame().to_csv(output_path, index=False)
    
    # Write invalid SMILES manifest if there were any
    if invalid_smiles_records and manifest_path:
        manifest_df = pd.DataFrame(invalid_smiles_records)
        manifest_df.to_csv(manifest_path, index=False)
        logger.info(f"Wrote {len(invalid_smiles_records)} excluded SMILES to {manifest_path}")
        
        # Update state file with manifest hash
        if state_path and state_path.exists():
            try:
                # Compute hash of manifest file
                with open(manifest_path, 'rb') as f:
                    manifest_hash = hashlib.sha256(f.read()).hexdigest()
                
                # Load current state
                import yaml
                with open(state_path, 'r') as f:
                    state_data = yaml.safe_load(f) or {}
                
                # Update state with manifest hash
                if 'excluded_smiles_manifest' not in state_data:
                    state_data['excluded_smiles_manifest'] = {}
                
                state_data['excluded_smiles_manifest']['file'] = str(manifest_path)
                state_data['excluded_smiles_manifest']['sha256'] = manifest_hash
                state_data['excluded_smiles_manifest']['count'] = len(invalid_smiles_records)
                
                # Write updated state
                with open(state_path, 'w') as f:
                    yaml.dump(state_data, f, default_flow_style=False)
                
                logger.info(f"Updated state file with manifest hash: {manifest_hash}")
            except Exception as e:
                logger.error(f"Failed to update state file: {str(e)}")
    elif invalid_smiles_records and not manifest_path:
        logger.warning("Invalid SMILES found but no manifest path provided.")

def main():
    """Main entry point for TDA computation."""
    # Example usage - in practice, paths would come from config or CLI args
    # This is a placeholder for the actual execution flow
    print("TDA Computation Module Loaded")
    print("Use generate_tda_features_csv to process SMILES lists")

if __name__ == "__main__":
    main()
