"""
Clustering module for analyzing routing patterns in SiT-XL with DAR.

This module implements the logic to:
1. Load recorded routing tensors from the tracing phase.
2. Compute mean routing vectors across images/blocks for each timestep.
3. Apply k-means clustering to group timesteps.
4. Compute silhouette scores and handle null hypotheses.
5. Save cluster centers and null hypothesis flags.
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from src.config import get_routing_cache_path, get_results_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_routing_cache(cache_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load all routing tensor files from the cache directory.
    
    Args:
        cache_dir: Path to the routing cache directory. Defaults to config setting.
        
    Returns:
        List of dictionaries containing routing data for each image.
        
    Raises:
        FileNotFoundError: If the cache directory does not exist or is empty.
    """
    if cache_dir is None:
        cache_dir = get_routing_cache_path()
        
    if not cache_dir.exists():
        raise FileNotFoundError(f"Routing cache directory not found: {cache_dir}")
        
    routing_files = list(cache_dir.glob("*.npy")) + list(cache_dir.glob("*.pt"))
    
    if not routing_files:
        raise FileNotFoundError(f"No routing tensor files found in {cache_dir}")
        
    logger.info(f"Loading {len(routing_files)} routing files from {cache_dir}")
    
    routing_data = []
    for file_path in routing_files:
        try:
            if file_path.suffix == '.npy':
                data = np.load(file_path)
            elif file_path.suffix == '.pt':
                import torch
                data = torch.load(file_path, map_location='cpu')
                if isinstance(data, torch.Tensor):
                    data = data.numpy()
            else:
                continue
                
            routing_data.append({
                'file_path': str(file_path),
                'data': data,
                'filename': file_path.name
            })
            logger.debug(f"Loaded {file_path.name}: shape {data.shape}")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise
            
    return routing_data

def compute_mean_routing_vectors(routing_data: List[Dict[str, Any]]) -> np.ndarray:
    """
    Compute the mean routing vector across all images and blocks for each timestep.
    
    Input shape per file: [num_blocks, num_timesteps, history_dim]
    Output shape: [num_timesteps, history_dim]
    
    Args:
        routing_data: List of dictionaries containing routing data.
        
    Returns:
        Mean routing vectors array with shape [num_timesteps, history_dim].
    """
    if not routing_data:
        raise ValueError("No routing data provided")
        
    # Collect all data arrays
    all_arrays = [item['data'] for item in routing_data]
    
    # Verify shapes are consistent
    base_shape = all_arrays[0].shape
    if len(base_shape) != 3:
        raise ValueError(f"Expected 3D arrays (blocks, timesteps, history_dim), got shape {base_shape}")
        
    num_blocks, num_timesteps, history_dim = base_shape
    
    logger.info(f"Processing {len(all_arrays)} files with shape {base_shape}")
    
    # Stack all arrays along a new image dimension
    # Shape: [num_images, num_blocks, num_timesteps, history_dim]
    stacked = np.stack(all_arrays, axis=0)
    
    # Compute mean across images (axis 0) and blocks (axis 1)
    # Result shape: [num_timesteps, history_dim]
    mean_vectors = np.mean(stacked, axis=(0, 1))
    
    logger.info(f"Computed mean routing vectors with shape {mean_vectors.shape}")
    return mean_vectors

def perform_clustering(
    mean_vectors: np.ndarray,
    max_k: int = 10,
    random_state: int = 42
) -> Tuple[Optional[KMeans], Optional[float], int]:
    """
    Perform k-means clustering on mean routing vectors to group timesteps.
    
    Args:
        mean_vectors: Array of shape [num_timesteps, history_dim].
        max_k: Maximum number of clusters to try.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (KMeans model, silhouette score, optimal k).
        Returns (None, None, 0) if clustering is not possible (null hypothesis).
    """
    num_timesteps = mean_vectors.shape[0]
    
    # Null hypothesis check: need at least 2 timesteps to cluster
    if num_timesteps < 2:
        logger.warning(f"Not enough timesteps ({num_timesteps}) for clustering. Null hypothesis.")
        return None, None, 0
        
    # Try different k values to find the optimal one
    best_k = 0
    best_score = -1
    best_model = None
    
    # Determine feasible k range
    feasible_ks = range(2, min(max_k + 1, num_timesteps))
    
    if not list(feasible_ks):
        logger.warning("No feasible k values for clustering.")
        return None, None, 0
        
    logger.info(f"Testing k values from 2 to {min(max_k, num_timesteps - 1)}")
    
    for k in feasible_ks:
        try:
            kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            labels = kmeans.fit_predict(mean_vectors)
            
            # Compute silhouette score
            if len(np.unique(labels)) > 1:
                score = silhouette_score(mean_vectors, labels)
            else:
                score = -1
                
            logger.info(f"k={k}, silhouette_score={score:.4f}")
            
            if score > best_score:
                best_score = score
                best_k = k
                best_model = kmeans
                
        except Exception as e:
            logger.warning(f"Failed clustering with k={k}: {e}")
            continue
    
    # Null hypothesis check: silhouette score too low
    if best_score < 0.25:
        logger.warning(f"Best silhouette score ({best_score:.4f}) < 0.25. Null hypothesis triggered.")
        return None, None, 0
        
    logger.info(f"Selected k={best_k} with silhouette score {best_score:.4f}")
    return best_model, best_score, best_k

