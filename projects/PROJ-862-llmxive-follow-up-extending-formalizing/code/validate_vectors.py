"""
Validation module for baseline latent vectors.

This module provides functions to validate that extracted vectors:
1. Match the model's hidden dimension size
2. Are properly L2-normalized (unit length)

These validations are critical for ensuring the integrity of the 
baseline extraction process before downstream analysis.
"""
import logging
import torch
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import csv
from config import ModelConfig, OutputPaths
from memory_monitor import check_memory_limit, get_current_memory_mb

logger = logging.getLogger(__name__)

class VectorValidationError(Exception):
    """Raised when vector validation fails."""
    pass

def validate_vector_dimension(
    vector: torch.Tensor, 
    expected_dim: int, 
    pair_id: str, 
    index: int
) -> Tuple[bool, str]:
    """
    Validate that a single vector matches the expected hidden dimension.
    
    Args:
        vector: The extracted hidden state vector
        expected_dim: Expected dimension (model hidden size)
        pair_id: The PairID for context
        index: Index within the batch/sequence
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    actual_dim = vector.shape[-1]
    if actual_dim != expected_dim:
        error_msg = (
            f"Dimension mismatch for PairID {pair_id}, index {index}: "
            f"expected {expected_dim}, got {actual_dim}"
        )
        logger.error(error_msg)
        return False, error_msg
    
    logger.debug(f"Dimension check passed for PairID {pair_id}, index {index}")
    return True, ""

def validate_l2_normalization(
    vector: torch.Tensor, 
    tolerance: float = 1e-5,
    pair_id: str = "unknown",
    index: int = 0
) -> Tuple[bool, str]:
    """
    Validate that a vector is L2-normalized (unit length).
    
    Args:
        vector: The vector to validate
        tolerance: Acceptable deviation from unit length
        pair_id: The PairID for context
        index: Index within the batch/sequence
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if vector.dim() == 0:
        error_msg = f"Scalar value detected for PairID {pair_id}, index {index}"
        logger.error(error_msg)
        return False, error_msg
        
    l2_norm = torch.linalg.norm(vector).item()
    if abs(l2_norm - 1.0) > tolerance:
        error_msg = (
            f"L2 normalization failed for PairID {pair_id}, index {index}: "
            f"norm = {l2_norm:.6f} (expected ~1.0)"
        )
        logger.error(error_msg)
        return False, error_msg
    
    logger.debug(f"L2 normalization check passed for PairID {pair_id}, index {index}")
    return True, ""

def validate_vector_batch(
    vectors: List[torch.Tensor],
    pair_ids: List[str],
    expected_dim: int,
    tolerance: float = 1e-5
) -> Dict[str, Any]:
    """
    Validate a batch of vectors for dimension and normalization.
    
    Args:
        vectors: List of extracted vectors
        pair_ids: List of corresponding PairIDs
        expected_dim: Expected hidden dimension
        tolerance: Tolerance for L2 norm check
        
    Returns:
        Dictionary with validation results:
        - total_count: Total vectors checked
        - passed_count: Number of valid vectors
        - failed_count: Number of invalid vectors
        - dimension_errors: List of dimension mismatch errors
        - normalization_errors: List of normalization errors
    """
    if len(vectors) != len(pair_ids):
        raise ValueError(
            f"Length mismatch: {len(vectors)} vectors vs {len(pair_ids)} pair_ids"
        )
    
    results = {
        "total_count": len(vectors),
        "passed_count": 0,
        "failed_count": 0,
        "dimension_errors": [],
        "normalization_errors": []
    }
    
    for i, (vec, pair_id) in enumerate(zip(vectors, pair_ids)):
        # Check memory periodically
        if i % 1000 == 0:
            check_memory_limit()
        
        # Validate dimension
        dim_valid, dim_err = validate_vector_dimension(vec, expected_dim, pair_id, i)
        if not dim_valid:
            results["dimension_errors"].append(dim_err)
            results["failed_count"] += 1
            continue
        
        # Validate L2 normalization
        norm_valid, norm_err = validate_l2_normalization(vec, tolerance, pair_id, i)
        if not norm_valid:
            results["normalization_errors"].append(norm_err)
            results["failed_count"] += 1
            continue
        
        results["passed_count"] += 1
    
    return results

