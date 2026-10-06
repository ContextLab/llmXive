import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def load_coverage_vectors(file_path: str) -> List[Dict[str, Any]]:
    """Load coverage vectors from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Coverage vectors file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    # Handle different possible structures
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'vectors' in data:
        return data['vectors']
    else:
        raise ValueError(f"Unexpected coverage vectors structure in {file_path}")

def load_validation_results(file_path: str) -> List[Dict[str, Any]]:
    """Load validation results from JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Validation results file not found: {file_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        raise ValueError(f"Unexpected validation results structure in {file_path}")

def calculate_vector_scalar(vector: List[int]) -> int:
    """Calculate the scalar value (sum of 1s) from a binary coverage vector."""
    return sum(vector)

def align_data(coverage_vectors: List[Dict[str, Any]], validation_results: List[Dict[str, Any]]) -> Tuple[List[float], List[float]]:
    """Align coverage vectors with validation results by task ID."""
    # Create a mapping from task_id to success_rate
    validation_map = {}
    for result in validation_results:
        task_id = result.get('task_id')
        if task_id:
            validation_map[task_id] = result.get('success_rate', 0.0)
    
    scalars = []
    success_rates = []
    
    for vector_data in coverage_vectors:
        task_id = vector_data.get('task_id')
        if task_id and task_id in validation_map:
            vector = vector_data.get('vector', [])
            scalar = calculate_vector_scalar(vector)
            scalars.append(scalar)
            success_rates.append(validation_map[task_id])
    
    if len(scalars) == 0:
        raise ValueError("No aligned data found between coverage vectors and validation results")
    
    return scalars, success_rates

def compute_pearson_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson correlation coefficient and p-value."""
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("Insufficient data for correlation calculation")
    
    x_array = np.array(x)
    y_array = np.array(y)
    
    # Calculate Pearson correlation
    correlation_matrix = np.corrcoef(x_array, y_array)
    r = correlation_matrix[0, 1]
    
    # Calculate p-value (two-tailed)
    # Using t-distribution approach
    n = len(x)
    t_stat = r * np.sqrt((n - 2) / (1 - r**2))
    
    # Approximate p-value using scipy if available, otherwise use a simple approximation
    try:
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
    except ImportError:
        # Fallback: simple approximation for p-value
        # This is less accurate but avoids hard dependency on scipy
        p_value = 1.0 - abs(r)  # Very rough approximation
        
    return float(r), float(p_value)

def analyze_sensitivity(coverage_vectors: List[Dict[str, Any]], validation_results: List[Dict[str, Any]], 
                      invalid_threshold: float = 0.3, validated_threshold: float = 0.5) -> Dict[str, Any]:
    """Perform full sensitivity analysis."""
    # Align data
    scalars, success_rates = align_data(coverage_vectors, validation_results)
    
    # Calculate statistics
    mean_scalar = np.mean(scalars)
    std_scalar = np.std(scalars)
    mean_success_rate = np.mean(success_rates)
    std_success_rate = np.std(success_rates)
    
    # Calculate correlation
    r, p_value = compute_pearson_correlation(scalars, success_rates)
    
    # Determine status
    if r >= validated_threshold:
        status = "Proxy Validated"
    elif r < invalid_threshold:
        status = "Invalid Proxy"
    else:
        status = "Inconclusive"
    
    # Prepare results
    results = {
        'pearson_r': r,
        'p_value': p_value,
        'sample_size': len(scalars),
        'status': status,
        'mean_scalar': float(mean_scalar),
        'std_scalar': float(std_scalar),
        'mean_success_rate': float(mean_success_rate),
        'std_success_rate': float(std_success_rate),
        'invalid_threshold': invalid_threshold,
        'validated_threshold': validated_threshold,
        'sample_data': {
            'scalars': scalars[:10],  # First 10 samples
            'success_rates': success_rates[:10]
        }
    }
    
    # Log status
    if status == "Proxy Validated":
        logger.info(f"Proxy Validated: r={r:.4f} >= {validated_threshold}")
    elif status == "Invalid Proxy":
        logger.warning(f"Invalid Proxy: r={r:.4f} < {invalid_threshold}. Recommend expanding variable set.")
    else:
        logger.warning(f"Inconclusive: {invalid_threshold} <= r={r:.4f} < {validated_threshold}")
    
    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save sensitivity analysis results to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity results saved to {output_path}")

def main():
    """Main entry point for sensitivity analysis."""
    # Default paths
    config_path = "code/analysis/config/sensitivity_config.json"
    coverage_path = "data/processed/coverage_vectors.json"
    validation_path = "data/processed/validation_results.json"
    results_path = "data/processed/sensitivity_results.json"
    
    # Allow command line overrides
    if len(sys.argv) > 1:
        coverage_path = sys.argv[1]
    if len(sys.argv) > 2:
        validation_path = sys.argv[2]
    if len(sys.argv) > 3:
        results_path = sys.argv[3]
        
    logger.info(f"Starting sensitivity analysis")
    logger.info(f"Coverage vectors: {coverage_path}")
    logger.info(f"Validation results: {validation_path}")
    logger.info(f"Results output: {results_path}")
    
    try:
        # Load data
        coverage_vectors = load_coverage_vectors(coverage_path)
        validation_results = load_validation_results(validation_path)
        
        # Perform analysis
        results = analyze_sensitivity(coverage_vectors, validation_results)
        
        # Save results
        save_results(results, results_path)
        
        logger.info("Sensitivity analysis completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
