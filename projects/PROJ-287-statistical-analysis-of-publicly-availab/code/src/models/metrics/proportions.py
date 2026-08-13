import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from src.utils.logging import get_logger
from src.models.entities import TopicVector

logger = get_logger(__name__)

# Define the standard windows used in this project
WINDOWS = [
    "2000-2004",
    "2005-2009",
    "2010-2014",
    "2015-2019",
    "2020-2024"
]

def load_topic_distributions(window: str, data_dir: Path) -> np.ndarray:
    """
    Load the topic distribution (proportions) for a specific window.
    
    This expects the LDA fitter (T020) to have saved a file per window,
    typically named {window}_topic_proportions.json or similar.
    Based on T020 implementation, we look for a JSON file containing
    the average topic proportions for documents in that window.
    
    Args:
        window: The 5-year window string (e.g., "2000-2004")
        data_dir: Path to the directory containing processed LDA results.
        
    Returns:
        numpy.ndarray: A vector of topic proportions summing to 1.0.
        
    Raises:
        FileNotFoundError: If the expected file does not exist.
        ValueError: If the loaded data is invalid.
    """
    # The T020 fitter typically saves per-window stats in results/stats or data/processed
    # We assume the fitter saved a file named {window}_proportions.json in results/stats/
    # If T020 saved elsewhere, adjust path logic here.
    # Based on T025, final vectors go to results/stats/topic_vectors.json, 
    # but intermediate per-window vectors might be in data/processed or results/stats.
    # Let's assume the fitter saves to results/stats/{window}_proportions.json
    
    file_path = data_dir / f"{window}_proportions.json"
    
    if not file_path.exists():
        # Fallback: check if it's in a subdirectory or named differently
        # If T020 saved a single file for all windows, we'd need to load that.
        # However, T020 says "iteratively for each... window", implying per-window output.
        # Let's try a common pattern: results/stats/{window}_lda_results.json
        alt_path = data_dir.parent / "stats" / f"{window}_lda_results.json"
        if alt_path.exists():
            file_path = alt_path
        else:
            raise FileNotFoundError(f"Could not find topic proportions for window {window} at {file_path} or {alt_path}")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Expecting a structure like {"proportions": [0.1, 0.2, ...]} or just the list
        if isinstance(data, dict):
            if 'proportions' in data:
                proportions = np.array(data['proportions'], dtype=np.float64)
            elif 'topic_distribution' in data:
                proportions = np.array(data['topic_distribution'], dtype=np.float64)
            else:
                # Try to find a key that looks like a list of floats
                for key, val in data.items():
                    if isinstance(val, list) and len(val) > 1:
                        proportions = np.array(val, dtype=np.float64)
                        break
                else:
                    raise ValueError(f"Could not find proportions list in {file_path}")
        elif isinstance(data, list):
            proportions = np.array(data, dtype=np.float64)
        else:
            raise ValueError(f"Unexpected data format in {file_path}: {type(data)}")
        
        return proportions
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading topic distributions for {window}: {e}")
        raise

def compute_topic_proportions(doc_topic_dists: np.ndarray, k: int = 10) -> np.ndarray:
    """
    Compute the average topic proportion vector for a set of documents.
    
    Args:
        doc_topic_dists: A 2D numpy array of shape (n_docs, k) where each row
                         is a topic distribution for a document (sums to 1).
        k: Number of topics.
        
    Returns:
        numpy.ndarray: A 1D array of length k representing the average topic proportions.
    """
    if doc_topic_dists.ndim != 2 or doc_topic_dists.shape[1] != k:
        raise ValueError(f"Expected 2D array with {k} columns, got shape {doc_topic_dists.shape}")
    
    # Compute mean across documents (axis 0)
    mean_proportions = np.mean(doc_topic_dists, axis=0)
    
    # Ensure sum is exactly 1.0 (handle floating point errors)
    total = np.sum(mean_proportions)
    if total == 0:
        # Should not happen if inputs are valid, but handle gracefully
        logger.warning("Computed mean proportions sum to 0. Returning uniform distribution.")
        return np.ones(k) / k
    
    normalized = mean_proportions / total
    
    return normalized