def validate_csv_vectors(
    csv_path: str,
    model_config: ModelConfig,
    output_paths: OutputPaths,
    vector_column: str = "vector",
    pair_id_column: str = "pair_id"
) -> Dict[str, Any]:
    """
    Validate vectors stored in a CSV file against model configuration.
    
    Args:
        csv_path: Path to the CSV file containing vectors
        model_config: Model configuration with hidden_size
        output_paths: Output paths configuration
        vector_column: Name of the column containing vector data
        pair_id_column: Name of the column containing PairIDs
        
    Returns:
        Dictionary with validation results
    """
    logger.info(f"Validating vectors in {csv_path}")
    
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"Vector file not found: {csv_path}")
    
    expected_dim = model_config.hidden_size
    total_count = 0
    passed_count = 0
    failed_count = 0
    errors = []
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row_idx, row in enumerate(reader):
            # Check memory periodically
            if row_idx % 1000 == 0:
                check_memory_limit()
            
            total_count += 1
            pair_id = row.get(pair_id_column, f"row_{row_idx}")
            
            try:
                # Parse vector from CSV string representation
                vector_str = row.get(vector_column, "")
                if not vector_str:
                    raise VectorValidationError(
                        f"Empty vector for PairID {pair_id} at row {row_idx}"
                    )
                
                # Parse the vector (assumes comma-separated values in brackets)
                vector_str = vector_str.strip('[]')
                values = [float(x.strip()) for x in vector_str.split(',')]
                vector = torch.tensor(values, dtype=torch.float32)
                
                # Validate dimension
                if vector.shape[-1] != expected_dim:
                    error = (
                        f"Dimension mismatch for {pair_id}: "
                        f"expected {expected_dim}, got {vector.shape[-1]}"
                    )
                    errors.append(error)
                    failed_count += 1
                    continue
                
                # Validate L2 normalization
                l2_norm = torch.linalg.norm(vector).item()
                if abs(l2_norm - 1.0) > 1e-5:
                    error = (
                        f"L2 normalization failed for {pair_id}: "
                        f"norm = {l2_norm:.6f}"
                    )
                    errors.append(error)
                    failed_count += 1
                    continue
                
                passed_count += 1
                
            except (ValueError, IndexError) as e:
                error = f"Parse error for {pair_id} at row {row_idx}: {str(e)}"
                errors.append(error)
                failed_count += 1
                continue
    
    results = {
        "file_path": csv_path,
        "total_count": total_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate": passed_count / total_count if total_count > 0 else 0.0,
        "errors": errors
    }
    
    logger.info(
        f"Validation complete: {passed_count}/{total_count} passed "
        f"({results['pass_rate']:.2%})"
    )
    
    return results

def write_validation_report(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Write validation results to a report file.
    
    Args:
        results: Validation results dictionary
        output_path: Path to write the report
    """
    import json
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Validation report written to {output_path}")

def run_baseline_validation(
    csv_path: str,
    model_config: ModelConfig,
    output_paths: OutputPaths
) -> bool:
    """
    Run full validation on baseline vectors and report results.
    
    Args:
        csv_path: Path to baseline vectors CSV
        model_config: Model configuration
        output_paths: Output paths configuration
        
    Returns:
        True if all validations pass, False otherwise
    """
    results = validate_csv_vectors(
        csv_path=csv_path,
        model_config=model_config,
        output_paths=output_paths
    )
    
    report_path = str(Path(output_paths.processed_dir) / "validation_report.json")
    write_validation_report(results, report_path)
    
    if results["failed_count"] > 0:
        logger.error(
            f"Validation failed: {results['failed_count']} vectors failed "
            f"out of {results['total_count']}"
        )
        return False
    
    logger.info("All baseline vectors passed validation")
    return True

if __name__ == "__main__":
    # Example usage for standalone testing
    logging.basicConfig(level=logging.INFO)
    
    # This would be called from main.py with actual config
    logger.info("Validation module loaded successfully")
