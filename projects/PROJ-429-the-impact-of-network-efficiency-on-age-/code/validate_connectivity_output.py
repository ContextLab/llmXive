import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from config import ensure_dirs, get_config_summary
from network.connectivity import load_epochs_from_file

# Standard 10-20 system channel count (approximate for validation)
# Common high-density montages: 64, 128. Standard 10-20 is 21-25 channels.
# We validate against a reasonable range for standard EEG systems.
VALID_DIMENSIONS = list(range(19, 130))  # 19 (minimum standard) to 128 (high density)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_connectivity_matrix(file_path: Path) -> np.ndarray:
    """Load a .npy connectivity matrix file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Connectivity matrix file not found: {file_path}")
    
    try:
        matrix = np.load(file_path)
        return matrix
    except Exception as e:
        raise RuntimeError(f"Failed to load matrix from {file_path}: {e}")

def validate_matrix_dimensions(matrix: np.ndarray, file_path: Path) -> Tuple[bool, str]:
    """
    Validate that the matrix dimensions match expected EEG electrode systems.
    Returns (is_valid, message).
    """
    if matrix.ndim != 2:
        return False, f"Matrix must be 2D, got {matrix.ndim}D"
    
    rows, cols = matrix.shape
    if rows != cols:
        return False, f"Matrix must be square, got shape {matrix.shape}"
    
    if rows not in VALID_DIMENSIONS:
        # Allow a specific check for common standard montages if needed
        # For now, flag if it's outside the plausible range for standard EEG
        return False, f"Matrix dimension {rows} not in expected range {VALID_DIMENSIONS}. " \
                      f"Expected standard EEG system (e.g., 19, 21, 64, 128 channels)."
    
    return True, f"Valid dimensions: {matrix.shape}"

def validate_non_nan_values(matrix: np.ndarray, file_path: Path) -> Tuple[bool, str]:
    """
    Validate that the matrix contains no NaN values.
    Returns (is_valid, message).
    """
    nan_count = np.isnan(matrix).sum()
    if nan_count > 0:
        return False, f"Matrix contains {nan_count} NaN values"
    
    # Also check for Inf
    inf_count = np.isinf(matrix).sum()
    if inf_count > 0:
        return False, f"Matrix contains {inf_count} Inf values"
    
    return True, "No NaN or Inf values found"

def validate_connectivity_matrices(matrices_dir: Path) -> Dict[str, Any]:
    """
    Validate all .npy files in the connectivity matrices directory.
    Returns a validation report.
    """
    if not matrices_dir.exists():
        return {
            "status": "error",
            "message": f"Connectivity matrices directory not found: {matrices_dir}",
            "files_checked": 0
        }
    
    npy_files = list(matrices_dir.glob("*.npy"))
    if not npy_files:
        return {
            "status": "warning",
            "message": "No .npy files found in connectivity matrices directory",
            "files_checked": 0
        }
    
    results = []
    all_valid = True
    
    for file_path in npy_files:
        file_result = {
            "file": str(file_path.name),
            "valid": False,
            "checks": {}
        }
        
        try:
            matrix = load_connectivity_matrix(file_path)
            
            # Check dimensions
            dim_valid, dim_msg = validate_matrix_dimensions(matrix, file_path)
            file_result["checks"]["dimensions"] = {
                "valid": dim_valid,
                "message": dim_msg,
                "shape": list(matrix.shape) if dim_valid else None
            }
            
            # Check for NaN/Inf
            nan_valid, nan_msg = validate_non_nan_values(matrix, file_path)
            file_result["checks"]["non_nan"] = {
                "valid": nan_valid,
                "message": nan_msg
            }
            
            file_result["valid"] = dim_valid and nan_valid
            
            if not file_result["valid"]:
                all_valid = False
                logger.warning(f"Validation failed for {file_path.name}: {dim_msg} or {nan_msg}")
            else:
                logger.info(f"Validation passed for {file_path.name}: {dim_msg}")
                
        except Exception as e:
            file_result["error"] = str(e)
            file_result["valid"] = False
            all_valid = False
            logger.error(f"Error processing {file_path.name}: {e}")
        
        results.append(file_result)
    
    return {
        "status": "passed" if all_valid else "failed",
        "message": "All connectivity matrices validated successfully" if all_valid else "Some matrices failed validation",
        "files_checked": len(npy_files),
        "valid_count": sum(1 for r in results if r["valid"]),
        "invalid_count": sum(1 for r in results if not r["valid"]),
        "details": results
    }

def generate_validation_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """Save the validation report to a JSON file."""
    ensure_dirs(output_path.parent)
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """Main entry point for connectivity output validation."""
    config = get_config_summary()
    matrices_dir = Path(config.get("processed_dir", "data/processed")) / "connectivity_matrices"
    output_path = Path("data/quality") / "connectivity_validation_report.json"
    
    logger.info(f"Validating connectivity matrices in: {matrices_dir}")
    
    report = validate_connectivity_matrices(matrices_dir)
    generate_validation_report(report, output_path)
    
    # Exit with appropriate code
    if report["status"] == "passed":
        logger.info("Connectivity validation PASSED")
        return 0
    elif report["status"] == "warning":
        logger.warning("Connectivity validation completed with warnings")
        return 0
    else:
        logger.error("Connectivity validation FAILED")
        return 1

if __name__ == "__main__":
    exit(main())