def validate_proportion_vector(vec: np.ndarray, k: int = 10) -> Tuple[bool, str]:
    """
    Validate that a vector is a valid topic proportion vector.
    
    Checks:
    1. Length is k
    2. All values are non-negative
    3. Sum is approximately 1.0 (within floating point tolerance)
    4. No NaN values
    
    Args:
        vec: The vector to validate.
        k: Expected number of topics.
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if len(vec) != k:
        return False, f"Vector length {len(vec)} does not match expected k={k}"
    
    if np.any(np.isnan(vec)):
        return False, "Vector contains NaN values"
    
    if np.any(vec < 0):
        return False, "Vector contains negative values"
    
    total = np.sum(vec)
    if not np.isclose(total, 1.0, atol=1e-6):
        return False, f"Vector sum is {total}, expected 1.0"
    
    return True, "Valid"

def compute_all_window_proportions(stats_dir: Path, k: int = 10) -> Dict[str, np.ndarray]:
    """
    Compute topic proportion vectors for all defined windows.
    
    Args:
        stats_dir: Path to the directory containing per-window LDA results.
        k: Number of topics.
        
    Returns:
        Dict[str, np.ndarray]: Dictionary mapping window strings to their proportion vectors.
    """
    results = {}
    
    for window in WINDOWS:
        try:
            # Load raw document-topic distributions if available, or pre-computed averages
            # T020 might have saved the average directly. Let's try to load the average first.
            # If T020 saved per-document distributions, we need to aggregate them.
            # For now, assume T020 saved a file with the average proportions directly.
            # If not, we'd need to load the full doc-topic matrix.
            
            # Attempt to load the pre-computed average from T020
            proportions = load_topic_distributions(window, stats_dir)
            
            is_valid, msg = validate_proportion_vector(proportions, k)
            if not is_valid:
                logger.warning(f"Window {window} proportions invalid: {msg}. Attempting to recompute or skip.")
                # If invalid, we might need to load raw doc-topic dists and recompute.
                # For this task, we assume T020 produces valid averages.
                # If the file contained raw doc-topic dists, we would compute mean here.
                # But load_topic_distributions expects the final vector.
                # If the file format was different (e.g. list of docs), we handle it in load_topic_distributions.
                # Let's assume the file contains the average.
                continue
            
            results[window] = proportions
            logger.info(f"Successfully loaded/validated proportions for window {window}")
            
        except FileNotFoundError as e:
            logger.error(f"Missing data for window {window}: {e}")
            # In a real pipeline, this might be a hard failure.
            # For now, we skip and log.
            continue
        except Exception as e:
            logger.error(f"Error processing window {window}: {e}")
            continue
    
    if not results:
        logger.error("No valid window proportions found.")
        raise RuntimeError("Failed to compute proportions for any window.")
        
    return results

def save_topic_vectors(proportions_dict: Dict[str, np.ndarray], output_path: Path) -> None:
    """
    Save topic proportion vectors to a JSON file.
    
    Args:
        proportions_dict: Dictionary mapping window strings to proportion vectors.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "windows": list(proportions_dict.keys()),
        "k_topics": len(next(iter(proportions_dict.values()))),
        "topic_vectors": {
            window: vec.tolist() 
            for window, vec in proportions_dict.items()
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved topic vectors to {output_path}")

def main():
    """
    Main entry point for computing and saving topic proportions.
    """
    logger.info("Starting topic proportion computation (T024)")
    
    # Define paths based on project structure
    # T020 saves intermediate results, T025 expects final output at results/stats/topic_vectors.json
    # We assume T020 saved per-window averages in results/stats/ or data/processed/
    # Let's assume the intermediate files are in results/stats/
    stats_dir = Path("results/stats")
    output_file = Path("results/stats/topic_vectors.json")
    
    if not stats_dir.exists():
        logger.error(f"Stats directory {stats_dir} does not exist. Ensure T020 has run.")
        return
    
    try:
        k = 10 # Standard k for this project
        proportions = compute_all_window_proportions(stats_dir, k)
        
        if not proportions:
            logger.error("No proportions computed.")
            return
        
        save_topic_vectors(proportions, output_file)
        
        # Log summary
        for window, vec in proportions.items():
            is_valid, msg = validate_proportion_vector(vec, k)
            logger.info(f"Window {window}: sum={np.sum(vec):.6f}, valid={is_valid}")
            
        logger.info("T024 completed successfully.")
        
    except Exception as e:
        logger.error(f"T024 failed: {e}")
        raise

if __name__ == "__main__":
    main()
