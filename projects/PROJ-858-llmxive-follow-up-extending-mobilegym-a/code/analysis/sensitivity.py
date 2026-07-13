import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_coverage_vectors(vectors_path: str) -> List[Dict[str, Any]]:
    """
    Load the binary State Coverage Vectors from the processed data.
    Expected format: List of records with 'vector' (list of 0/1) and 'task_id'.
    """
    path = Path(vectors_path)
    if not path.exists():
        raise FileNotFoundError(f"Coverage vectors file not found: {vectors_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'vectors' in data:
        return data['vectors']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in coverage vectors file: {vectors_path}")

def load_validation_results(results_path: str) -> List[Dict[str, Any]]:
    """
    Load the validation set results containing success rates per task.
    Expected format: List of records with 'task_id' and 'success_rate' (float 0-1).
    """
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Validation results file not found: {results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected format in validation results file: {results_path}")

def calculate_vector_scalar(coverage_vector: List[int]) -> float:
    """
    Calculate the scalar count (sum of 1s) from a binary State Coverage Vector.
    
    Args:
        coverage_vector: List of 0s and 1s representing state coverage.
        
    Returns:
        Scalar count of covered states.
    """
    if not all(x in (0, 1) for x in coverage_vector):
        raise ValueError(f"Invalid binary vector: {coverage_vector}")
    return float(sum(coverage_vector))

def align_data(coverage_vectors: List[Dict], validation_results: List[Dict]) -> Tuple[List[float], List[float]]:
    """
    Align coverage vectors with validation results by task_id.
    
    Returns:
        Tuple of (scalar_counts, success_rates) aligned lists.
    """
    # Create lookup for validation results
    val_lookup = {r['task_id']: r['success_rate'] for r in validation_results if 'task_id' in r and 'success_rate' in r}
    
    scalar_counts = []
    success_rates = []
    
    for vec_record in coverage_vectors:
        task_id = vec_record.get('task_id')
        if not task_id:
            logger.warning(f"Skipping vector record without task_id: {vec_record}")
            continue
        
        if task_id not in val_lookup:
            logger.warning(f"Task {task_id} has coverage vector but no validation result")
            continue
        
        vector = vec_record.get('vector')
        if not vector:
            logger.warning(f"Skipping vector record without vector data: {vec_record}")
            continue
        
        try:
            scalar = calculate_vector_scalar(vector)
            success_rate = val_lookup[task_id]
            
            scalar_counts.append(scalar)
            success_rates.append(success_rate)
        except ValueError as e:
            logger.error(f"Error processing vector for task {task_id}: {e}")
            continue
    
    if len(scalar_counts) != len(success_rates):
        raise ValueError(f"Mismatch in aligned data lengths: {len(scalar_counts)} vs {len(success_rates)}")
    
    if len(scalar_counts) == 0:
        raise ValueError("No matching data points found between coverage vectors and validation results")
    
    return scalar_counts, success_rates

def compute_pearson_correlation(x: List[float], y: List[float]) -> float:
    """
    Compute Pearson correlation coefficient (r) between two lists.
    
    Args:
        x: First list of values (scalar counts).
        y: Second list of values (success rates).
        
    Returns:
        Pearson correlation coefficient r.
    """
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Need at least 2 matching data points for correlation")
    
    x_arr = np.array(x)
    y_arr = np.array(y)
    
    # Calculate correlation using numpy
    correlation_matrix = np.corrcoef(x_arr, y_arr)
    r = float(correlation_matrix[0, 1])
    
    return r

def analyze_sensitivity(
    coverage_vectors_path: str,
    validation_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Main analysis function to compute Pearson correlation between 
    scalar state coverage count and success rate.
    
    Args:
        coverage_vectors_path: Path to coverage vectors JSON file.
        validation_results_path: Path to validation results JSON file.
        output_path: Path to save the sensitivity report.
        
    Returns:
        Dictionary containing analysis results.
    """
    logger.info("Starting sensitivity analysis")
    
    # Load data
    logger.info(f"Loading coverage vectors from {coverage_vectors_path}")
    coverage_vectors = load_coverage_vectors(coverage_vectors_path)
    
    logger.info(f"Loading validation results from {validation_results_path}")
    validation_results = load_validation_results(validation_results_path)
    
    # Align data
    logger.info("Aligning data by task_id")
    scalar_counts, success_rates = align_data(coverage_vectors, validation_results)
    logger.info(f"Aligned {len(scalar_counts)} data points")
    
    # Compute correlation
    logger.info("Computing Pearson correlation coefficient")
    r = compute_pearson_correlation(scalar_counts, success_rates)
    logger.info(f"Pearson correlation coefficient (r): {r:.4f}")
    
    # Determine validity
    if r >= 0.5:
        status = "VALIDATED"
        message = "Proxy Validated: State coverage count is a strong predictor of success rate."
    elif r >= 0.3:
        status = "WEAK"
        message = "Proxy is weakly correlated. Consider expanding variable set."
    else:
        status = "INVALID"
        message = "Invalid Proxy: State coverage count does not predict success rate (r < 0.3)."
    
    results = {
        "pearson_r": r,
        "sample_size": len(scalar_counts),
        "status": status,
        "message": message,
        "thresholds": {
            "validated": 0.5,
            "weak": 0.3
        },
        "summary": {
            "mean_scalar_count": float(np.mean(scalar_counts)),
            "std_scalar_count": float(np.std(scalar_counts)),
            "mean_success_rate": float(np.mean(success_rates)),
            "std_success_rate": float(np.std(success_rates))
        }
    }
    
    # Save report
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return results

def main():
    """Main entry point for sensitivity analysis."""
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "code" / "analysis" / "config.json"
    vectors_path = project_root / "data" / "processed" / "coverage_vectors.json"
    validation_path = project_root / "data" / "processed" / "validation_results.json"
    output_path = project_root / "data" / "processed" / "sensitivity_report.json"
    
    # Check if config exists, otherwise use defaults
    if config_path.exists():
        config = load_config(str(config_path))
        vectors_path = config.get('coverage_vectors_path', str(vectors_path))
        validation_path = config.get('validation_results_path', str(validation_path))
        output_path = config.get('output_path', str(output_path))
    
    try:
        results = analyze_sensitivity(vectors_path, validation_path, output_path)
        print(f"Analysis complete. Pearson r = {results['pearson_r']:.4f} ({results['status']})")
        return 0
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        print(f"Error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        print(f"Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
