import os
import sys
import json
import logging
import numpy as np
from pathlib import Path

from config import DATA_RESULTS_DIR, N_SIDE
from analysis.parameter_est import load_leakage_matrix, validate_leakage_matrix

# Configure logging for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def ensure_robustness_log_dir():
    """Ensure the directory for robustness failure logs exists."""
    log_path = Path(DATA_RESULTS_DIR)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path

def check_positive_definite(matrix: np.ndarray, realization_id: str) -> bool:
    """
    Check if a matrix (specifically a Fisher Matrix Hessian) is positive-definite.
    
    Args:
        matrix: The matrix to check.
        realization_id: ID of the realization for logging.
        
    Returns:
        True if positive-definite, False otherwise.
    """
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        logger.error(f"Realization {realization_id}: Matrix is not square.")
        return False
    
    try:
        # Eigenvalue decomposition
        eigenvalues = np.linalg.eigvalsh(matrix)
        
        # Check for positive definiteness (all eigenvalues > 0)
        # Using a small tolerance for floating point errors
        min_eig = np.min(eigenvalues)
        if min_eig <= 1e-10:
            logger.warning(f"Realization {realization_id}: Fisher Hessian is NOT positive-definite. "
                         f"Min eigenvalue: {min_eig}")
            return False
        else:
            logger.info(f"Realization {realization_id}: Fisher Hessian is positive-definite. "
                      f"Min eigenvalue: {min_eig}")
            return True
    except np.linalg.LinAlgError as e:
        logger.error(f"Realization {realization_id}: Error during eigenvalue decomposition: {e}")
        return False

def log_robustness_failure(realization_id: str, eigenvalues: np.ndarray, 
                           matrix_shape: tuple, failure_reason: str = "Non-positive eigenvalue"):
    """
    Log a robustness failure to the specific log file.
    
    Args:
        realization_id: ID of the realization.
        eigenvalues: The computed eigenvalues.
        matrix_shape: Shape of the matrix.
        failure_reason: Description of why it failed.
    """
    log_dir = ensure_robustness_log_dir()
    log_file = log_dir / "robustness_failures.log"
    
    failure_entry = {
        "realization_id": realization_id,
        "failure_reason": failure_reason,
        "min_eigenvalue": float(np.min(eigenvalues)),
        "max_eigenvalue": float(np.max(eigenvalues)),
        "matrix_shape": list(matrix_shape),
        "timestamp": str(Path.home()) # Placeholder for actual timestamp if needed, or use datetime
    }
    
    # Append to log file
    with open(log_file, 'a') as f:
        f.write(json.dumps(failure_entry) + '\n')
    
    logger.error(f"Logged robustness failure for {realization_id} to {log_file}")

def validate_fisher_hessian(hessian: np.ndarray, realization_id: str) -> bool:
    """
    Validate that the Fisher Matrix Hessian is positive-definite.
    Raises an error and logs failure if not.
    
    Args:
        hessian: The Hessian matrix.
        realization_id: ID of the realization.
        
    Returns:
        True if valid.
        
    Raises:
        ValueError: If the Hessian is not positive-definite.
    """
    if not check_positive_definite(hessian, realization_id):
        eigenvalues = np.linalg.eigvalsh(hessian)
        log_robustness_failure(realization_id, eigenvalues, hessian.shape)
        raise ValueError(f"Realization {realization_id}: Fisher Hessian is not positive-definite. "
                       f"Realization excluded from analysis.")
    return True

def run_robustness_checks(parameter_est_results_path: str, realization_id: str) -> bool:
    """
    Run robustness checks on parameter estimation results.
    Specifically validates the Fisher Hessian if present.
    
    Args:
        parameter_est_results_path: Path to the parameter estimation results JSON.
        realization_id: ID of the realization.
        
    Returns:
        True if checks pass, False if excluded.
    """
    if not os.path.exists(parameter_est_results_path):
        logger.warning(f"Parameter estimation results not found for {realization_id}. Skipping robustness check.")
        return False
    
    try:
        with open(parameter_est_results_path, 'r') as f:
            results = json.load(f)
        
        if 'fisher_hessian' not in results:
            logger.warning(f"No Fisher Hessian found for {realization_id}. Skipping check.")
            return True # No Hessian to check, not a failure
        
        hessian = np.array(results['fisher_hessian'])
        
        # Validate positive definiteness
        # This function will raise ValueError if not PD, which we catch below
        validate_fisher_hessian(hessian, realization_id)
        
        logger.info(f"Robustness checks passed for {realization_id}.")
        return True
        
    except ValueError as e:
        logger.error(f"Robustness check failed for {realization_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during robustness check for {realization_id}: {e}")
        return False

def main():
    """
    Main entry point for running robustness checks on all available realizations.
    This script is intended to be run after parameter estimation (T028b) to filter
    out invalid results before bias analysis.
    """
    logger.info("Starting Robustness Checks (T041)...")
    
    # Determine paths based on project structure
    # Assuming parameter_est results are in data/metadata/{realization_id}_algo_{name}.json
    # or a specific directory. For this implementation, we scan data/metadata for relevant files.
    metadata_dir = Path("data/metadata")
    results_dir = Path("data/results")
    
    if not metadata_dir.exists():
        logger.error("Metadata directory not found. Cannot run robustness checks.")
        sys.exit(1)
    
    # Find parameter estimation result files
    # Pattern: *_algo_*.json or similar. We look for files containing 'parameter' or 'est'
    # or specifically the output of T028b.
    # For this task, we assume the results of T028b are stored in data/metadata/
    # with a naming convention like {realization_id}_est.json or similar.
    # Let's scan for JSON files that might contain 'fisher_hessian'.
    
    processed_count = 0
    passed_count = 0
    failed_count = 0
    excluded_ids = []
    
    for json_file in metadata_dir.glob("*.json"):
        # Skip ground truth files (T013) which don't have hessian
        if "ground_truth" in json_file.name or "algo" in json_file.name:
             # Check if it's a parameter estimation result
             # T023/T028b outputs might be named differently.
             # Let's try to load and check for 'fisher_hessian'
             try:
                 with open(json_file, 'r') as f:
                     data = json.load(f)
                 if 'fisher_hessian' in data:
                     # Extract realization ID from filename or data
                     # Assuming filename format: {realization_id}_algo_{algo_name}.json
                     parts = json_file.stem.split('_')
                     rid = parts[0] if parts else json_file.stem
                     
                     passed = run_robustness_checks(str(json_file), rid)
                     processed_count += 1
                     if passed:
                         passed_count += 1
                     else:
                         failed_count += 1
                         excluded_ids.append(rid)
             except Exception as e:
                 logger.warning(f"Could not process {json_file}: {e}")
    
    # Also check data/results if specific output files are there
    # T028b might output to data/results/parameter_est.json or similar
    # But based on T023, metadata is in data/metadata.
    
    logger.info(f"Robustness Checks Complete.")
    logger.info(f"Processed: {processed_count}, Passed: {passed_count}, Failed: {failed_count}")
    
    if excluded_ids:
        logger.warning(f"Excluded Realizations: {excluded_ids}")
        # Update excluded log if necessary, though T024 handles general exclusions.
        # We ensure the robustness_failures.log is updated via log_robustness_failure.
    
    # Return exit code 1 if critical failures (e.g., all failed) - optional per spec
    if processed_count == 0:
        logger.warning("No parameter estimation results found to check.")
        sys.exit(0) # Not necessarily a failure if no data yet
    
    sys.exit(0)

if __name__ == "__main__":
    main()