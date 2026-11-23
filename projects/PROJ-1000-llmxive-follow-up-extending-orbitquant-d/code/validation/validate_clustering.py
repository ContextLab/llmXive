import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path (assuming script runs from code/ or project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLUSTERING_REPORT_PATH = PROJECT_ROOT / "data" / "processed" / "clustering_report.json"

def validate_structure(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the top-level structure of the clustering report.
    Ensures required keys (layers, subsets, boundaries, matrices) are present.
    
    Args:
        data: The loaded JSON dictionary from clustering_report.json
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_keys = ['layers', 'subsets', 'boundaries', 'matrices']
    
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key: '{key}'")
    
    if not data.get('matrices'):
        errors.append("Matrices list is empty or missing.")
    
    if not data.get('layers'):
        errors.append("Layers list is empty or missing.")
    
    return len(errors) == 0, errors

def validate_data_types(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the data types of the clustering report fields.
    Ensures matrices is a list of arrays/lists, boundaries are numeric, etc.
    
    Args:
        data: The loaded JSON dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(data.get('matrices'), list):
        errors.append("Field 'matrices' must be a list.")
    else:
        for i, mat in enumerate(data['matrices']):
            if not isinstance(mat, (list, np.ndarray)):
                errors.append(f"Matrix at index {i} is not a list or numpy array.")
    
    if not isinstance(data.get('boundaries'), list):
        errors.append("Field 'boundaries' must be a list.")
    
    if not isinstance(data.get('layers'), list):
        errors.append("Field 'layers' must be a list.")
        
    return len(errors) == 0, errors

def validate_consistency(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates logical consistency:
    1. Number of matrices matches number of boundaries + 1 (if boundaries define intervals)
       OR matches number of subsets.
    2. Validates matrix dimensions are consistent.
    3. Validates orthogonality and unit norm of rotation matrices.
    
    Args:
        data: The loaded JSON dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    matrices = data.get('matrices', [])
    boundaries = data.get('boundaries', [])
    subsets = data.get('subsets', [])
    
    if not matrices:
        errors.append("No matrices found to validate consistency.")
        return False, errors
        
    # 1. Check count consistency
    # Assuming boundaries define K-1 cut points for K clusters, so len(matrices) should equal len(boundaries) + 1
    # OR simply len(matrices) should equal len(subsets)
    if len(subsets) > 0 and len(matrices) != len(subsets):
        errors.append(f"Matrix count ({len(matrices)}) does not match subset count ({len(subsets)}).")
    
    if len(boundaries) > 0 and len(matrices) != len(boundaries) + 1:
        # This is a common pattern, but we might just warn if it doesn't match perfectly
        # depending on how boundaries are defined in T022.
        # For safety, we check if it's a valid configuration.
        logger.warning(f"Matrix count ({len(matrices)}) != boundaries count + 1 ({len(boundaries) + 1}). Checking if valid...")
    
    # 2. Check dimension consistency
    if len(matrices) > 0:
        first_shape = np.array(matrices[0]).shape
        for i, mat in enumerate(matrices[1:], start=1):
            current_shape = np.array(mat).shape
            if current_shape != first_shape:
                errors.append(f"Matrix {i} shape {current_shape} differs from first matrix shape {first_shape}.")
    
    # 3. Validate Orthogonality and Unit Norm (The Core Task T045)
    # Rotation matrices R should satisfy R^T * R = I (Identity)
    # And columns (or rows, depending on convention) should be unit vectors.
    # We check R^T * R approx I.
    
    logger.info("Validating orthogonality and unit norm of rotation matrices...")
    ortho_errors = 0
    tolerance = 1e-5
    
    for i, mat in enumerate(matrices):
        mat_np = np.array(mat)
        
        # Check Unit Norm (L2 norm of each column should be 1)
        # If mat is (D, D), columns are mat[:, j]
        norms = np.linalg.norm(mat_np, axis=0)
        if not np.allclose(norms, 1.0, atol=tolerance):
            # Report the max deviation
            max_dev = np.max(np.abs(norms - 1.0))
            errors.append(f"Matrix {i} columns are not unit vectors. Max deviation: {max_dev:.2e}")
            ortho_errors += 1
        
        # Check Orthogonality (R^T * R = I)
        # R^T * R
        identity_check = np.dot(mat_np.T, mat_np)
        expected_identity = np.eye(identity_check.shape[0])
        
        if not np.allclose(identity_check, expected_identity, atol=tolerance):
            # Calculate Frobenius norm of the difference
            diff_norm = np.linalg.norm(identity_check - expected_identity, ord='fro')
            errors.append(f"Matrix {i} is not orthogonal. R^T*R deviation (Frobenius): {diff_norm:.2e}")
            ortho_errors += 1
    
    if ortho_errors > 0:
        logger.error(f"Found {ortho_errors} matrices failing orthogonality/unit norm checks.")
    else:
        logger.info("All rotation matrices are orthogonal and have unit norm.")
    
    return len(errors) == 0, errors

def validate_clustering_report(report_path: Optional[Path] = None) -> bool:
    """
    Main entry point to validate the clustering report.
    
    Args:
        report_path: Optional path to the report. Defaults to PROJECT_ROOT/data/processed/clustering_report.json
        
    Returns:
        True if all validations pass, False otherwise.
    """
    path = report_path or CLUSTERING_REPORT_PATH
    
    if not path.exists():
        logger.error(f"Clustering report not found at: {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON at {path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading file {path}: {e}")
        return False
    
    all_valid = True
    all_errors = []
    
    # Run validations
    valid, errors = validate_structure(data)
    if not valid:
        all_valid = False
        all_errors.extend([f"[Structure] {e}" for e in errors])
    
    valid, errors = validate_data_types(data)
    if not valid:
        all_valid = False
        all_errors.extend([f"[Data Types] {e}" for e in errors])
    
    valid, errors = validate_consistency(data)
    if not valid:
        all_valid = False
        all_errors.extend([f"[Consistency] {e}" for e in errors])
    
    if all_valid:
        logger.info("Validation PASSED: Clustering report is valid.")
    else:
        logger.error("Validation FAILED. Errors found:")
        for err in all_errors:
            logger.error(f"  - {err}")
    
    return all_valid

def main():
    """
    CLI entry point for T045 validation task.
    """
    logger.info(f"Starting Clustering Report Validation (T045)...")
    logger.info(f"Target file: {CLUSTERING_REPORT_PATH}")
    
    success = validate_clustering_report()
    
    if success:
        logger.info("T045 Validation Complete: SUCCESS")
        sys.exit(0)
    else:
        logger.error("T045 Validation Complete: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()