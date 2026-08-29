"""
Jensen-Shannon Divergence calculations for topic distribution analysis.

This module implements the computation of Jensen-Shannon divergence between
topic proportion vectors across different time windows. It uses scipy's
implementation with base-2 logarithm for interpretability in bits.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
from scipy.spatial.distance import jensenshannon

from src.utils.logging import get_logger

# Configure module logger
logger = get_logger(__name__)


def validate_topic_distribution(proportions: np.ndarray, window_name: str = "unknown") -> bool:
    """
    Validate that a topic distribution vector is valid for JS divergence calculation.
    
    Conditions:
    1. Must be 1D array
    2. All values must be non-negative
    3. Sum must be approximately 1.0 (within floating point tolerance)
    4. No NaN or Inf values
    
    Args:
        proportions: Numpy array of topic proportions
        window_name: Name of the window for logging purposes
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If the distribution is invalid
    """
    if proportions.ndim != 1:
        raise ValueError(f"Window '{window_name}': Distribution must be 1D, got {proportions.ndim}D")
        
    if np.any(proportions < 0):
        raise ValueError(f"Window '{window_name}': Distribution contains negative values")
        
    if np.any(np.isnan(proportions)) or np.any(np.isinf(proportions)):
        raise ValueError(f"Window '{window_name}': Distribution contains NaN or Inf values")
        
    total = np.sum(proportions)
    if not np.isclose(total, 1.0, atol=1e-6):
        raise ValueError(f"Window '{window_name}': Distribution sum is {total}, expected ~1.0")
        
    logger.debug(f"Window '{window_name}': Distribution validation passed (sum={total:.6f})")
    return True


def calculate_js_divergence(p: np.ndarray, q: np.ndarray, window_pair: Tuple[str, str]) -> float:
    """
    Calculate Jensen-Shannon divergence between two topic distributions.
    
    Uses base-2 logarithm for interpretability in bits. The JS divergence
    is symmetric and bounded between 0 and 1.
    
    Args:
        p: First topic distribution (must sum to 1)
        q: Second topic distribution (must sum to 1)
        window_pair: Tuple of (window1_name, window2_name) for logging
        
    Returns:
        float: JS divergence value in [0, 1]
        
    Raises:
        ValueError: If distributions are invalid
    """
    window1, window2 = window_pair
    
    # Validate inputs
    validate_topic_distribution(p, window1)
    validate_topic_distribution(q, window2)
    
    # scipy.spatial.distance.jensenshannon returns sqrt(JS), so we square it
    # to get the actual JS divergence value
    js_distance = jensenshannon(p, q, base=2)
    js_divergence = js_distance ** 2
    
    logger.debug(f"JS divergence between {window1} and {window2}: {js_divergence:.6f}")
    return js_divergence


def calculate_js_divergence_matrix(
    topic_vectors: Dict[str, np.ndarray],
    window_order: Optional[List[str]] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Calculate pairwise JS divergence matrix for all windows.
    
    Args:
        topic_vectors: Dictionary mapping window names to topic distribution arrays
        window_order: Optional list specifying the order of windows in the matrix.
                    If None, uses sorted keys of topic_vectors.
                    
    Returns:
        Tuple of (divergence_matrix, window_names) where:
        - divergence_matrix is a square matrix with JS divergence values
        - window_names is the list of window names in matrix order
    """
    if window_order is None:
        window_order = sorted(topic_vectors.keys())
        
    n_windows = len(window_order)
    divergence_matrix = np.zeros((n_windows, n_windows))
    
    # Convert to numpy array for efficient indexing
    vectors = [topic_vectors[win] for win in window_order]
    
    for i in range(n_windows):
        for j in range(i, n_windows):
            if i == j:
                # JS divergence of a distribution with itself is 0
                divergence_matrix[i, j] = 0.0
            else:
                js_div = calculate_js_divergence(
                    vectors[i], 
                    vectors[j], 
                    (window_order[i], window_order[j])
                )
                divergence_matrix[i, j] = js_div
                divergence_matrix[j, i] = js_div  # JS is symmetric
                
    logger.info(f"Computed divergence matrix for {n_windows} windows")
    return divergence_matrix, window_order


