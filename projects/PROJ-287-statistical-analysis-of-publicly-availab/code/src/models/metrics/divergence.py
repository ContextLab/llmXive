"""
Divergence metrics for topic drift analysis.

Implements Jensen-Shannon divergence calculation for comparing
topic distributions across time windows.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
from scipy.spatial.distance import jensenshannon

from src.utils.logging import get_logger


def calculate_js_divergence(
    dist1: Union[np.ndarray, List[float]],
    dist2: Union[np.ndarray, List[float]],
    base: int = 2
) -> float:
    """
    Calculate Jensen-Shannon divergence between two probability distributions.
    
    Args:
        dist1: First probability distribution (must sum to 1.0)
        dist2: Second probability distribution (must sum to 1.0)
        base: Logarithm base for divergence calculation (default: 2 for bits)
    
    Returns:
        JS divergence value (non-negative, bounded by 1.0 for base 2)
    
    Raises:
        ValueError: If distributions are not valid probability vectors
        TypeError: If inputs cannot be converted to numpy arrays
    """
    # Convert to numpy arrays
    p = np.asarray(dist1, dtype=np.float64)
    q = np.asarray(dist2, dtype=np.float64)
    
    # Validate inputs
    if p.ndim != 1 or q.ndim != 1:
        raise ValueError("Distributions must be 1-dimensional vectors")
    
    if len(p) != len(q):
        raise ValueError(f"Distributions must have same length: {len(p)} vs {len(q)}")
    
    # Ensure non-negative values
    if np.any(p < 0) or np.any(q < 0):
        raise ValueError("Distributions must contain only non-negative values")
    
    # Normalize to ensure they sum to 1.0
    p_sum = p.sum()
    q_sum = q.sum()
    
    if p_sum == 0 or q_sum == 0:
        raise ValueError("Distributions cannot be all zeros")
    
    p = p / p_sum
    q = q / q_sum
    
    # Handle numerical edge cases (very small values)
    # scipy.spatial.distance.jensenshannon handles this internally,
    # but we ensure inputs are clean
    p = np.clip(p, 1e-15, 1.0)
    q = np.clip(q, 1e-15, 1.0)
    
    # Recalculate after clipping to maintain sum=1
    p = p / p.sum()
    q = q / q.sum()
    
    # Calculate JS divergence
    js_div = jensenshannon(p, q, base=base)
    
    # Square the result since jensenshannon returns sqrt(JS) in older scipy versions
    # In scipy >= 1.8, it returns the actual JS divergence
    # We check the scipy version to be safe
    import scipy
    from packaging import version
    
    if version.parse(scipy.__version__) < version.parse("1.8.0"):
        # Older versions return sqrt(JS), so we square it
        js_div = js_div ** 2
    
    return float(js_div)


def calculate_js_divergence_matrix(
    distributions: Dict[str, np.ndarray],
    base: int = 2
) -> Tuple[Dict[str, Dict[str, float]], np.ndarray, List[str]]:
    """
    Calculate pairwise Jensen-Shannon divergence matrix for multiple windows.
    
    Args:
        distributions: Dictionary mapping window names to topic distributions
        base: Logarithm base for divergence calculation
    
    Returns:
        Tuple of:
            - Nested dict of pairwise divergences
            - Symmetric divergence matrix
            - List of window names in matrix order
    """
    window_names = sorted(distributions.keys())
    n = len(window_names)
    
    # Initialize matrix
    divergence_matrix = np.zeros((n, n))
    
    # Calculate pairwise divergences
    for i, window1 in enumerate(window_names):
        for j, window2 in enumerate(window_names):
            if i == j:
                divergence_matrix[i, j] = 0.0
            else:
                js_div = calculate_js_divergence(
                    distributions[window1],
                    distributions[window2],
                    base=base
                )
                divergence_matrix[i, j] = js_div
                divergence_matrix[j, i] = js_div  # Symmetric
    
    # Create nested dict for JSON serialization
    divergence_dict = {}
    for i, window1 in enumerate(window_names):
        divergence_dict[window1] = {}
        for j, window2 in enumerate(window_names):
            divergence_dict[window1][window2] = float(divergence_matrix[i, j])
    
    return divergence_dict, divergence_matrix, window_names


def validate_topic_distribution(
    distribution: np.ndarray,
    window_name: str,
    tolerance: float = 1e-6
) -> bool:
    """
    Validate that a topic distribution is a valid probability vector.
    
    Args:
        distribution: Topic distribution vector
        window_name: Name of the window for error messages
        tolerance: Tolerance for sum check (default: 1e-6)
    
    Returns:
        True if valid, raises ValueError if invalid
    """
    if not isinstance(distribution, np.ndarray):
        raise ValueError(f"Window {window_name}: distribution must be numpy array")
    
    if distribution.ndim != 1:
        raise ValueError(f"Window {window_name}: distribution must be 1D vector")
    
    if np.any(distribution < 0):
        raise ValueError(f"Window {window_name}: distribution contains negative values")
    
    dist_sum = distribution.sum()
    if abs(dist_sum - 1.0) > tolerance:
        raise ValueError(
            f"Window {window_name}: distribution sum is {dist_sum}, expected 1.0"
        )
    
    return True


def load_topic_vectors_from_file(
    filepath: Union[str, Path]
) -> Dict[str, np.ndarray]:
    """
    Load topic vectors from a JSON file.
    
    Args:
        filepath: Path to the JSON file containing topic vectors
    
    Returns:
        Dictionary mapping window names to topic distribution arrays
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Topic vectors file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    distributions = {}
    for window_name, vector_data in data.items():
        if isinstance(vector_data, list):
            distributions[window_name] = np.array(vector_data, dtype=np.float64)
        elif isinstance(vector_data, dict) and 'values' in vector_data:
            distributions[window_name] = np.array(
                vector_data['values'], dtype=np.float64
            )
        else:
            raise ValueError(
                f"Unexpected format for window {window_name} in {filepath}"
            )
    
    return distributions


