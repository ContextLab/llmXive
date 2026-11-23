"""
T017: Validation logic for generated adjacency matrices.

Verifies:
1. Non-zero edge counts (matrices are not empty).
2. Correct node labels (dimensions match expected atlas sizes: 90, 200, 400).
3. Data integrity (valid numeric types, no NaN/Inf).

Outputs: data/results/validation_report.json
"""
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Import existing project utilities
from config import get_path, ensure_paths_exist
from utils.logger import get_logger, ValidationFailedError

logger = get_logger(__name__)

# Expected node counts per resolution
EXPECTED_NODES = {
    "aal90": 90,
    "schaefer200": 200,
    "schaefer400": 400
}

def load_matrix(file_path: Path) -> np.ndarray:
    """Load an adjacency matrix from .npz file."""
    try:
        data = np.load(file_path, allow_pickle=True)
        # Handle both 'matrix' key and default 'arr_0' if unnamed
        if 'matrix' in data.files:
            mat = data['matrix']
        elif 'arr_0' in data.files:
            mat = data['arr_0']
        else:
            raise ValueError(f"Unknown data keys in {file_path}: {data.files}")
        
        # Ensure it's a 2D array
        if mat.ndim != 2:
            raise ValueError(f"Matrix in {file_path} is not 2D (shape: {mat.shape})")
        
        return mat
    except Exception as e:
        raise RuntimeError(f"Failed to load matrix from {file_path}: {e}")

def validate_matrix(file_path: Path, subject_id: str, resolution: str) -> Dict[str, Any]:
    """
    Validate a single matrix file.
    
    Checks:
    - File exists and is readable
    - Shape matches expected node count
    - Non-zero edge count
    - No NaN or Inf values
    - Symmetry (if applicable, assuming undirected)
    """
    result = {
        "subject": subject_id,
        "resolution": resolution,
        "file_path": str(file_path),
        "valid": False,
        "errors": []
    }

    if not file_path.exists():
        result["errors"].append("File does not exist")
        return result

    try:
        matrix = load_matrix(file_path)
        result["shape"] = list(matrix.shape)
        result["dtype"] = str(matrix.dtype)
        result["min_val"] = float(np.min(matrix))
        result["max_val"] = float(np.max(matrix))
        result["mean_val"] = float(np.mean(matrix))
        result["nnz"] = int(np.count_nonzero(matrix))
        result["density"] = float(result["nnz"] / (matrix.shape[0] * matrix.shape[1]))

        # Check 1: Correct node labels (dimension)
        expected_n = EXPECTED_NODES.get(resolution)
        if expected_n is None:
            result["errors"].append(f"Unknown resolution: {resolution}")
            return result

        if matrix.shape[0] != expected_n or matrix.shape[1] != expected_n:
            result["errors"].append(
                f"Shape mismatch: expected ({expected_n}, {expected_n}), got {matrix.shape}"
            )
            return result

        # Check 2: Non-zero edge count
        if result["nnz"] == 0:
            result["errors"].append("Matrix has zero edges (empty graph)")
            return result

        # Check 3: No NaN or Inf
        if np.isnan(matrix).any():
            result["errors"].append("Matrix contains NaN values")
            return result
        if np.isinf(matrix).any():
            result["errors"].append("Matrix contains Inf values")
            return result

        # Check 4: Symmetry (optional but good for connectivity)
        # We allow small floating point errors
        if not np.allclose(matrix, matrix.T, rtol=1e-5, atol=1e-8):
            # Not strictly an error for directed graphs, but worth flagging
            # For this pipeline, we assume undirected/symmetric matrices
            logger.warning(f"Matrix {file_path} is not symmetric.")
            # We do not fail validation for this, just log

        result["valid"] = True

    except Exception as e:
        result["errors"].append(str(e))
        logger.error(f"Validation error for {file_path}: {e}")

    return result

def run_validation(subjects: List[str], resolutions: List[str]) -> Dict[str, Any]:
    """
    Run validation on all generated matrices for the given subjects and resolutions.
    """
    data_processed = get_path("data_processed")
    report = {
        "summary": {
            "total_subjects": len(subjects),
            "total_matrices": 0,
            "valid_matrices": 0,
            "invalid_matrices": 0,
            "resolutions_checked": resolutions
        },
        "results": []
    }

    for subject in subjects:
        for resolution in resolutions:
            file_name = f"{subject}_{resolution}.npz"
            file_path = data_processed / file_name
            validation_result = validate_matrix(file_path, subject, resolution)
            
            report["results"].append(validation_result)
            report["summary"]["total_matrices"] += 1
            
            if validation_result["valid"]:
                report["summary"]["valid_matrices"] += 1
            else:
                report["summary"]["invalid_matrices"] += 1

    # Final summary check
    if report["summary"]["invalid_matrices"] > 0:
        raise ValidationFailedError(
            f"Validation failed: {report['summary']['invalid_matrices']} matrices are invalid. "
            f"See report for details."
        )

    return report

def main():
    """
    Entry point for T017.
    Reads subject list from data/raw (or config if available) and validates all processed matrices.
    Outputs data/results/validation_report.json.
    """
    # Ensure output directory exists
    ensure_paths_exist(["data_results"])
    output_path = get_path("data_results") / "validation_report.json"

    # We need to know which subjects were downloaded.
    # Since T012 downloaded them, we can scan the raw data directory or use a manifest.
    # For robustness, we scan the raw data directory for NIfTI files to get subject IDs.
    data_raw = get_path("data_raw")
    
    # Extract subject IDs from filenames like "sub-XXXXX..."
    subjects = set()
    if data_raw.exists():
        for f in data_raw.iterdir():
            if f.suffix.lower() == '.nii.gz' or f.suffix.lower() == '.nii':
                # Assuming filename starts with sub-<id> or similar pattern
                # We'll just use the stem without extension for now, or parse sub-
                stem = f.stem
                if stem.startswith("sub-"):
                    subject_id = stem.split("_")[0].replace("sub-", "")
                    subjects.add(subject_id)
                else:
                    # Fallback: use full stem
                    subjects.add(stem)
    
    # If no subjects found in raw, check if we have any processed files to infer subjects
    if not subjects:
        data_processed = get_path("data_processed")
        if data_processed.exists():
            for f in data_processed.iterdir():
                if f.suffix == '.npz':
                    # Filename format: {subject}_{resolution}.npz
                    stem = f.stem
                    parts = stem.rsplit("_", 1) # Split from right to separate resolution
                    if len(parts) == 2:
                        subjects.add(parts[0])
    
    subjects = sorted(list(subjects))
    resolutions = ["aal90", "schaefer200", "schaefer400"]

    if not subjects:
        logger.warning("No subjects found to validate. Creating empty report.")
        report = {
            "summary": {
                "total_subjects": 0,
                "total_matrices": 0,
                "valid_matrices": 0,
                "invalid_matrices": 0,
                "resolutions_checked": resolutions
            },
            "results": [],
            "error": "No subjects found in data/raw or data/processed"
        }
    else:
        logger.info(f"Validating {len(subjects)} subjects across {len(resolutions)} resolutions.")
        report = run_validation(subjects, resolutions)

    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {output_path}")
    
    # Exit with error if validation failed (handled by run_validation raising, 
    # but if we caught it here, we'd exit 1. Since we raise, main crashes, which is fine for CI)
    if report["summary"]["invalid_matrices"] > 0:
        # This case is actually handled by the raise in run_validation, 
        # but if we reached here, it means we didn't raise (e.g. empty subject list)
        logger.error("Validation failed.")
        exit(1)

if __name__ == "__main__":
    main()
