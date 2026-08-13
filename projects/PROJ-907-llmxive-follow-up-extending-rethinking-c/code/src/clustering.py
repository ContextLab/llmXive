import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: str) -> List[np.ndarray]:
    """
    Load all routing tensor files from the cache directory.
    Expects files named image_{index}.npy or image_{index}.pt (converted to npy).
    Returns a list of numpy arrays, each shape [num_blocks, num_timesteps, history_dim].
    """
    cache_path = Path(cache_dir)
    if not cache_path.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_dir}")

    routing_tensors = []
    files = sorted([f for f in cache_path.iterdir() if f.suffix in ['.npy', '.pt']])
    
    if not files:
        raise ValueError(f"No routing tensor files found in {cache_dir}")

    for file_path in files:
        logger.info(f"Loading routing tensor from {file_path}")
        if file_path.suffix == '.npy':
            tensor = np.load(file_path)
        elif file_path.suffix == '.pt':
            # PyTorch tensors need to be loaded and converted
            import torch
            tensor = torch.load(file_path, map_location='cpu').numpy()
        else:
            continue
        
        if tensor.ndim != 3:
            logger.warning(f"Skipping {file_path}: expected 3D tensor, got {tensor.ndim}D")
            continue
        
        routing_tensors.append(tensor)

    if not routing_tensors:
        raise ValueError("No valid routing tensors loaded")

    logger.info(f"Loaded {len(routing_tensors)} routing tensors")
    return routing_tensors

def compute_mean_routing_vectors(routing_tensors: List[np.ndarray]) -> np.ndarray:
    """
    Compute the mean routing vector across all images/blocks for each timestep.
    Input: List of arrays [num_blocks, num_timesteps, history_dim]
    Output: Array [num_timesteps, history_dim]
    """
    if not routing_tensors:
        raise ValueError("No routing tensors provided")

    # Stack all tensors: [num_images, num_blocks, num_timesteps, history_dim]
    stacked = np.stack(routing_tensors, axis=0)
    
    # Mean across images (axis 0) and blocks (axis 1)
    # Result: [num_timesteps, history_dim]
    mean_vectors = np.mean(stacked, axis=(0, 1))
    
    logger.info(f"Computed mean routing vectors: shape {mean_vectors.shape}")
    return mean_vectors

def perform_clustering(
    mean_vectors: np.ndarray,
    distance_threshold: float = 0.1,
    max_clusters: int = 10
) -> Tuple[Optional[KMeans], int, float]:
    """
    Apply k-means clustering to group timesteps based on mean routing vectors.
    Returns (model, k, silhouette_score) or (None, 0, -1.0) if clustering fails.
    """
    num_timesteps = mean_vectors.shape[0]
    
    # Determine number of clusters based on distance threshold
    # We'll try to find the optimal k that satisfies the distance constraint
    # For simplicity, we'll use a heuristic: k = min(num_timesteps, max_clusters)
    # but ensure k >= 2 for meaningful clustering
    
    if num_timesteps < 2:
        logger.warning("Not enough timesteps for clustering")
        return None, 0, -1.0

    # Try different k values and pick the one with best silhouette score
    best_k = 2
    best_score = -1.0
    best_model = None

    # Determine reasonable range for k
    k_range = range(2, min(max_clusters + 1, num_timesteps + 1))

    for k in k_range:
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(mean_vectors)
            
            # Calculate silhouette score
            from sklearn.metrics import silhouette_score
            if len(np.unique(labels)) > 1:
                score = silhouette_score(mean_vectors, labels)
            else:
                score = -1.0
            
            if score > best_score:
                best_score = score
                best_k = k
                best_model = kmeans
        
        except Exception as e:
            logger.warning(f"Clustering with k={k} failed: {e}")
            continue

    if best_model is None:
        logger.warning("No valid clustering found")
        return None, 0, -1.0

    logger.info(f"Best clustering: k={best_k}, silhouette_score={best_score:.4f}")
    return best_model, best_k, best_score

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """
    Generate global average vector as fallback for null hypothesis.
    Input: [num_timesteps, history_dim]
    Output: [history_dim]
    """
    global_avg = np.mean(mean_vectors, axis=0)
    logger.info(f"Generated global average vector: shape {global_avg.shape}")
    return global_avg

def save_cluster_centers(
    model: KMeans,
    silhouette_score: float,
    output_path: str
) -> None:
    """
    Save cluster centers to JSON file.
    Schema: [{"cluster_id": int, "center_vector": [float], "silhouette_score": float}, ...]
    """
    centers = model.cluster_centers_.tolist()
    output_data = []
    
    for i, center in enumerate(centers):
        output_data.append({
            "cluster_id": i,
            "center_vector": center,
            "silhouette_score": float(silhouette_score)
        })

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved cluster centers to {output_path}")

