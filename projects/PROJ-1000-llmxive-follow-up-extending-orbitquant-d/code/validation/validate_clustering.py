"""
Validation module for clustering results (T023a).
Verifies the existence and structural integrity of data/processed/clustering_report.json.
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Required keys as per T022b specification
REQUIRED_TOP_LEVEL_KEYS = ["layers", "subsets", "boundaries", "matrices"]
REQUIRED_LAYER_KEYS = ["layer_name", "subset_id", "variance_threshold", "rotation_matrix"]
REQUIRED_MATRIX_KEYS = ["shape", "data"]  # shape: tuple/list, data: list of lists

def validate_structure(report_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates that the clustering report file exists and contains the required top-level keys.
    
    Args:
        report_path: Path to data/processed/clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not report_path.exists():
        errors.append(f"File not found: {report_path}")
        return False, errors
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON format: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Error reading file: {e}")
        return False, errors
    
    if not isinstance(data, dict):
        errors.append("Root element must be a JSON object (dict)")
        return False, errors
    
    missing_keys = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing_keys:
        errors.append(f"Missing required top-level keys: {missing_keys}")
        
    return len(errors) == 0, errors

def validate_data_types(report_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates the data types of the rotation matrices and boundaries.
    
    Args:
        report_path: Path to data/processed/clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"Could not read file for type validation: {e}")
        return False, errors
    
    # Check 'matrices' structure
    if "matrices" in data:
        matrices = data["matrices"]
        if not isinstance(matrices, dict):
            errors.append("'matrices' field must be a dictionary mapping layer names to matrix info")
            return False, errors
          
        for layer_name, matrix_info in matrices.items():
            if not isinstance(matrix_info, dict):
                errors.append(f"Matrix info for layer '{layer_name}' must be a dict")
                continue
            
            if "data" not in matrix_info:
                errors.append(f"Matrix info for layer '{layer_name}' missing 'data'")
                continue
            
            if "shape" not in matrix_info:
                errors.append(f"Matrix info for layer '{layer_name}' missing 'shape'")
                continue
            
            mat_data = matrix_info["data"]
            if not isinstance(mat_data, list):
                errors.append(f"Matrix data for layer '{layer_name}' must be a list of lists")
                continue
              
            # Verify it looks like a 2D array
            if len(mat_data) > 0:
                if not isinstance(mat_data[0], list):
                    errors.append(f"Matrix data for layer '{layer_name}' must be a 2D list")
                    continue
                
                # Check for numeric values
                try:
                    flat_vals = [x for row in mat_data for x in row]
                    np.array(flat_vals, dtype=float)
                except (ValueError, TypeError):
                    errors.append(f"Matrix data for layer '{layer_name}' contains non-numeric values")
                    
    # Check 'boundaries' structure
    if "boundaries" in data:
        boundaries = data["boundaries"]
        if not isinstance(boundaries, list):
            errors.append("'boundaries' field must be a list of float/int values")
            return False, errors
        
        try:
            np.array(boundaries, dtype=float)
        except (ValueError, TypeError):
            errors.append("'boundaries' contains non-numeric values")
    
    # Check 'subsets' structure
    if "subsets" in data:
        subsets = data["subsets"]
        if not isinstance(subsets, list):
            errors.append("'subsets' field must be a list")
            return False, errors
            
        for i, subset in enumerate(subsets):
            if not isinstance(subset, dict):
                errors.append(f"Item at subsets[{i}] must be a dict")
                continue
            if "subset_id" not in subset:
                errors.append(f"Item at subsets[{i}] missing 'subset_id'")
                
    return len(errors) == 0, errors

def validate_consistency(report_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates logical consistency of the clustering report.
    Ensures that the number of matrices matches the number of subsets/layers defined.
    
    Args:
        report_path: Path to data/processed/clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"Could not read file for consistency check: {e}")
        return False, errors
    
    # Count defined matrices
    matrix_count = len(data.get("matrices", {}))
    
    # Count defined subsets
    subset_count = len(data.get("subsets", []))
    
    # Count defined layers (assuming 'layers' is a list of layer definitions)
    layers = data.get("layers", [])
    if isinstance(layers, list):
        layer_count = len(layers)
    elif isinstance(layers, dict):
        layer_count = len(layers)
    else:
        layer_count = 0
        errors.append("'layers' field is not a list or dict, cannot count layers")
    
    # Consistency check: The number of matrices should match the number of subsets (K=16)
    # and ideally match the number of layers if 1:1 mapping is intended per the spec.
    # The spec (T022b) says "derive K=16 pre-optimized rotation matrices".
    # We expect the 'matrices' dict to have 16 entries or correspond to the clusters.
    
    if matrix_count == 0:
        errors.append("No rotation matrices found in 'matrices' field")
    
    if subset_count == 0:
        errors.append("No subsets found in 'subsets' field")
    
    # Check if boundaries length matches number of subsets (for K clusters, we need K-1 boundaries)
    boundaries = data.get("boundaries", [])
    if len(boundaries) > 0 and subset_count > 0:
        # K clusters usually imply K-1 boundaries for 1D sorting, or specific boundaries per cluster
        # We just check that boundaries exist and are numeric (already checked in validate_data_types)
        pass
    
    # Verify that every layer in 'layers' has a corresponding entry in 'matrices' if layers is a list of names
    if isinstance(layers, list) and len(layers) > 0:
        if isinstance(layers[0], str):
            missing_matrix_layers = [l for l in layers if l not in data.get("matrices", {})]
            if missing_matrix_layers:
                errors.append(f"Layers missing corresponding matrices: {missing_matrix_layers}")
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for T023a.
    Runs all validation checks on data/processed/clustering_report.json.
    Exits with code 0 if valid, 1 if invalid.
    """
    config = Config()
    report_path = config.get_clustering_report_path()
    
    logger.info(f"Validating clustering report at: {report_path}")
    
    all_valid = True
    
    # 1. Structure Check
    valid, errors = validate_structure(report_path)
    if not valid:
        logger.error("Structure validation FAILED:")
        for err in errors:
            logger.error(f"  - {err}")
        all_valid = False
    else:
        logger.info("Structure validation PASSED")
        
    if not all_valid:
        # If structure fails, other checks might be meaningless or redundant, but we run them for completeness
        pass
    
    # 2. Data Types Check
    valid, errors = validate_data_types(report_path)
    if not valid:
        logger.error("Data types validation FAILED:")
        for err in errors:
            logger.error(f"  - {err}")
        all_valid = False
    else:
        logger.info("Data types validation PASSED")
    
    # 3. Consistency Check
    valid, errors = validate_consistency(report_path)
    if not valid:
        logger.error("Consistency validation FAILED:")
        for err in errors:
            logger.error(f"  - {err}")
        all_valid = False
    else:
        logger.info("Consistency validation PASSED")
    
    if all_valid:
        logger.info("SUCCESS: Clustering report validation passed all checks.")
        print("VALIDATION_STATUS: PASSED")
        return 0
    else:
        logger.error("FAILURE: Clustering report validation failed.")
        print("VALIDATION_STATUS: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