def save_divergence_results(
    results: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save divergence results to a JSON file.
    
    Args:
        results: Dictionary containing divergence calculations and metadata
        output_path: Path to save the results JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger = get_logger(__name__)
    logger.info(f"Saved divergence results to {output_path}")


def compute_pairwise_divergences(
    topic_vectors_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    base: int = 2
) -> Dict[str, Any]:
    """
    Compute pairwise JS divergences for all topic vectors.
    
    Args:
        topic_vectors_path: Path to JSON file containing topic vectors
        output_path: Optional path to save results (if None, returns dict only)
        base: Logarithm base for JS divergence
    
    Returns:
        Dictionary containing divergence matrix and metadata
    """
    logger = get_logger(__name__)
    logger.info(f"Loading topic vectors from {topic_vectors_path}")
    
    distributions = load_topic_vectors_from_file(topic_vectors_path)
    
    # Validate all distributions
    for window_name, dist in distributions.items():
        validate_topic_distribution(dist, window_name)
    
    logger.info(f"Calculated distributions for {len(distributions)} windows")
    
    # Calculate pairwise divergences
    divergence_dict, divergence_matrix, window_names = calculate_js_divergence_matrix(
        distributions, base=base
    )
    
    results = {
        'method': 'Jensen-Shannon divergence',
        'base': base,
        'windows': window_names,
        'divergence_matrix': divergence_dict,
        'metadata': {
            'num_windows': len(window_names),
            'num_topics': len(list(distributions.values())[0]),
            'computation_time': 'N/A'  # Would be added in full pipeline
        }
    }
    
    if output_path:
        save_divergence_results(results, output_path)
    
    return results


def main():
    """
    Main entry point for divergence calculation from command line.
    
    Usage:
        python -m src.models.metrics.divergence \
            --input results/stats/topic_vectors.json \
            --output results/stats/divergence_results.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Calculate Jensen-Shannon divergence between topic distributions'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Path to JSON file containing topic vectors'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Path to save divergence results'
    )
    parser.add_argument(
        '--base', '-b',
        type=int,
        default=2,
        help='Logarithm base for JS divergence (default: 2)'
    )
    
    args = parser.parse_args()
    
    logger = get_logger(__name__)
    logger.info("Starting divergence calculation")
    
    try:
        results = compute_pairwise_divergences(
            topic_vectors_path=args.input,
            output_path=args.output,
            base=args.base
        )
        
        logger.info("Divergence calculation completed successfully")
        logger.info(f"Results saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Error during divergence calculation: {str(e)}")
        raise


if __name__ == '__main__':
    main()