def generate_global_average(mean_vectors: np.ndarray) -> np.ndarray:
    """
    Generate a global average routing vector as a fallback for null hypothesis.
    
    Args:
        mean_vectors: Array of shape [num_timesteps, history_dim].
        
    Returns:
        Global average vector with shape [history_dim].
    """
    global_avg = np.mean(mean_vectors, axis=0)
    logger.info(f"Generated global average vector with shape {global_avg.shape}")
    return global_avg

def save_null_hypothesis_flag(
    is_null: bool,
    reason: str,
    output_path: Optional[Path] = None
) -> None:
    """
    Save a flag indicating if the null hypothesis was triggered.
    
    Args:
        is_null: Whether the null hypothesis was triggered.
        reason: Explanation for the null hypothesis.
        output_path: Path to save the flag file. Defaults to config setting.
    """
    if output_path is None:
        results_dir = get_results_path()
        output_path = results_dir / "null_hypothesis_flag.json"
        
    flag_data = {
        "is_null_hypothesis": is_null,
        "reason": reason,
        "timestamp": str(Path(output_path).parent.name)  # Simple timestamp placeholder
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(flag_data, f, indent=2)
        
    logger.info(f"Saved null hypothesis flag to {output_path}")

def save_cluster_centers(
    model: Optional[KMeans],
    mean_vectors: np.ndarray,
    output_path: Optional[Path] = None
) -> None:
    """
    Save cluster centers to a JSON file.
    
    Args:
        model: Trained KMeans model.
        mean_vectors: Input mean vectors.
        output_path: Path to save the cluster centers. Defaults to config setting.
    """
    if output_path is None:
        cache_dir = get_routing_cache_path()
        output_path = cache_dir / "cluster_centers.json"
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if model is not None:
        centers = model.cluster_centers_
        centers_list = centers.tolist()
        is_null = False
    else:
        # Fallback: use global average
        global_avg = generate_global_average(mean_vectors)
        centers_list = global_avg.tolist()
        is_null = True
        
    result_data = {
        "is_null_hypothesis": is_null,
        "num_clusters": model.n_clusters if model else 1,
        "cluster_centers": centers_list,
        "input_shape": list(mean_vectors.shape)
    }
    
    with open(output_path, 'w') as f:
        json.dump(result_data, f, indent=2)
        
    logger.info(f"Saved cluster centers to {output_path}")

def run_clustering_analysis(
    cache_dir: Optional[Path] = None,
    max_k: int = 10,
    random_state: int = 42,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run the full clustering analysis pipeline.
    
    Args:
        cache_dir: Path to routing cache directory.
        max_k: Maximum number of clusters to try.
        random_state: Random seed for reproducibility.
        output_dir: Directory to save results. Defaults to config setting.
        
    Returns:
        Dictionary containing analysis results.
    """
    logger.info("Starting clustering analysis...")
    
    # Load routing data
    try:
        routing_data = load_routing_cache(cache_dir)
    except Exception as e:
        logger.error(f"Failed to load routing cache: {e}")
        raise
        
    # Compute mean vectors
    mean_vectors = compute_mean_routing_vectors(routing_data)
    
    # Perform clustering
    model, score, best_k = perform_clustering(mean_vectors, max_k, random_state)
    
    # Determine if null hypothesis was triggered
    is_null = (model is None)
    reason = ""
    if is_null:
        if best_k == 0:
            reason = "Insufficient timesteps for clustering"
        else:
            reason = f"Silhouette score ({score:.4f}) < 0.25 threshold"
        
        # Generate global average for null case
        global_avg = generate_global_average(mean_vectors)
        logger.info(f"Null hypothesis triggered: {reason}")
    else:
        logger.info(f"Clustering successful: k={best_k}, silhouette={score:.4f}")
        
    # Save outputs
    if output_dir is None:
        output_dir = get_routing_cache_path()
        
    save_cluster_centers(model, mean_vectors, output_dir / "cluster_centers.json")
    save_null_hypothesis_flag(is_null, reason, output_dir / "null_hypothesis_flag.json")
    
    # Print silhouette score as required
    if score is not None:
        print(f"Silhouette score: {score:.4f}")
    else:
        print("Silhouette score: N/A (null hypothesis)")
        
    # Prepare results
    results = {
        "is_null_hypothesis": is_null,
        "reason": reason,
        "optimal_k": best_k,
        "silhouette_score": float(score) if score is not None else None,
        "input_shape": list(mean_vectors.shape),
        "num_files_processed": len(routing_data)
    }
    
    logger.info("Clustering analysis completed.")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run clustering analysis on routing tensors")
    parser.add_argument("--cache-dir", type=str, default=None, help="Path to routing cache directory")
    parser.add_argument("--max-k", type=int, default=10, help="Maximum number of clusters to try")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    
    results = run_clustering_analysis(
        cache_dir=cache_dir,
        max_k=args.max_k,
        random_state=args.seed
    )
    
    print(json.dumps(results, indent=2))