def load_topic_vectors_from_file(file_path: Union[str, Path]) -> Dict[str, np.ndarray]:
    """
    Load topic vectors from a JSON file.
    
    Expected format:
    {
        "window_name_1": [0.1, 0.2, ..., 0.1],
        "window_name_2": [...],
        ...
    }
    
    Args:
        file_path: Path to the JSON file containing topic vectors
                    
    Returns:
        Dictionary mapping window names to numpy arrays
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the file format is invalid
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Topic vectors file not found: {file_path}")
        
    with open(file_path, 'r') as f:
        data = json.load(f)
        
    result = {}
    for window_name, vector in data.items():
        arr = np.array(vector, dtype=np.float64)
        result[window_name] = arr
        
    logger.info(f"Loaded topic vectors for {len(result)} windows from {file_path}")
    return result


def save_divergence_results(
    divergence_matrix: np.ndarray,
    window_names: List[str],
    output_path: Union[str, Path]
) -> None:
    """
    Save divergence results to a JSON file.
    
    Args:
        divergence_matrix: 2D numpy array of JS divergence values
        window_names: List of window names corresponding to matrix rows/cols
        output_path: Path to save the results JSON file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "window_names": window_names,
        "divergence_matrix": divergence_matrix.tolist(),
        "num_windows": len(window_names),
        "num_topics": divergence_matrix.shape[0] // len(window_names) if len(window_names) > 0 else 0
    }
    
    # Calculate summary statistics
    if divergence_matrix.size > 0:
        # Exclude diagonal (self-divergence = 0)
        upper_tri_indices = np.triu_indices_from(divergence_matrix, k=1)
        upper_tri_values = divergence_matrix[upper_tri_indices]
        
        result["summary"] = {
            "mean_divergence": float(np.mean(upper_tri_values)),
            "max_divergence": float(np.max(upper_tri_values)),
            "min_divergence": float(np.min(upper_tri_values)),
            "std_divergence": float(np.std(upper_tri_values))
        }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Saved divergence results to {output_path}")


def compute_pairwise_divergences(
    topic_vectors: Dict[str, np.ndarray],
    window_order: Optional[List[str]] = None
) -> Dict[Tuple[str, str], float]:
    """
    Compute all pairwise JS divergences as a dictionary.
    
    Args:
        topic_vectors: Dictionary mapping window names to topic distributions
        window_order: Optional list specifying window order
        
    Returns:
        Dictionary mapping (window1, window2) tuples to JS divergence values
    """
    matrix, names = calculate_js_divergence_matrix(topic_vectors, window_order)
    
    result = {}
    n = len(names)
    for i in range(n):
        for j in range(i + 1, n):
            result[(names[i], names[j])] = float(matrix[i, j])
            
    return result


def main() -> None:
    """
    Main entry point for running divergence analysis.
    
    This function:
    1. Loads topic vectors from results/stats/topic_vectors.json
    2. Computes pairwise JS divergences
    3. Saves results to results/stats/divergence_results.json
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent.parent
    topic_vectors_path = project_root / "results" / "stats" / "topic_vectors.json"
    output_path = project_root / "results" / "stats" / "divergence_results.json"
    
    logger.info(f"Starting JS divergence analysis")
    logger.info(f"Loading topic vectors from: {topic_vectors_path}")
    
    try:
        # Load topic vectors
        topic_vectors = load_topic_vectors_from_file(topic_vectors_path)
        
        if not topic_vectors:
            raise ValueError("No topic vectors loaded. Check input file.")
        
        logger.info(f"Loaded {len(topic_vectors)} window vectors")
        
        # Define expected window order
        expected_windows = [
            "2000-2004",
            "2005-2009", 
            "2010-2014",
            "2015-2019",
            "2020-2024"
        ]
        
        # Filter to only expected windows if present
        available_windows = [w for w in expected_windows if w in topic_vectors]
        
        if len(available_windows) < 2:
            raise ValueError(f"Need at least 2 windows for divergence analysis. Found: {list(topic_vectors.keys())}")
        
        # Compute pairwise divergences
        pairwise_results = compute_pairwise_divergences(topic_vectors, available_windows)
        
        # Compute full matrix
        divergence_matrix, window_names = calculate_js_divergence_matrix(
            topic_vectors, 
            available_windows
        )
        
        # Save results
        save_divergence_results(divergence_matrix, window_names, output_path)
        
        # Log summary
        logger.info("Divergence analysis complete")
        logger.info(f"Results saved to: {output_path}")
        
        # Print pairwise results for quick inspection
        logger.info("Pairwise JS divergences:")
        for (w1, w2), value in sorted(pairwise_results.items()):
            logger.info(f"  {w1} vs {w2}: {value:.6f}")
            
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during divergence analysis: {e}")
        raise


if __name__ == "__main__":
    # Setup basic logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()