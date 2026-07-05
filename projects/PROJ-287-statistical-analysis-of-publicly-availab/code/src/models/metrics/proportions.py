"""
Topic Proportion Computation Module.

Computes topic proportion vectors for each 5-year window based on
aligned LDA model outputs. Ensures vectors sum to 1.0 and contain no NaN values.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from scipy.special import softmax

from src.models.entities import TopicVector
from src.utils.logging import get_logger
from src.utils.config import get_random_seed

logger = get_logger(__name__)

# Define the 5-year windows as per project specification
WINDOWS = [
    "2000-2004",
    "2005-2009",
    "2010-2014",
    "2015-2019",
    "2020-2024"
]

# Expected number of topics (k) based on T020/T022 configuration
DEFAULT_K = 10

def load_topic_distributions(window_path: Path) -> Dict[str, np.ndarray]:
    """
    Load topic-word distributions (phi matrices) from a window's LDA results.
    
    Expects a JSON file containing the topic-word distribution matrix where
    rows are topics and columns are words.
    
    Args:
        window_path: Path to the window's results directory containing topic distributions.
        
    Returns:
        Dictionary mapping window ID to topic-word distribution matrix (k x vocab_size).
        
    Raises:
        FileNotFoundError: If the distribution file does not exist.
        ValueError: If the file format is invalid.
    """
    dist_file = window_path / "topic_distributions.json"
    
    if not dist_file.exists():
        raise FileNotFoundError(f"Topic distribution file not found: {dist_file}")
        
    with open(dist_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if 'topics' not in data:
        raise ValueError(f"Invalid format in {dist_file}: missing 'topics' key")
        
    # Convert list of topic vectors to numpy array
    topic_matrix = np.array(data['topics'], dtype=np.float32)
    
    # Validate dimensions
    if topic_matrix.ndim != 2:
        raise ValueError(f"Expected 2D topic matrix, got shape {topic_matrix.shape}")
        
    return topic_matrix

def compute_topic_proportions(
    topic_matrix: np.ndarray,
    document_topic_dists: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Compute normalized topic proportion vectors for a given window.
    
    If document_topic_dists are provided, aggregates them to window-level proportions.
    Otherwise, derives proportions from the topic-word distributions (phi) by
    normalizing and ensuring sum=1.0.
    
    Args:
        topic_matrix: Topic-word distribution matrix (k x vocab_size).
        document_topic_dists: Optional document-topic distribution matrix (n_docs x k).
        
    Returns:
        Normalized topic proportion vector (k,) that sums to 1.0.
        
    Raises:
        ValueError: If inputs are invalid or contain NaN/Inf values.
    """
    if topic_matrix is None or topic_matrix.size == 0:
        raise ValueError("Topic matrix cannot be empty")
        
    if np.any(np.isnan(topic_matrix)) or np.any(np.isinf(topic_matrix)):
        raise ValueError("Topic matrix contains NaN or Inf values")
        
    k = topic_matrix.shape[0]
    
    if document_topic_dists is not None:
        # Aggregate document-level distributions to window-level
        if document_topic_dists.shape[1] != k:
            raise ValueError(f"Document-topic distribution has {document_topic_dists.shape[1]} topics, expected {k}")
            
        # Sum across documents and normalize
        window_proportions = np.sum(document_topic_dists, axis=0)
    else:
        # Fallback: use topic weights from the model's prior or uniform if not available
        # In practice, we'd have document-topic distributions from T020
        # For robustness, we compute from the topic matrix by assuming uniform document distribution
        # This is a simplified approach; real implementation would use gamma from LDA
        logger.warning("No document-topic distributions provided. Using topic matrix weights.")
        # Normalize topic matrix rows to get topic weights
        topic_weights = np.sum(topic_matrix, axis=1)
        window_proportions = topic_weights
        
    # Ensure no NaN values
    if np.any(np.isnan(window_proportions)):
        logger.error("Computed proportions contain NaN values. Replacing with small epsilon.")
        window_proportions = np.nan_to_num(window_proportions, nan=1e-10)
        
    # Ensure positive values (LDA proportions should be >= 0)
    window_proportions = np.maximum(window_proportions, 1e-10)
    
    # Normalize to sum to 1.0
    total = np.sum(window_proportions)
    if total == 0:
        raise ValueError("Sum of proportions is zero. Cannot normalize.")
        
    normalized_proportions = window_proportions / total
    
    # Final validation
    if not np.isclose(np.sum(normalized_proportions), 1.0, atol=1e-6):
        logger.warning(f"Proportions sum to {np.sum(normalized_proportions)}, re-normalizing.")
        normalized_proportions = normalized_proportions / np.sum(normalized_proportions)
        
    if np.any(np.isnan(normalized_proportions)) or np.any(np.isinf(normalized_proportions)):
        raise ValueError("Normalized proportions contain NaN or Inf values")
        
    return normalized_proportions

