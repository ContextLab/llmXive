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
    with open(config_path, 'r') as f:
        return json.load(f)

def load_coverage_vectors(file_path: str) -> List[Dict[str, Any]]:
    """Load coverage vectors from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('vectors', [])

def load_validation_results(file_path: str) -> List[Dict[str, Any]]:
    """Load validation results (success rates) from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('results', [])

def calculate_vector_scalar(coverage_vector: Dict[str, Any]) -> int:
    """
    Calculate the scalar count (sum of 1s) from the binary State Coverage Vector.
    
    Args:
        coverage_vector: Dictionary containing a 'vector' key with a list of 0s and 1s.
    
    Returns:
        Integer sum of the vector elements.
    """
    vector = coverage_vector.get('vector', [])
    return sum(vector)

def align_data(
    coverage_vectors: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]]
) -> Tuple[List[int], List[float]]:
    """
    Align coverage vectors with validation results by task_id.
    
    Args:
        coverage_vectors: List of coverage vector records.
        validation_results: List of validation result records.
    
    Returns:
        Tuple of (list of vector scalars, list of success rates).
    """
    # Create lookup maps
    vec_map = {v.get('task_id'): v for v in coverage_vectors}
    val_map = {r.get('task_id'): r for r in validation_results}
    
    # Find common task IDs
    common_ids = sorted(set(vec_map.keys()) & set(val_map.keys()))
    
    scalars = []
    rates = []
    
    for task_id in common_ids:
        vec = vec_map[task_id]
        val = val_map[task_id]
        
        scalar = calculate_vector_scalar(vec)
        success_rate = val.get('success_rate', 0.0)
        
        scalars.append(scalar)
        rates.append(success_rate)
    
    return scalars, rates

def compute_pearson_correlation(x: List[float], y: List[float]) -> Optional[float]:
    """
    Compute Pearson correlation coefficient between two lists.
    
    Args:
        x: First list of values.
        y: Second list of values.
    
    Returns:
        Pearson correlation coefficient, or None if computation fails.
    """
    if len(x) < 2 or len(y) < 2:
        logger.warning("Insufficient data points for correlation calculation.")
        return None
    
    if len(x) != len(y):
        logger.error("Input lists have different lengths.")
        return None
    
    try:
        x_arr = np.array(x)
        y_arr = np.array(y)
        
        # Check for zero variance
        if np.std(x_arr) == 0 or np.std(y_arr) == 0:
            logger.warning("One of the variables has zero variance.")
            return None
        
        correlation = np.corrcoef(x_arr, y_arr)[0, 1]
        return float(correlation)
    except Exception as e:
        logger.error(f"Error computing Pearson correlation: {e}")
        return None

def analyze_sensitivity(
    config: Dict[str, Any],
    coverage_vectors: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis: compute Pearson correlation between
    scalar count of coverage vector and success rate.
    
    Args:
        config: Configuration dictionary.
        coverage_vectors: List of coverage vector records.
        validation_results: List of validation result records.
    
    Returns:
        Dictionary containing analysis results.
    """
    scalars, rates = align_data(coverage_vectors, validation_results)
    
    if not scalars or not rates:
        return {
            'status': 'failed',
            'reason': 'No aligned data points found',
            'correlation': None
        }
    
    correlation = compute_pearson_correlation(scalars, rates)
    
    result = {
        'status': 'success',
        'correlation': correlation,
        'n_samples': len(scalars),
        'threshold_warning': 0.3,
        'threshold_validated': 0.5
    }
    
    # Log validation status
    if correlation is not None:
        if correlation < 0.3:
            result['validation_status'] = 'Invalid Proxy'
            result['message'] = (
                f"Correlation r={correlation:.3f} < 0.3. "
                "Recommend expanding variable set."
            )
            logger.warning(result['message'])
        elif correlation >= 0.5:
            result['validation_status'] = 'Proxy Validated'
            result['message'] = (
                f"Correlation r={correlation:.3f} >= 0.5. "
                "State Coverage Vector variables are a statistically significant proxy for task difficulty."
            )
            log_with_context(
                logger, 
                "PROXY_VALIDATED", 
                result['message'],
                extra={
                    'correlation': correlation,
                    'task_id': 'T041',
                    'us': 'US4'
                }
            )
        else:
            result['validation_status'] = 'Inconclusive'
            result['message'] = (
                f"Correlation r={correlation:.3f} is between 0.3 and 0.5. "
                "Further investigation recommended."
            )
            logger.info(result['message'])
    else:
        result['validation_status'] = 'Error'
        result['message'] = "Correlation could not be computed."
    
    return result

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save analysis results to JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def generate_markdown_report(results: Dict[str, Any], output_path: str) -> None:
    """Generate a markdown report of the sensitivity analysis."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    report_lines = [
        "# Sensitivity Analysis Report",
        "",
        f"**Status:** {results.get('status', 'Unknown')}",
        f"**Validation Status:** {results.get('validation_status', 'N/A')}",
        f"**Sample Size (n):** {results.get('n_samples', 0)}",
        f"**Pearson Correlation (r):** {results.get('correlation', 'N/A')}",
        "",
        "## Message",
        f"{results.get('message', 'No message available.')}",
        ""
    ]
    
    if results.get('correlation') is not None:
        corr = results['correlation']
        if abs(corr) < 0.3:
            report_lines.append("## Interpretation")
            report_lines.append("- **Weak Correlation**: The State Coverage Vector is likely NOT a good proxy for task difficulty.")
            report_lines.append("- **Recommendation**: Expand the set of state variables to capture more relevant dimensions.")
        elif abs(corr) >= 0.5:
            report_lines.append("## Interpretation")
            report_lines.append("- **Strong Correlation**: The State Coverage Vector IS a statistically significant proxy for task difficulty.")
            report_lines.append("- **Conclusion**: Proxy Validated. The curriculum scheduler can reliably use these state variables.")
        else:
            report_lines.append("## Interpretation")
            report_lines.append("- **Moderate Correlation**: The relationship is present but not strong enough for definitive validation.")
            report_lines.append("- **Recommendation**: Collect more data or refine the state variables.")
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    logger.info(f"Markdown report saved to {output_path}")

def main() -> None:
    """Main entry point for sensitivity analysis."""
    config_path = os.environ.get('CONFIG_PATH', 'data/config/sensitivity_config.json')
    coverage_path = os.environ.get('COVERAGE_PATH', 'data/processed/coverage_vectors.json')
    validation_path = os.environ.get('VALIDATION_PATH', 'data/processed/validation_results.json')
    output_json = os.environ.get('OUTPUT_JSON', 'data/processed/sensitivity_results.json')
    output_md = os.environ.get('OUTPUT_MD', 'data/processed/sensitivity_report.md')
    
    logger.info("Starting sensitivity analysis...")
    
    try:
        config = load_config(config_path)
        coverage_vectors = load_coverage_vectors(coverage_path)
        validation_results = load_validation_results(validation_path)
        
        results = analyze_sensitivity(config, coverage_vectors, validation_results)
        
        save_results(results, output_json)
        generate_markdown_report(results, output_md)
        
        logger.info("Sensitivity analysis completed successfully.")
        
        # Exit with error code if proxy validation failed (r < 0.3)
        if results.get('validation_status') == 'Invalid Proxy':
            logger.error("Proxy validation failed. Exiting with error code 1.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
