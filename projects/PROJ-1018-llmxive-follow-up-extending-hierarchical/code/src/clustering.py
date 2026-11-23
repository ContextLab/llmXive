import logging
import json
import os
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
import numpy as np
from dataclasses import dataclass, field

from src.models import StaticIndex
from src.config import Config

logger = logging.getLogger(__name__)

def apply_pca(profiles: List[Dict[str, Any]], n_components: int = 50) -> np.ndarray:
    """
    Apply PCA dimensionality reduction to relevance profiles.
    
    Args:
        profiles: List of dicts with 'scores' key containing float lists
        n_components: Number of PCA components to retain
        
    Returns:
        Reduced data matrix as numpy array
    """
    try:
        from sklearn.decomposition import PCA
    except ImportError:
        raise ImportError("scikit-learn is required for PCA. Install via: pip install scikit-learn")
    
    if not profiles:
        raise ValueError("Cannot apply PCA to empty list of profiles")
        
    # Extract score vectors
    score_vectors = [np.array(p['scores']) for p in profiles]
    
    # Pad to uniform length if necessary (shouldn't happen with valid data)
    max_len = max(len(v) for v in score_vectors)
    padded = np.zeros((len(score_vectors), max_len))
    for i, v in enumerate(score_vectors):
        padded[i, :len(v)] = v
        
    # Apply PCA
    pca = PCA(n_components=n_components, random_state=42)
    reduced = pca.fit_transform(padded)
    
    logger.info(f"PCA reduced {padded.shape} to {reduced.shape}, explained variance: {pca.explained_variance_ratio_.sum():.4f}")
    return reduced

def run_kmeans(data: np.ndarray, k: int, retry_count: int = 3) -> Tuple[np.ndarray, List[int]]:
    """
    Run K-Means clustering with retry logic for empty cluster convergence.
    
    Args:
        data: Input data matrix (n_samples, n_features)
        k: Number of clusters
        retry_count: Maximum number of retries for empty clusters
        
    Returns:
        Tuple of (centroids, labels)
    """
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        raise ImportError("scikit-learn is required for K-Means. Install via: pip install scikit-learn")
    
    if k <= 0:
        raise ValueError("k must be positive")
    if k > len(data):
        raise ValueError(f"k ({k}) cannot exceed number of samples ({len(data)})")
        
    best_kmeans = None
    best_inertia = float('inf')
    
    for attempt in range(retry_count):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        labels = kmeans.fit_predict(data)
        
        # Check for empty clusters
        unique_labels = set(labels)
        if len(unique_labels) < k:
            logger.warning(f"K-Means attempt {attempt+1}: Found {len(unique_labels)} clusters instead of {k}. Retrying...")
            continue
        
        if kmeans.inertia_ < best_inertia:
            best_inertia = kmeans.inertia_
            best_kmeans = kmeans
        
        # If we have a valid solution, break early
        break
    else:
        # If all retries failed to find k clusters, use the best we have
        if best_kmeans is None:
            raise RuntimeError(f"K-Means failed to converge to {k} clusters after {retry_count} attempts")
        
    return best_kmeans.cluster_centers_, best_kmeans.labels_

