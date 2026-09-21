import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected paths based on project structure
CLUSTERING_REPORT_PATH = Path("data/processed/clustering_report.json")

# Required keys for the clustering report
REQUIRED_TOP_LEVEL_KEYS = {"layers", "subsets", "boundaries", "matrices"}
REQUIRED_LAYER_KEYS = {"name", "subset_index", "boundary", "matrix"}

def validate_structure(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the top-level structure and required keys of the clustering report.
    
    Args:
        report_data: The dictionary loaded from clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(report_data, dict):
        errors.append("Report data is not a dictionary.")
        return False, errors
    
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(report_data.keys())
    if missing_keys:
        errors.append(f"Missing required top-level keys: {missing_keys}")
    
    # Check 'layers' structure
    if "layers" in report_data:
        if not isinstance(report_data["layers"], list):
            errors.append("'layers' must be a list.")
        else:
            for i, layer_entry in enumerate(report_data["layers"]):
                if not isinstance(layer_entry, dict):
                    errors.append(f"Layer entry at index {i} is not a dictionary.")
                    continue
                
                missing_layer_keys = REQUIRED_LAYER_KEYS - set(layer_entry.keys())
                if missing_layer_keys:
                    errors.append(f"Layer entry at index {i} missing keys: {missing_layer_keys}")
    
    # Check 'matrices' structure
    if "matrices" in report_data:
        if not isinstance(report_data["matrices"], list):
            errors.append("'matrices' must be a list.")
        else:
            for i, matrix_entry in enumerate(report_data["matrices"]):
                if not isinstance(matrix_entry, dict):
                    errors.append(f"Matrix entry at index {i} is not a dictionary.")
                    continue
                if "layer_name" not in matrix_entry:
                    errors.append(f"Matrix entry at index {i} missing 'layer_name'.")
    
    return len(errors) == 0, errors

def validate_data_types(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that the data types within the report are correct (e.g., matrices are lists/arrays).
    
    Args:
        report_data: The dictionary loaded from clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if "matrices" in report_data:
        for i, matrix_entry in enumerate(report_data["matrices"]):
            if "matrix_data" in matrix_entry:
                # Check if matrix_data is a list or can be converted to numpy
                if not isinstance(matrix_entry["matrix_data"], (list, np.ndarray)):
                    errors.append(f"Matrix entry {i} 'matrix_data' is not a list or numpy array.")
            if "shape" in matrix_entry:
                if not isinstance(matrix_entry["shape"], (tuple, list)) or len(matrix_entry["shape"]) != 2:
                    errors.append(f"Matrix entry {i} 'shape' is invalid.")
    
    if "boundaries" in report_data:
        if not isinstance(report_data["boundaries"], (list, dict)):
            errors.append("'boundaries' must be a list or dictionary.")
    
    return len(errors) == 0, errors

def validate_consistency(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates logical consistency between layers, subsets, and matrices.
    Ensures that every layer references a valid subset and matrix index.
    
    Args:
        report_data: The dictionary loaded from clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Extract unique subset indices and matrix indices referenced in layers
    if "layers" in report_data:
        layer_subset_indices = set()
        layer_matrix_indices = set()
        
        for layer_entry in report_data["layers"]:
            if "subset_index" in layer_entry:
                layer_subset_indices.add(layer_entry["subset_index"])
            if "matrix_index" in layer_entry:
                layer_matrix_indices.add(layer_entry["matrix_index"])
        
        # Verify subsets exist
        if "subsets" in report_data:
            if isinstance(report_data["subsets"], list):
                valid_subset_indices = set(range(len(report_data["subsets"])))
                invalid_subsets = layer_subset_indices - valid_subset_indices
                if invalid_subsets:
                    errors.append(f"Layers reference non-existent subset indices: {invalid_subsets}")
            elif isinstance(report_data["subsets"], dict):
                valid_subset_indices = set(report_data["subsets"].keys())
                # Convert to int if keys are strings representing ints
                valid_subset_indices_int = {int(k) if isinstance(k, str) and k.isdigit() else k for k in valid_subset_indices}
                invalid_subsets = layer_subset_indices - valid_subset_indices_int
                if invalid_subsets:
                    errors.append(f"Layers reference non-existent subset keys: {invalid_subsets}")
        
        # Verify matrices exist
        if "matrices" in report_data:
            if isinstance(report_data["matrices"], list):
                valid_matrix_indices = set(range(len(report_data["matrices"])))
                invalid_matrices = layer_matrix_indices - valid_matrix_indices
                if invalid_matrices:
                    errors.append(f"Layers reference non-existent matrix indices: {invalid_matrices}")
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for the validation script.
    Checks for file existence and runs all validation steps.
    """
    logger.info("Starting clustering report validation...")
    
    # 1. Check file existence
    if not CLUSTERING_REPORT_PATH.exists():
        logger.error(f"Clustering report not found at: {CLUSTERING_REPORT_PATH}")
        logger.error("Validation FAILED. Ensure T022 has completed successfully and generated the file.")
        sys.exit(1)
    
    logger.info(f"Found clustering report at: {CLUSTERING_REPORT_PATH}")
    
    # 2. Load JSON
    try:
        with open(CLUSTERING_REPORT_PATH, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        sys.exit(1)
    
    # 3. Run validations
    all_passed = True
    
    # Structure validation
    is_valid, errors = validate_structure(report_data)
    if not is_valid:
        all_passed = False
        for err in errors:
            logger.error(f"Structure Error: {err}")
    else:
        logger.info("Structure validation PASSED.")
    
    # Data type validation
    is_valid, errors = validate_data_types(report_data)
    if not is_valid:
        all_passed = False
        for err in errors:
            logger.error(f"Data Type Error: {err}")
    else:
        logger.info("Data Type validation PASSED.")
    
    # Consistency validation
    is_valid, errors = validate_consistency(report_data)
    if not is_valid:
        all_passed = False
        for err in errors:
            logger.error(f"Consistency Error: {err}")
    else:
        logger.info("Consistency validation PASSED.")
    
    # Final Result
    if all_passed:
        logger.info("VALIDATION SUCCESSFUL: Clustering report is valid. Proceeding to Phase 3.")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED: Clustering report has errors. Aborting Phase 3.")
        sys.exit(1)

if __name__ == "__main__":
    main()