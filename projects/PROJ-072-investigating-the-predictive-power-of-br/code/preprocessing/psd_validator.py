import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from preprocessing.metadata import load_subject_status

logger = logging.getLogger(__name__)

# Constants for regularization
EPSILON = 1e-6
REGULARIZATION_FACTOR = 1e-4

def is_symmetric(matrix: np.ndarray, rtol: float = 1e-05, atol: float = 1e-08) -> bool:
    """Check if a matrix is symmetric within numerical tolerance."""
    return np.allclose(matrix, matrix.T, rtol=rtol, atol=atol)

def make_symmetric(matrix: np.ndarray) -> np.ndarray:
    """Force a matrix to be symmetric by averaging with its transpose."""
    return (matrix + matrix.T) / 2.0

def is_positive_semi_definite(matrix: np.ndarray) -> Tuple[bool, Optional[float]]:
    """
    Check if a matrix is positive semi-definite (PSD).
    
    Returns:
        Tuple of (is_psd, min_eigenvalue)
    """
    # Ensure symmetry first
    if not is_symmetric(matrix):
        logger.warning("Matrix is not symmetric. Cannot be PSD.")
        return False, None
    
    try:
        eigenvalues = np.linalg.eigvalsh(matrix)
        min_eig = np.min(eigenvalues)
        is_psd = min_eig >= -EPSILON  # Allow small numerical negative values
        return is_psd, min_eig
    except np.linalg.LinAlgError as e:
        logger.error(f"Eigenvalue decomposition failed: {e}")
        return False, None

def regularize_matrix(matrix: np.ndarray, factor: float = REGULARIZATION_FACTOR) -> np.ndarray:
    """
    Regularize a matrix to make it positive semi-definite.
    
    Adds a small multiple of the identity matrix to the diagonal.
    """
    if not is_symmetric(matrix):
        matrix = make_symmetric(matrix)
    
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    # Clip eigenvalues to be non-negative
    eigenvalues = np.maximum(eigenvalues, 0)
    # Reconstruct matrix
    return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

def validate_and_regularize_matrix(matrix: np.ndarray, subject_id: str) -> Tuple[np.ndarray, bool, str]:
    """
    Validate a connectivity matrix and regularize if necessary.
    
    Args:
        matrix: The connectivity matrix to validate
        subject_id: ID of the subject for logging purposes
        
    Returns:
        Tuple of (validated_matrix, was_regularized, status_message)
    """
    is_sym = is_symmetric(matrix)
    if not is_sym:
        matrix = make_symmetric(matrix)
        logger.info(f"Subject {subject_id}: Made matrix symmetric.")
    
    is_psd, min_eig = is_positive_semi_definite(matrix)
    
    if is_psd:
        return matrix, False, "valid"
    else:
        logger.warning(f"Subject {subject_id}: Matrix is not PSD (min eigenvalue: {min_eig}). Applying regularization.")
        regularized = regularize_matrix(matrix)
        # Verify regularization worked
        is_psd_after, _ = is_positive_semi_definite(regularized)
        if is_psd_after:
            return regularized, True, "regularized"
        else:
            # If regularization fails, try a stronger one
            logger.error(f"Subject {subject_id}: Initial regularization failed. Applying stronger regularization.")
            strong_factor = REGULARIZATION_FACTOR * 10
            strong_regularized = regularize_matrix(matrix, factor=strong_factor)
            is_psd_strong, _ = is_positive_semi_definite(strong_regularized)
            if is_psd_strong:
                return strong_regularized, True, "regularized_strong"
            else:
                logger.error(f"Subject {subject_id}: Failed to make matrix PSD even with strong regularization.")
                return matrix, False, "invalid"

def run_psd_validation_pipeline(subject_ids: list, matrices_dir: Path, output_dir: Path) -> dict:
    """
    Run PSD validation on all subject connectivity matrices.
    
    Args:
        subject_ids: List of subject IDs to process
        matrices_dir: Directory containing .npy matrix files
        output_dir: Directory to save validated matrices and logs
        
    Returns:
        Dictionary with validation statistics
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    validation_log = []
    stats = {
        "total_subjects": len(subject_ids),
        "valid": 0,
        "regularized": 0,
        "invalid": 0,
        "details": []
    }
    
    for sub_id in subject_ids:
        matrix_path = matrices_dir / f"{sub_id}_matrix.npy"
        if not matrix_path.exists():
            logger.warning(f"Matrix not found for {sub_id}. Skipping.")
            continue
        
        try:
            matrix = np.load(matrix_path)
            validated_matrix, was_regularized, status = validate_and_regularize_matrix(matrix, sub_id)
            
            # Save validated matrix
            output_path = output_dir / f"{sub_id}_matrix_validated.npy"
            np.save(output_path, validated_matrix)
            
            # Log result
            log_entry = {
                "subject_id": sub_id,
                "status": status,
                "regularized": was_regularized,
                "input_path": str(matrix_path),
                "output_path": str(output_path)
            }
            validation_log.append(log_entry)
            stats["details"].append(log_entry)
            
            if status == "valid":
                stats["valid"] += 1
            elif status.startswith("regularized"):
                stats["regularized"] += 1
            else:
                stats["invalid"] += 1
                
        except Exception as e:
            logger.error(f"Error processing {sub_id}: {e}")
            stats["invalid"] += 1
            validation_log.append({
                "subject_id": sub_id,
                "status": "error",
                "error": str(e)
            })
    
    # Save validation log
    log_path = output_dir / "psd_validation_log.json"
    with open(log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
    
    logger.info(f"PSD validation complete. Valid: {stats['valid']}, Regularized: {stats['regularized']}, Invalid: {stats['invalid']}")
    
    return stats

def main():
    """Main entry point for PSD validation pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load subject status to get valid subjects
    subject_status_path = Path("data/metadata/subject_status.csv")
    if not subject_status_path.exists():
        logger.error(f"Subject status file not found: {subject_status_path}")
        return
    
    subject_status = load_subject_status(subject_status_path)
    # Get subjects that are not excluded
    valid_subjects = [
        row['subject_id'] for _, row in subject_status.iterrows()
        if row['excluded'] == False
    ]
    
    if not valid_subjects:
        logger.warning("No valid subjects found for PSD validation.")
        return
    
    matrices_dir = Path("data/processed")
    output_dir = Path("data/processed/validated")
    
    stats = run_psd_validation_pipeline(valid_subjects, matrices_dir, output_dir)
    
    # Save summary stats
    summary_path = Path("data/metadata/psd_validation_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Validation summary saved to {summary_path}")

if __name__ == "__main__":
    main()