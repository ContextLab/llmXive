"""
Validation module for latent vectors.
Ensures output vectors match model hidden dimension and are L2-normalized.
"""
import logging
import torch
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import csv

logger = logging.getLogger(__name__)


class VectorValidationError(Exception):
    """Exception raised when vector validation fails."""
    pass


def validate_vector_dimension(vector: torch.Tensor, expected_dim: int) -> Tuple[bool, str]:
    """
    Validate that a vector matches the expected hidden dimension.

    Args:
        vector: The vector to validate (1D tensor).
        expected_dim: The expected dimension size.

    Returns:
        Tuple of (is_valid, message)
    """
    if vector.dim() != 1:
        return False, f"Vector has dimension {vector.dim()}, expected 1D"

    actual_dim = vector.size(0)
    if actual_dim != expected_dim:
        return False, f"Vector dimension mismatch: expected {expected_dim}, got {actual_dim}"

    return True, f"Dimension check passed: {actual_dim}"


def validate_l2_normalization(vector: torch.Tensor, tolerance: float = 1e-6) -> Tuple[bool, str]:
    """
    Validate that a vector is L2-normalized (unit length).

    Args:
        vector: The vector to validate (1D tensor).
        tolerance: Allowed deviation from 1.0 for L2 norm.

    Returns:
        Tuple of (is_valid, message)
    """
    if vector.dim() != 1:
        return False, f"Vector has dimension {vector.dim()}, expected 1D"

    l2_norm = torch.norm(vector, p=2).item()

    if abs(l2_norm - 1.0) > tolerance:
        return False, f"Vector is not L2-normalized: L2 norm = {l2_norm:.6f} (expected ~1.0)"

    return True, f"L2 normalization check passed: norm = {l2_norm:.6f}"


def validate_vector_batch(
    vectors: List[torch.Tensor],
    expected_dim: int,
    tolerance: float = 1e-6
) -> Tuple[bool, List[str]]:
    """
    Validate a batch of vectors for dimension and L2 normalization.

    Args:
        vectors: List of 1D tensors to validate.
        expected_dim: Expected hidden dimension.
        tolerance: Allowed deviation for L2 norm.

    Returns:
        Tuple of (all_valid, list_of_error_messages)
    """
    errors = []
    for i, vec in enumerate(vectors):
        dim_valid, dim_msg = validate_vector_dimension(vec, expected_dim)
        if not dim_valid:
            errors.append(f"Vector {i}: {dim_msg}")
            continue

        norm_valid, norm_msg = validate_l2_normalization(vec, tolerance)
        if not norm_valid:
            errors.append(f"Vector {i}: {norm_msg}")

    return len(errors) == 0, errors


def validate_csv_vectors(
    csv_path: str,
    expected_dim: int,
    vector_column: str = "vector",
    tolerance: float = 1e-6,
    sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate vectors stored in a CSV file.

    Args:
        csv_path: Path to the CSV file.
        expected_dim: Expected hidden dimension.
        vector_column: Name of the column containing vector strings.
        tolerance: Allowed deviation for L2 norm.
        sample_size: Number of rows to sample for validation (None = all).

    Returns:
        Dictionary with validation results.
    """
    path = Path(csv_path)
    if not path.exists():
        return {
            "success": False,
            "error": f"File not found: {csv_path}",
            "checked_count": 0
        }

    results = {
        "success": True,
        "checked_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "errors": [],
        "dimension_errors": 0,
        "normalization_errors": 0
    }

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check if vector column exists
            if vector_column not in reader.fieldnames:
                return {
                    "success": False,
                    "error": f"Column '{vector_column}' not found in CSV. Available columns: {reader.fieldnames}",
                    "checked_count": 0
                }

            count = 0
            for row in reader:
                if sample_size is not None and count >= sample_size:
                    break

                try:
                    # Parse vector string to tensor
                    vec_str = row[vector_column].strip('[]')
                    values = [float(x.strip()) for x in vec_str.split(',')]
                    vec = torch.tensor(values, dtype=torch.float32)

                    # Validate dimension
                    dim_valid, _ = validate_vector_dimension(vec, expected_dim)
                    if not dim_valid:
                        results["dimension_errors"] += 1
                        results["failed_count"] += 1
                        results["errors"].append(f"Row {count}: Dimension mismatch")
                        results["success"] = False
                        continue

                    # Validate L2 normalization
                    norm_valid, _ = validate_l2_normalization(vec, tolerance)
                    if not norm_valid:
                        results["normalization_errors"] += 1
                        results["failed_count"] += 1
                        results["errors"].append(f"Row {count}: Not L2-normalized")
                        results["success"] = False
                        continue

                    results["passed_count"] += 1

                except Exception as e:
                    results["failed_count"] += 1
                    results["errors"].append(f"Row {count}: Parse error - {str(e)}")
                    results["success"] = False

                count += 1

            results["checked_count"] = count

            if results["checked_count"] == 0:
                results["error"] = "No rows found in CSV"
                results["success"] = False

    except Exception as e:
        results["success"] = False
        results["error"] = f"Failed to read CSV: {str(e)}"

    return results


def write_validation_report(results: Dict[str, Any], output_path: str) -> None:
    """
    Write validation results to a JSON file.

    Args:
        results: Validation results dictionary.
        output_path: Path to write the report.
    """
    import json
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Validation report written to {output_path}")


def run_baseline_validation(
    baseline_csv_path: str,
    expected_dim: int,
    model_name: str = "unknown"
) -> Dict[str, Any]:
    """
    Run full validation on baseline vectors CSV.

    Args:
        baseline_csv_path: Path to baseline_vectors.csv.
        expected_dim: Expected hidden dimension of the model.
        model_name: Name of the model used (for logging).

    Returns:
        Validation results dictionary.
    """
    logger.info(f"Validating baseline vectors for model '{model_name}' (dim={expected_dim})")

    if not Path(baseline_csv_path).exists():
        raise VectorValidationError(
            f"Baseline vectors file not found: {baseline_csv_path}. "
            "Run extraction first (T015)."
        )

    results = validate_csv_vectors(
        csv_path=baseline_csv_path,
        expected_dim=expected_dim,
        vector_column="vector",
        tolerance=1e-6
    )

    if results["success"]:
        logger.info(
            f"✓ Validation PASSED: {results['passed_count']}/{results['checked_count']} vectors valid. "
            f"All vectors match dimension {expected_dim} and are L2-normalized."
        )
    else:
        error_summary = []
        if results.get("dimension_errors", 0) > 0:
            error_summary.append(f"{results['dimension_errors']} dimension mismatches")
        if results.get("normalization_errors", 0) > 0:
            error_summary.append(f"{results['normalization_errors']} normalization failures")
        if results.get("error"):
            error_summary.append(results["error"])

        logger.error(
            f"✗ Validation FAILED: {results['failed_count']}/{results['checked_count']} vectors invalid. "
            f"Issues: {'; '.join(error_summary)}"
        )

        # Raise error to halt pipeline if validation fails
        raise VectorValidationError(
            f"Baseline vector validation failed: {', '.join(error_summary)}"
        )

    return results