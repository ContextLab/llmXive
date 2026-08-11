import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: str) -> Dict[str, np.ndarray]:
    """
    Load all routing cache files from the specified directory.
    
    Args:
        cache_dir: Path to the routing cache directory.
        
    Returns:
        Dictionary mapping image indices to routing tensors.
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_dir}")
    
    routing_data = {}
    for file in cache_path.glob("*.npy"):
        try:
            idx = int(file.stem)
            routing_data[idx] = np.load(file)
            logger.info(f"Loaded routing data for image {idx}: shape {routing_data[idx].shape}")
        except Exception as e:
            logger.error(f"Failed to load {file}: {e}")
    
    if not routing_data:
        raise ValueError("No valid routing data files found in cache directory")
    
    return routing_data

def compute_mean_routing_vectors(routing_data: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Compute the mean routing vector across all images and blocks for each timestep.
    
    Args:
        routing_data: Dictionary of routing tensors.
        
    Returns:
        Mean routing vector array of shape [timesteps, history_dim].
    """
    if not routing_data:
        raise ValueError("No routing data provided for mean computation")
    
    # Stack all routing data (assuming consistent shape across images)
    all_vectors = list(routing_data.values())
    stacked = np.stack(all_vectors, axis=0)  # Shape: [num_images, num_blocks, num_timesteps, history_dim]
    
    # Average over images and blocks
    mean_vectors = np.mean(stacked, axis=(0, 1))  # Shape: [num_timesteps, history_dim]
    
    logger.info(f"Computed mean routing vectors: shape {mean_vectors.shape}")
    return mean_vectors

def perform_clustering(mean_vectors: np.ndarray, max_k: int = 10) -> Tuple[Optional[KMeans], float, int]:
    """
    Perform k-means clustering on mean routing vectors to find optimal k.
    
    Args:
        mean_vectors: Mean routing vectors of shape [timesteps, history_dim].
        max_k: Maximum number of clusters to try.
        
    Returns:
        Tuple of (best_kmeans_model, silhouette_score, optimal_k) or (None, 0.0, 0) if clustering fails.
    """
    if mean_vectors.shape[0] < 2:
        logger.warning("Not enough timesteps for clustering")
        return None, 0.0, 0
    
    best_k = 0
    best_score = -1
    best_model = None
    
    # Try different k values
    for k in range(2, min(max_k + 1, mean_vectors.shape[0])):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(mean_vectors)
            
            # Compute silhouette score
            score = silhouette_score(mean_vectors, labels)
            
            if score > best_score:
                best_score = score
                best_k = k
                best_model = kmeans
                
            logger.info(f"k={k}, silhouette_score={score:.4f}")
            
        except Exception as e:
            logger.warning(f"Clustering failed for k={k}: {e}")
            continue
    
    if best_model is None:
        logger.warning("No valid clustering found")
        return None, 0.0, 0
    
    logger.info(f"Best clustering: k={best_k}, silhouette_score={best_score:.4f}")
    return best_model, best_score, best_k

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """
    Generate a global average routing vector as fallback.
    
    Args:
        mean_vectors: Mean routing vectors.
        
    Returns:
        Global average vector of shape [history_dim].
    """
    global_avg = np.mean(mean_vectors, axis=0)
    logger.info(f"Generated global average vector: shape {global_avg.shape}")
    return global_avg

def save_cluster_centers(model: KMeans, output_path: str, k: int):
    """
    Save cluster centers to a JSON file.
    
    Args:
        model: Trained KMeans model.
        output_path: Path to save the JSON file.
        k: Number of clusters.
    """
    centers = model.cluster_centers_.tolist()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'num_clusters': k,
            'cluster_centers': centers,
            'feature_dim': len(centers[0])
        }, f, indent=2)
    
    logger.info(f"Saved cluster centers to {output_path}")

def save_null_hypothesis_flag(output_path: str, is_null: bool, score: float, threshold: float = 0.25):
    """
    Save a flag indicating whether the null hypothesis condition was met.
    
    Args:
        output_path: Path to save the JSON flag file.
        is_null: True if silhouette score < threshold (null hypothesis condition met).
        score: The actual silhouette score.
        threshold: The threshold for null hypothesis detection.
    """
    flag_data = {
        'null_hypothesis_detected': is_null,
        'silhouette_score': float(score),
        'threshold': float(threshold),
        'message': f"Null hypothesis detected: silhouette score ({score:.4f}) < threshold ({threshold})" if is_null 
                   else f"Clustering valid: silhouette score ({score:.4f}) >= threshold ({threshold})"
    }
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    if is_null:
        logger.warning(f"NULL HYPOTHESIS DETECTED: {flag_data['message']}")
    else:
        logger.info(f"Clustering validation passed: {flag_data['message']}")

def run_clustering_analysis(
    cache_dir: str, 
    output_dir: str, 
    silhouette_threshold: float = 0.25
) -> Dict[str, Any]:
    """
    Run the full clustering analysis pipeline including null hypothesis validation.
    
    Args:
        cache_dir: Path to routing cache directory.
        output_dir: Path to save results.
        silhouette_threshold: Threshold for null hypothesis detection.
        
    Returns:
        Dictionary with analysis results.
    """
    logger.info(f"Starting clustering analysis with cache_dir={cache_dir}, output_dir={output_dir}")
    
    # Load routing data
    routing_data = load_routing_cache(cache_dir)
    
    # Compute mean vectors
    mean_vectors = compute_mean_routing_vectors(routing_data)
    
    # Perform clustering
    model, score, k = perform_clustering(mean_vectors)
    
    # Prepare output paths
    cache_path = Path(output_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    
    cluster_centers_path = str(cache_path / "cluster_centers.json")
    null_flag_path = str(cache_path / "null_hypothesis_flag.json")
    
    # Check for null hypothesis condition
    is_null_hypothesis = (k < 2) or (score < silhouette_threshold)
    
    # Save null hypothesis flag
    save_null_hypothesis_flag(null_flag_path, is_null_hypothesis, score, silhouette_threshold)
    
    if is_null_hypothesis:
        logger.warning("Null hypothesis condition met. Generating global average fallback.")
        global_avg = generate_global_average(mean_vectors)
        
        # Save global average as cluster centers (single "cluster")
        with open(cluster_centers_path, 'w') as f:
            json.dump({
                'num_clusters': 1,
                'cluster_centers': [global_avg.tolist()],
                'feature_dim': len(global_avg),
                'fallback_reason': 'null_hypothesis',
                'silhouette_score': float(score),
                'threshold': float(silhouette_threshold)
            }, f, indent=2)
        
        logger.info(f"Saved global average fallback to {cluster_centers_path}")
        
        return {
            'status': 'null_hypothesis',
            'silhouette_score': float(score),
            'threshold': float(silhouette_threshold),
            'num_clusters': 1,
            'fallback_used': True,
            'global_average_vector': global_avg.tolist()
        }
    else:
        # Save cluster centers
        save_cluster_centers(model, cluster_centers_path, k)
        
        return {
            'status': 'success',
            'silhouette_score': float(score),
            'threshold': float(silhouette_threshold),
            'num_clusters': k,
            'fallback_used': False
        }

def main():
    """Main entry point for clustering analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run clustering analysis on routing cache")
    parser.add_argument('--cache-dir', type=str, required=True, help='Path to routing cache directory')
    parser.add_argument('--output-dir', type=str, required=True, help='Path to save results')
    parser.add_argument('--threshold', type=float, default=0.25, help='Silhouette score threshold for null hypothesis')
    
    args = parser.parse_args()
    
    results = run_clustering_analysis(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        silhouette_threshold=args.threshold
    )
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()