def save_null_hypothesis_flag(output_path: str, reason: str) -> None:
    """
    Save null hypothesis flag to JSON file.
    Schema: {"flag": true, "reason": str, "silhouette_score": float, "k": int}
    """
    flag_data = {
        "flag": True,
        "reason": reason,
        "timestamp": str(Path(output_path).parent.name)  # Placeholder for actual timestamp
    }
    
    with open(output_path, 'w') as f:
        json.dump(flag_data, f, indent=2)
    
    logger.warning(f"Null hypothesis flag saved: {reason}")

def run_clustering_analysis(
    cache_dir: str,
    output_dir: str,
    distance_threshold: float = 0.1
) -> Dict[str, Any]:
    """
    Main function to run clustering analysis on routing tensors.
    Handles null hypothesis and saves all required artifacts.
    """
    # Ensure output directories exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cache_path = Path(cache_dir)
    
    # Load routing tensors
    logger.info(f"Loading routing tensors from {cache_dir}")
    routing_tensors = load_routing_cache(str(cache_path))
    
    # Compute mean routing vectors
    logger.info("Computing mean routing vectors")
    mean_vectors = compute_mean_routing_vectors(routing_tensors)
    
    # Perform clustering
    logger.info(f"Performing clustering with distance_threshold={distance_threshold}")
    model, k, silhouette_score = perform_clustering(mean_vectors, distance_threshold)
    
    # Handle null hypothesis
    is_null_hypothesis = False
    null_reason = ""
    
    if k < 2 or silhouette_score < 0.25:
        is_null_hypothesis = True
        if k < 2:
            null_reason = f"Number of clusters k={k} is less than 2"
        else:
            null_reason = f"Silhouette score {silhouette_score:.4f} is less than 0.25"
        
        logger.warning(f"Null hypothesis triggered: {null_reason}")
        
        # Generate global average as fallback
        global_avg = generate_global_average(mean_vectors)
        
        # Save null hypothesis flag
        null_flag_path = Path(output_dir) / "null_hypothesis_flag.json"
        save_null_hypothesis_flag(str(null_flag_path), null_reason)
        
        # Save cluster centers with global average (as a single cluster)
        centers_path = Path(output_dir) / "cluster_centers.json"
        centers_data = [{
            "cluster_id": 0,
            "center_vector": global_avg.tolist(),
            "silhouette_score": float(silhouette_score)
        }]
        with open(centers_path, 'w') as f:
            json.dump(centers_data, f, indent=2)
        
        logger.info(f"Saved global average to {centers_path}")
        
        return {
            "is_null_hypothesis": True,
            "k": k,
            "silhouette_score": float(silhouette_score),
            "reason": null_reason,
            "centers_path": str(centers_path),
            "null_flag_path": str(null_flag_path)
        }
    
    # Save cluster centers for valid clustering
    centers_path = Path(output_dir) / "cluster_centers.json"
    save_cluster_centers(model, silhouette_score, str(centers_path))
    
    logger.info(f"Silhouette score: {silhouette_score:.4f}")
    
    return {
        "is_null_hypothesis": False,
        "k": k,
        "silhouette_score": float(silhouette_score),
        "centers_path": str(centers_path),
        "model": model
    }

def main():
    """Main entry point for clustering analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run clustering analysis on routing tensors")
    parser.add_argument("--cache-dir", type=str, default="data/routing_cache",
                      help="Directory containing routing tensor files")
    parser.add_argument("--output-dir", type=str, default="data/routing_cache",
                      help="Directory to save output files")
    parser.add_argument("--distance-threshold", type=float, default=0.1,
                      help="Distance threshold for clustering")
    
    args = parser.parse_args()
    
    result = run_clustering_analysis(
        cache_dir=args.cache_dir,
        output_dir=args.output_dir,
        distance_threshold=args.distance_threshold
    )
    
    # Print summary
    print(f"Clustering Analysis Complete:")
    print(f"  Null Hypothesis: {result['is_null_hypothesis']}")
    print(f"  Number of Clusters (k): {result['k']}")
    print(f"  Silhouette Score: {result['silhouette_score']:.4f}")
    if result['is_null_hypothesis']:
        print(f"  Reason: {result['reason']}")
    print(f"  Output Files:")
    print(f"    Cluster Centers: {result['centers_path']}")
    if result.get('null_flag_path'):
        print(f"    Null Flag: {result['null_flag_path']}")

if __name__ == "__main__":
    main()