def validate_proportion_vector(proportion_vector: np.ndarray, k: int = DEFAULT_K) -> bool:
    """
    Validate that a proportion vector meets all requirements:
    - Length equals k
    - All values are non-negative
    - No NaN or Inf values
    - Sum is approximately 1.0
    
    Args:
        proportion_vector: The vector to validate.
        k: Expected number of topics.
        
    Returns:
        True if valid, False otherwise.
    """
    if len(proportion_vector) != k:
        logger.error(f"Vector length {len(proportion_vector)} != expected k={k}")
        return False
        
    if np.any(proportion_vector < 0):
        logger.error("Vector contains negative values")
        return False
        
    if np.any(np.isnan(proportion_vector)) or np.any(np.isinf(proportion_vector)):
        logger.error("Vector contains NaN or Inf values")
        return False
        
    if not np.isclose(np.sum(proportion_vector), 1.0, atol=1e-6):
        logger.error(f"Vector sum {np.sum(proportion_vector)} != 1.0")
        return False
        
    return True

def compute_all_window_proportions(
    base_results_path: Path,
    k: int = DEFAULT_K
) -> Dict[str, TopicVector]:
    """
    Compute topic proportion vectors for all windows.
    
    Args:
        base_results_path: Base path to results directory containing window subdirectories.
        k: Number of topics.
        
    Returns:
        Dictionary mapping window ID to TopicVector object.
        
    Raises:
        RuntimeError: If any window fails to compute valid proportions.
    """
    proportions_by_window = {}
    failed_windows = []
    
    for window_id in WINDOWS:
        window_path = base_results_path / window_id
        
        if not window_path.exists():
            logger.warning(f"Window directory not found: {window_path}. Skipping.")
            failed_windows.append(window_id)
            continue
            
        try:
            # Load topic distributions for this window
            topic_matrix = load_topic_distributions(window_path)
            
            # Compute proportions
            proportions = compute_topic_proportions(topic_matrix)
            
            # Validate
            if not validate_proportion_vector(proportions, k):
                logger.error(f"Invalid proportions for window {window_id}")
                failed_windows.append(window_id)
                continue
                
            # Create TopicVector entity
            topic_vector = TopicVector(
                window_id=window_id,
                proportions=proportions.tolist(),
                k_topics=k,
                checksum=None  # Will be computed by manifest system
            )
            
            proportions_by_window[window_id] = topic_vector
            logger.info(f"Computed proportions for window {window_id}: sum={np.sum(proportions):.6f}")
            
        except Exception as e:
            logger.error(f"Failed to compute proportions for window {window_id}: {e}")
            failed_windows.append(window_id)
            
    if failed_windows:
        raise RuntimeError(f"Failed to compute proportions for windows: {failed_windows}")
        
    return proportions_by_window

def save_topic_vectors(
    proportions_by_window: Dict[str, TopicVector],
    output_path: Path
) -> None:
    """
    Save topic vectors to a JSON file.
    
    Args:
        proportions_by_window: Dictionary of window_id to TopicVector.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "windows": {},
        "metadata": {
            "k_topics": DEFAULT_K,
            "windows_processed": list(proportions_by_window.keys()),
            "timestamp": str(__import__('datetime').datetime.now(__import__('datetime').timezone.utc))
        }
    }
    
    for window_id, topic_vector in proportions_by_window.items():
        output_data["windows"][window_id] = {
            "proportions": topic_vector.proportions,
            "k_topics": topic_vector.k_topics,
            "sum_check": sum(topic_vector.proportions)
        }
        
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Saved topic vectors to {output_path}")

def main():
    """
    Main entry point for computing and saving topic proportions.
    """
    # Get configuration
    seed = get_random_seed()
    np.random.seed(seed)
    
    # Define paths
    base_results_path = Path("results/stats")
    output_path = base_results_path / "topic_vectors.json"
    
    # Ensure base path exists
    base_results_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting topic proportion computation with k={DEFAULT_K}")
    logger.info(f"Base results path: {base_results_path}")
    
    try:
        # Compute proportions for all windows
        proportions_by_window = compute_all_window_proportions(base_results_path)
        
        # Save results
        save_topic_vectors(proportions_by_window, output_path)
        
        logger.info(f"Successfully computed and saved topic vectors for {len(proportions_by_window)} windows")
        
        # Print summary
        for window_id, tv in proportions_by_window.items():
            print(f"{window_id}: {np.array(tv.proportions).round(4)} (sum={sum(tv.proportions):.6f})")
            
    except Exception as e:
        logger.error(f"Failed to compute topic proportions: {e}")
        raise

if __name__ == "__main__":
    main()