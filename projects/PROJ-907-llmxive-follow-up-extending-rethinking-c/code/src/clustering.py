import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.config import get_results_path, get_routing_cache_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load all routing weight matrices from the cache directory."""
    if cache_dir is None:
        cache_dir = get_routing_cache_path()
    
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_path}")
    
    routing_data = []
    for file_path in cache_path.glob("*.npy"):
        try:
            data = np.load(file_path, allow_pickle=True).item()
            routing_data.append(data)
        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")
    
    if not routing_data:
        raise ValueError(f"No valid routing data found in {cache_path}")
    
    return routing_data

def compute_mean_routing_vectors(routing_data: List[Dict[str, Any]]) -> np.ndarray:
    """
    Compute the mean routing vector across all images/blocks for each timestep.
    Input: List of dicts with shape [blocks, timesteps, history_dim]
    Output: Array of shape [timesteps, history_dim]
    """
    if not routing_data:
        raise ValueError("No routing data provided")
    
    # Assume all entries have the same dimensions
    sample = routing_data[0]
    if isinstance(sample, dict):
        # Extract the routing weight matrix (usually under a key like 'weights' or 'routing')
        key = next(iter(sample.keys()))
        all_vectors = [d[key] for d in routing_data]
    elif isinstance(sample, np.ndarray):
        all_vectors = routing_data
    else:
        raise TypeError(f"Unexpected data type: {type(sample)}")
    
    # Stack all vectors: shape [num_images, blocks, timesteps, history_dim]
    stacked = np.stack(all_vectors, axis=0)
    
    # Mean across images and blocks: shape [timesteps, history_dim]
    mean_vectors = stacked.mean(axis=(0, 1))
    
    return mean_vectors

def perform_clustering(mean_vectors: np.ndarray, max_k: int = 10) -> Tuple[np.ndarray, float, int]:
    """
    Perform k-means clustering on mean routing vectors.
    Returns: (cluster_centers, silhouette_score, k)
    """
    n_samples = mean_vectors.shape[0]
    if n_samples < 2:
        logger.warning("Not enough samples for clustering (n < 2)")
        return np.array([]), -1.0, 0
    
    best_k = 0
    best_score = -1.0
    best_centers = np.array([])
    
    # Try k from 2 to min(max_k, n_samples)
    for k in range(2, min(max_k + 1, n_samples)):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(mean_vectors)
        
        # Compute silhouette score
        score = silhouette_score(mean_vectors, labels)
        
        if score > best_score:
            best_score = score
            best_k = k
            best_centers = kmeans.cluster_centers_
    
    return best_centers, best_score, best_k

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """Generate a global average routing vector as fallback."""
    return mean_vectors.mean(axis=0)

def save_cluster_centers(centers: np.ndarray, score: float, k: int, output_path: Optional[Path] = None):
    """Save cluster centers and metadata to JSON."""
    if output_path is None:
        output_path = get_routing_cache_path() / "cluster_centers.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "cluster_centers": centers.tolist(),
        "silhouette_score": float(score),
        "k": int(k),
        "num_vectors": centers.shape[0] if centers.size > 0 else 0
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved cluster centers to {output_path}")

def save_null_hypothesis_flag(score: float, threshold: float = 0.25, output_path: Optional[Path] = None):
    """
    Save a flag file if the silhouette score is below the threshold.
    This explicitly flags the null hypothesis case (k < 2 or score < 0.25).
    """
    if output_path is None:
        results_path = get_results_path()
        output_path = results_path / "null_hypothesis_flag.json"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    is_null_hypothesis = score < threshold
    
    flag_data = {
        "silhouette_score": float(score),
        "threshold": float(threshold),
        "is_null_hypothesis": is_null_hypothesis,
        "warning": "Silhouette score is below threshold. Clustering may not be meaningful." if is_null_hypothesis else None
    }
    
    with open(output_path, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    if is_null_hypothesis:
        logger.warning(f"NULL HYPOTHESIS DETECTED: Silhouette score {score:.4f} < {threshold}. Check {output_path}")
    else:
        logger.info(f"Clustering validation passed: Silhouette score {score:.4f} >= {threshold}")
    
    return is_null_hypothesis

def run_clustering_analysis(cache_dir: Optional[Path] = None, threshold: float = 0.25, max_k: int = 10) -> Dict[str, Any]:
    """
    Main entry point for clustering analysis with null hypothesis validation.
    Returns a dict with results and validation status.
    """
    logger.info("Starting clustering analysis...")
    
    # Load data
    routing_data = load_routing_cache(cache_dir)
    logger.info(f"Loaded {len(routing_data)} routing samples")
    
    # Compute mean vectors
    mean_vectors = compute_mean_routing_vectors(routing_data)
    logger.info(f"Computed mean vectors of shape {mean_vectors.shape}")
    
    # Perform clustering
    centers, score, k = perform_clustering(mean_vectors, max_k)
    logger.info(f"Clustering result: k={k}, silhouette_score={score:.4f}")
    
    # Save cluster centers
    save_cluster_centers(centers, score, k)
    
    # Validate against null hypothesis
    is_null = save_null_hypothesis_flag(score, threshold)
    
    # If null hypothesis, generate global average
    if is_null:
        global_avg = generate_global_average(mean_vectors)
        logger.info("Generated global average as fallback due to null hypothesis")
        return {
            "k": k,
            "silhouette_score": score,
            "is_null_hypothesis": True,
            "global_average": global_avg.tolist(),
            "centers": centers.tolist() if centers.size > 0 else []
        }
    else:
        return {
            "k": k,
            "silhouette_score": score,
            "is_null_hypothesis": False,
            "centers": centers.tolist()
        }

def main():
    """Command-line entry point."""
    results = run_clustering_analysis()
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
