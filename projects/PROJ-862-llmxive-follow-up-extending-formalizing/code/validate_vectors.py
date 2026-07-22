import logging
import torch
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import csv

logger = logging.getLogger(__name__)

class VectorValidationError(Exception):
    """Raised when vector validation fails."""
    pass

def validate_vector_dimension(vector: torch.Tensor, expected_dim: int) -> bool:
    """Validates that a vector has the expected dimension."""
    if vector.dim() != 1:
        return False
    return vector.size(0) == expected_dim

def validate_l2_normalization(vector: torch.Tensor, tol: float = 1e-5) -> bool:
    """Validates that a vector is L2 normalized (norm approx 1.0)."""
    norm = vector.norm().item()
    return abs(norm - 1.0) < tol

def validate_vector_batch(vectors: List[torch.Tensor], expected_dim: int) -> Tuple[int, int]:
    """
    Validates a batch of vectors.
    Returns (passed_count, failed_count)
    """
    passed = 0
    failed = 0
    for v in vectors:
        if validate_vector_dimension(v, expected_dim) and validate_l2_normalization(v):
            passed += 1
        else:
            failed += 1
            logger.warning(f"Invalid vector found: dim={v.size(0)}, norm={v.norm().item()}")
    return passed, failed

def validate_csv_vectors(csv_path: str, expected_dim: int) -> Dict[str, Any]:
    """
    Validates vectors in a CSV file.
    """
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results["total"] += 1
            try:
                vec = torch.tensor(json.loads(row['Vector']))
                if not validate_vector_dimension(vec, expected_dim):
                    results["failed"] += 1
                    results["errors"].append(f"Dim error for {row['PairID']}")
                elif not validate_l2_normalization(vec):
                    results["failed"] += 1
                    results["errors"].append(f"Norm error for {row['PairID']}")
                else:
                    results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Parse error for {row['PairID']}: {e}")
    
    return results

def write_validation_report(report: Dict[str, Any], output_path: str):
    """Writes a validation report to a file."""
    import json
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

def run_baseline_validation(csv_path: str, expected_dim: int):
    """Runs validation on the baseline vectors file."""
    logger.info(f"Validating baseline vectors at {csv_path}")
    report = validate_csv_vectors(csv_path, expected_dim)
    logger.info(f"Validation complete: {report['passed']}/{report['total']} passed.")
    if report['failed'] > 0:
        logger.warning(f"{report['failed']} vectors failed validation.")
    return report