@dataclass
class StaticIndex:
    """Static index for HiLS attention sparsity patterns."""
    centroids: np.ndarray
    chunk_to_cluster: Dict[str, int]
    k: int
    pca_n_components: int = 50
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export."""
        return {
            'centroids': self.centroids.tolist(),
            'chunk_to_cluster': self.chunk_to_cluster,
            'k': self.k,
            'pca_n_components': self.pca_n_components
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StaticIndex':
        """Deserialize from dictionary."""
        return cls(
            centroids=np.array(data['centroids']),
            chunk_to_cluster=data['chunk_to_cluster'],
            k=data['k'],
            pca_n_components=data.get('pca_n_components', 50)
        )

def generate_static_index(
    profiles: List[Dict[str, Any]],
    k: int,
    pca_components: int = 50,
    seed: int = 42
) -> StaticIndex:
    """
    Generate a static index from relevance profiles using PCA + K-Means.
    
    Args:
        profiles: List of relevance profiles with 'chunk_id' and 'scores'
        k: Number of clusters
        pca_components: Number of PCA components
        seed: Random seed for reproducibility
        
    Returns:
        StaticIndex object
    """
    if not profiles:
        raise ValueError("Cannot generate static index from empty profiles")
        
    # Extract chunk IDs for mapping
    chunk_ids = [p['chunk_id'] for p in profiles]
    
    # Apply PCA
    reduced_data = apply_pca(profiles, n_components=pca_components)
    
    # Run K-Means
    centroids, labels = run_kmeans(reduced_data, k)
    
    # Build chunk-to-cluster mapping
    chunk_to_cluster = {
        chunk_id: int(label) 
        for chunk_id, label in zip(chunk_ids, labels)
    }
    
    return StaticIndex(
        centroids=centroids,
        chunk_to_cluster=chunk_to_cluster,
        k=k,
        pca_n_components=pca_components
    )

def save_static_index(index: StaticIndex, path: str) -> None:
    """
    Serialize static index to JSON file.
    
    Args:
        index: StaticIndex object to save
        path: Output file path
    """
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    
    output = index.to_dict()
    # Add metadata
    output['metadata'] = {
        'k': index.k,
        'pca_n_components': index.pca_n_components,
        'num_chunks': len(index.chunk_to_cluster)
    }
    
    with open(path, 'w') as f:
        json.dump(output, f, indent=2)
        
    logger.info(f"Saved static index with {len(index.chunk_to_cluster)} chunks to {path}")

def benchmark_lookup(index: StaticIndex, token_count: int = 32000) -> bool:
    """
    Benchmark lookup latency for the static index.
    
    Measures the time to perform cluster lookups for a given token count
    (simulating attention mask generation). Returns True if latency < 50ms.
    
    Args:
        index: StaticIndex object to benchmark
        token_count: Number of tokens to simulate (default 32k)
        
    Returns:
        True if latency < 50ms, False otherwise
    """
    if not index.chunk_to_cluster:
        raise ValueError("StaticIndex has no chunk-to-cluster mapping")
        
    # Simulate lookup operations
    # In practice, chunk_count ~ token_count / chunk_size
    # Assuming chunk_size ~ 512 tokens, we get ~62 chunks for 32k tokens
    chunk_size = 512
    num_lookups = max(1, token_count // chunk_size)
    
    # Warm-up runs
    for _ in range(2):
        for i in range(min(num_lookups, len(index.chunk_to_cluster))):
            chunk_id = list(index.chunk_to_cluster.keys())[i % len(index.chunk_to_cluster)]
            _ = index.chunk_to_cluster[chunk_id]
    
    # Timed runs
    start_time = time.perf_counter()
    for _ in range(10):  # 10 measurement runs
        for i in range(num_lookups):
            chunk_id = list(index.chunk_to_cluster.keys())[i % len(index.chunk_to_cluster)]
            _ = index.chunk_to_cluster[chunk_id]
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    avg_latency_ms = (total_time / 10) * 1000  # Convert to milliseconds
    
    logger.info(f"Lookup benchmark: {num_lookups} lookups, avg latency: {avg_latency_ms:.2f}ms")
    
    # Return True if latency < 50ms
    return avg_latency_ms < 50.0

def main():
    """Main entry point for clustering module."""
    # Load config
    config = Config()
    
    # Load relevance profiles
    profiles_path = os.path.join(config.data_interim_dir, 'relevance_profiles.json')
    if not os.path.exists(profiles_path):
        raise FileNotFoundError(f"Profiles not found at {profiles_path}")
        
    with open(profiles_path, 'r') as f:
        profiles = json.load(f)
        
    logger.info(f"Loaded {len(profiles)} relevance profiles")
    
    # Generate static index
    static_index = generate_static_index(
        profiles=profiles,
        k=config.k_clusters,
        pca_components=50,
        seed=config.seed
    )
    
    # Save static index
    output_path = os.path.join(config.data_processed_dir, 'static_index.json')
    save_static_index(static_index, output_path)
    
    # Benchmark lookup
    is_fast = benchmark_lookup(static_index, token_count=32000)
    logger.info(f"Lookup benchmark result: {'PASS' if is_fast else 'FAIL'} (< 50ms)")
    
    return static_index

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()