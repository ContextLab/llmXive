"""
Positive Semi-Definite (PSD) validation and regularization module.

This module ensures that connectivity matrices generated during preprocessing
are mathematically valid (symmetric and positive semi-definite).
If a matrix fails the PSD check, a minimal regularization (adding a small
value to the diagonal) is applied to make it PSD. All anomalies are logged.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

# Configure logging to be consistent with other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default regularization parameters
DEFAULT_EPSILON = 1e-5
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_INCREMENT_FACTOR = 10.0

def is_symmetric(matrix: np.ndarray, tol: float = 1e-8) -> bool:
    """
    Check if a matrix is symmetric within a given tolerance.

    Args:
        matrix: The matrix to check.
        tol: Tolerance for floating point comparison.

    Returns:
        True if symmetric, False otherwise.
    """
    if matrix.shape[0] != matrix.shape[1]:
        return False
    return np.allclose(matrix, matrix.T, atol=tol)

def make_symmetric(matrix: np.ndarray) -> np.ndarray:
    """
    Enforce symmetry by averaging the matrix with its transpose.

    Args:
        matrix: The input matrix.

    Returns:
        A symmetric version of the matrix.
    """
    if not is_symmetric(matrix):
        logger.debug("Enforcing symmetry on matrix.")
        return (matrix + matrix.T) / 2.0
    return matrix

def is_positive_semi_definite(matrix: np.ndarray) -> bool:
    """
    Check if a matrix is positive semi-definite (PSD).

    A matrix is PSD if all its eigenvalues are non-negative.
    We use a small tolerance for numerical stability.

    Args:
        matrix: The matrix to check.

    Returns:
        True if PSD, False otherwise.
    """
    try:
        # Ensure symmetry first for eigenvalue calculation
        sym_matrix = make_symmetric(matrix)
        eigenvalues = np.linalg.eigvalsh(sym_matrix)
        return np.all(eigenvalues >= -1e-10)
    except np.linalg.LinAlgError:
        logger.warning("Eigenvalue decomposition failed. Matrix is likely not PSD.")
        return False

def regularize_matrix(
    matrix: np.ndarray,
    epsilon: float = DEFAULT_EPSILON,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    increment_factor: float = DEFAULT_INCREMENT_FACTOR
) -> Tuple[np.ndarray, int]:
    """
    Regularize a matrix to make it positive semi-definite.

    This function adds a small value (epsilon) to the diagonal elements
    iteratively until the matrix becomes PSD or max_iterations is reached.

    Args:
        matrix: The input matrix (assumed symmetric or made symmetric).
        epsilon: Initial value to add to the diagonal.
        max_iterations: Maximum number of regularization attempts.
        increment_factor: Factor by which epsilon is increased per iteration.

    Returns:
        A tuple containing the regularized matrix and the number of iterations performed.
        If the matrix was already PSD, iterations will be 0.
    """
    if is_positive_semi_definite(matrix):
        return matrix, 0

    logger.info(f"Matrix is not PSD. Starting regularization with epsilon={epsilon}.")
    current_epsilon = epsilon
    sym_matrix = make_symmetric(matrix.copy())
    iterations = 0

    for i in range(max_iterations):
        iterations += 1
        # Add epsilon to diagonal
        diag_indices = np.diag_indices_from(sym_matrix)
        sym_matrix[diag_indices] += current_epsilon

        if is_positive_semi_definite(sym_matrix):
            logger.info(f"Matrix became PSD after {iterations} iteration(s) with epsilon={current_epsilon}.")
            return sym_matrix, iterations

        current_epsilon *= increment_factor

    logger.error(f"Failed to make matrix PSD after {max_iterations} iterations. Last epsilon: {current_epsilon}.")
    # Return the best effort matrix even if not fully PSD, or raise an error depending on strictness.
    # For robustness, we return the last attempt but log the failure.
    return sym_matrix, iterations

def validate_and_regularize_matrix(
    matrix: np.ndarray,
    subject_id: str,
    output_dir: Optional[Path] = None,
    anomaly_log_path: Optional[Path] = None
) -> Tuple[np.ndarray, bool]:
    """
    Validate a connectivity matrix for PSD property and regularize if necessary.

    Args:
        matrix: The input connectivity matrix.
        subject_id: Identifier for the subject (for logging).
        output_dir: Directory to save the corrected matrix (optional).
        anomaly_log_path: Path to the anomaly log file (optional).

    Returns:
        A tuple of (processed_matrix, was_regularized).
    """
    was_regularized = False
    subject_prefix = f"[Subject: {subject_id}]"

    # Step 1: Ensure symmetry
    if not is_symmetric(matrix):
        logger.warning(f"{subject_prefix} Matrix is not symmetric. Enforcing symmetry.")
        matrix = make_symmetric(matrix)

    # Step 2: Check PSD
    if not is_positive_semi_definite(matrix):
        logger.warning(f"{subject_prefix} Matrix is NOT positive semi-definite. Applying regularization.")
        matrix, iterations = regularize_matrix(matrix)
        was_regularized = True

        # Log anomaly details
        if anomaly_log_path:
            log_entry = {
                "subject_id": subject_id,
                "issue": "non_psd",
                "action": "regularization_applied",
                "iterations": iterations
            }
            log_file_exists = anomaly_log_path.exists()
            with open(anomaly_log_path, 'a') as f:
                if not log_file_exists:
                    f.write(json.dumps({"records": []}) + "\n")
                
                # Read existing, append, write back (simple approach for small logs)
                try:
                    with open(anomaly_log_path, 'r') as rf:
                        content = rf.read().strip()
                        if content:
                            data = json.loads(content)
                            if "records" not in data:
                                data["records"] = []
                            data["records"].append(log_entry)
                        else:
                            data = {"records": [log_entry]}
                except (json.JSONDecodeError, FileNotFoundError):
                    data = {"records": [log_entry]}

                with open(anomaly_log_path, 'w') as wf:
                    json.dump(data, wf, indent=2)

    return matrix, was_regularized

def run_psd_validation_pipeline(
    input_dir: Path,
    output_dir: Path,
    anomaly_log_path: Optional[Path] = None
) -> int:
    """
    Run PSD validation and regularization on all .npy matrices in a directory.

    Args:
        input_dir: Directory containing input matrices.
        output_dir: Directory to save corrected matrices.
        anomaly_log_path: Path to the anomaly log file.

    Returns:
        Number of matrices processed.
    """
    if anomaly_log_path is None:
        anomaly_log_path = Path("data/metadata/psd_anomalies.json")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize or clear the anomaly log if it's the first run in this session
    # Note: We append to the log to preserve history, but ensure valid JSON structure
    if not anomaly_log_path.exists():
        anomaly_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(anomaly_log_path, 'w') as f:
            json.dump({"records": []}, f)

    processed_count = 0
    npy_files = list(input_dir.glob("*.npy"))
    
    if not npy_files:
        logger.warning(f"No .npy files found in {input_dir}")
        return 0

    for file_path in npy_files:
        subject_id = file_path.stem
        try:
            matrix = np.load(file_path)
            logger.info(f"Processing {subject_id}...")
            
            processed_matrix, was_regularized = validate_and_regularize_matrix(
                matrix, subject_id, output_dir, anomaly_log_path
            )
            
            output_path = output_dir / f"{subject_id}_psd_corrected.npy"
            np.save(output_path, processed_matrix)
            
            if was_regularized:
                logger.info(f"Saved corrected matrix for {subject_id} to {output_path}")
            else:
                logger.debug(f"Matrix for {subject_id} was already valid.")
            
            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            continue

    return processed_count

def main():
    """
    Entry point for the PSD validation script.
    Expects to be run from the project root.
    """
    input_dir = Path("data/processed")
    output_dir = Path("data/processed/psd_validated")
    anomaly_log_path = Path("data/metadata/psd_anomalies.json")

    logger.info(f"Starting PSD validation pipeline.")
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Anomaly log: {anomaly_log_path}")

    count = run_psd_validation_pipeline(input_dir, output_dir, anomaly_log_path)
    logger.info(f"Pipeline completed. Processed {count} matrices.")

if __name__ == "__main__":
    main()
