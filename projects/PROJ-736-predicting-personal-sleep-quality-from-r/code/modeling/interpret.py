import os
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from scipy import sparse
from utils.logging import log_stage_start, log_stage_complete, log_stage_error
from config import get_paths

def load_model_coefficients(model_path: str) -> np.ndarray:
    """Load ElasticNet coefficients from a .npy file."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Coefficients file not found: {model_path}")
    coeffs = np.load(model_path)
    return coeffs

def load_feature_names(feature_names_path: str) -> List[str]:
    """Load feature names (edge labels) from a .txt or .json file."""
    if not os.path.exists(feature_names_path):
        raise FileNotFoundError(f"Feature names file not found: {feature_names_path}")
    
    ext = os.path.splitext(feature_names_path)[1]
    if ext == '.json':
        with open(feature_names_path, 'r') as f:
            return json.load(f)
    else:
        with open(feature_names_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]

def extract_nonzero_edges(coefficients: np.ndarray, feature_names: List[str], threshold: float = 1e-6) -> List[Tuple[str, float]]:
    """Extract edges with non-zero coefficients."""
    nonzero_indices = np.where(np.abs(coefficients) > threshold)[0]
    edges = []
    for idx in nonzero_indices:
        if idx < len(feature_names):
          edges.append((feature_names[idx], float(coefficients[idx])))
        else:
          # Fallback for index out of bounds
          edges.append((f"edge_{idx}", float(coefficients[idx])))
    return edges

def load_atlas_coordinates(atlas_path: str) -> Dict[str, Tuple[float, float, float]]:
    """Load Schaefer atlas coordinates (MNI) from a TSV or JSON file."""
    # Assuming a simple mapping file exists or is generated during preprocessing
    # For robustness, if file doesn't exist, return empty dict to trigger fallback logic
    if not os.path.exists(atlas_path):
        return {}
    
    coords = {}
    ext = os.path.splitext(atlas_path)[1]
    if ext == '.json':
        with open(atlas_path, 'r') as f:
            data = json.load(f)
            for node, val in data.items():
                coords[node] = tuple(val)
    elif ext == '.tsv':
        with open(atlas_path, 'r') as f:
            header = f.readline().strip().split('\t')
            # Expecting: node, x, y, z
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    coords[parts[0]] = (float(parts[1]), float(parts[2]), float(parts[3]))
    return coords

def map_edges_to_coordinates(edges: List[Tuple[str, float]], atlas_coords: Dict[str, Tuple[float, float, float]]) -> List[Tuple[Tuple[float, float, float], Tuple[float, float, float], float]]:
    """
    Map edge strings (e.g., 'NodeA-NodeB') to coordinate pairs.
    Returns list of ((x1, y1, z1), (x2, y2, z2), weight).
    """
    mapped_edges = []
    for edge_str, weight in edges:
        try:
            # Expect format "NodeA-NodeB"
            parts = edge_str.split('-')
            if len(parts) != 2:
                raise ValueError(f"Invalid edge format: {edge_str}")
            
            node_a, node_b = parts[0], parts[1]
            
            if node_a not in atlas_coords:
                raise KeyError(f"Node {node_a} not found in atlas")
            if node_b not in atlas_coords:
                raise KeyError(f"Node {node_b} not found in atlas")
            
            coord_a = atlas_coords[node_a]
            coord_b = atlas_coords[node_b]
            
            mapped_edges.append((coord_a, coord_b, weight))
            
        except (KeyError, ValueError) as e:
            # IMPLEMENTATION FOR T030: Handle failed edge mappings
            log_stage_error("map_edges_to_coordinates", f"Failed to map edge '{edge_str}': {str(e)}")
            # Continue processing other edges instead of crashing
            continue
    
    return mapped_edges

def save_interpreted_edges(mapped_edges: List[Tuple[Tuple[float, float, float], Tuple[float, float, float], float]], output_path: str):
    """Save mapped edges to a JSON file for visualization."""
    data = []
    for (c1, c2, w) in mapped_edges:
        data.append({
            "start": {"x": c1[0], "y": c1[1], "z": c1[2]},
            "end": {"x": c2[0], "y": c2[1], "z": c2[2]},
            "weight": w
        })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_interpretation(coefficients_path: str, feature_names_path: str, atlas_path: str, output_path: str) -> int:
    """
    Main orchestration for interpretation.
    Returns number of successfully mapped edges.
    """
    log_stage_start("interpretation", "Extracting non-zero coefficients and mapping to brain edges")
    
    try:
        coeffs = load_model_coefficients(coefficients_path)
        feature_names = load_feature_names(feature_names_path)
        atlas_coords = load_atlas_coordinates(atlas_path)
        
        edges = extract_nonzero_edges(coeffs, feature_names)
        
        if not edges:
            log_stage_error("interpretation", "No non-zero coefficients found.")
            # Save empty result
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump([], f)
            return 0
        
        mapped_edges = map_edges_to_coordinates(edges, atlas_coords)
        save_interpreted_edges(mapped_edges, output_path)
        
        log_stage_complete("interpretation", f"Successfully mapped {len(mapped_edges)} out of {len(edges)} edges.")
        return len(mapped_edges)
        
    except Exception as e:
        log_stage_error("interpretation", str(e))
        raise

def main():
    """Entry point for interpretation script."""
    paths = get_paths()
    coeffs_path = paths['model_coefficients'] # Assuming this key exists in config
    features_path = paths['feature_names']
    atlas_path = paths['atlas_coords']
    output_path = str(paths['data_results'] / 'interpreted_edges.json')
    
    # Fallback for paths if not explicitly in config, using standard project structure
    if not os.path.exists(coeffs_path):
        coeffs_path = str(paths['data_processed'] / 'model_coefficients.npy')
    if not os.path.exists(features_path):
        features_path = str(paths['data_processed'] / 'feature_names.txt')
    if not os.path.exists(atlas_path):
        atlas_path = str(paths['data_processed'] / 'schaefer_coords.tsv')

    run_interpretation(coeffs_path, features_path, atlas_path, output_path)

if __name__ == "__main__":
    main()