import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json
import time

from src.models import StaticIndex, RelevanceProfile
from src.config import Config

logger = logging.getLogger(__name__)

def apply_pca(profiles: List[RelevanceProfile], n_components: int = 50) -> np.ndarray:
    """
    Applies PCA dimensionality reduction to a list of RelevanceProfiles.
    
    Args:
        profiles: List of RelevanceProfile objects.
        n_components: Number of principal components to keep.
        
    Returns:
        np.ndarray of shape (len(profiles), n_components).
    """
    if not profiles:
        logger.warning("Empty profile list provided to apply_pca")
        return np.array([])
    
    # Extract scores as a matrix
    data_matrix = np.array([p.scores for p in profiles])
    
    # Standardize data before PCA
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data_matrix)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    reduced_data = pca.fit_transform(scaled_data)
    
    logger.info(f"PCA applied: reduced shape {reduced_data.shape}, explained variance ratio: {pca.explained_variance_ratio_.sum():.4f}")
    return reduced_data

def run_kmeans(data: np.ndarray, k: int, retry_count: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Runs K-Means clustering with retry logic for empty cluster convergence.
    
    Args:
        data: Input data array of shape (n_samples, n_features).
        k: Number of clusters.
        retry_count: Maximum number of retries if convergence fails or empty clusters occur.
        
    Returns:
        Tuple of (centroids, labels)
    """
    if data.size == 0:
        raise ValueError("Input data for K-Means cannot be empty.")
        
    best_labels = None
    best_inertia = np.inf
    best_centroids = None
    
    for attempt in range(retry_count):
        try:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
            labels = kmeans.fit_predict(data)
            
            # Check for empty clusters (labels should cover 0 to k-1)
            unique_labels = np.unique(labels)
            if len(unique_labels) < k:
                logger.warning(f"K-Means attempt {attempt + 1} resulted in {len(unique_labels)} clusters instead of {k}. Retrying...")
                continue
                
            if kmeans.inertia_ < best_inertia:
                best_inertia = kmeans.inertia_
                best_labels = labels
                best_centroids = kmeans.cluster_centers_
                
        except Exception as e:
            logger.warning(f"K-Means attempt {attempt + 1} failed: {e}")
            continue
            
    if best_labels is None:
        raise RuntimeError("K-Means failed to converge to a valid solution after retries.")
        
    logger.info(f"K-Means converged with inertia {best_inertia:.4f} after {attempt + 1} attempts.")
    return best_centroids, best_labels

def generate_static_index(profiles: List[RelevanceProfile], k: int, n_pca_components: int = 50) -> StaticIndex:
    """
    Generates a StaticIndex from a list of RelevanceProfiles.
    
    Steps:
    1. Apply PCA to reduce dimensionality of relevance scores.
    2. Run K-Means clustering on reduced data.
    3. Map each chunk_id to its assigned cluster ID.
    4. Return StaticIndex object.
    
    Args:
        profiles: List of RelevanceProfile objects.
        k: Number of clusters.
        n_pca_components: Number of PCA components.
        
    Returns:
        StaticIndex instance.
    """
    if not profiles:
        raise ValueError("Cannot generate StaticIndex from empty profile list.")
        
    logger.info(f"Generating StaticIndex with k={k} for {len(profiles)} profiles.")
    
    # 1. PCA
    reduced_data = apply_pca(profiles, n_components=n_pca_components)
    
    # 2. K-Means
    centroids, labels = run_kmeans(reduced_data, k)
    
    # 3. Build mapping
    chunk_to_cluster = {}
    for profile, label in zip(profiles, labels):
        chunk_to_cluster[profile.chunk_id] = int(label)
        
    # 4. Construct StaticIndex
    index = StaticIndex(
        centroids=centroids,
        chunk_to_cluster=chunk_to_cluster,
        k=k
    )
    
    logger.info(f"StaticIndex generated: {len(chunk_to_cluster)} mappings, {k} clusters.")
    return index

def save_static_index(index: StaticIndex, path: str) -> None:
    """
    Serializes and saves a StaticIndex to a JSON file.
    
    Args:
        index: StaticIndex object to save.
        path: File path to write the JSON.
    """
    logger.info(f"Saving StaticIndex to {path}")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(index.to_dict(), f, indent=2)
    logger.info("StaticIndex saved successfully.")

def benchmark_lookup(index: StaticIndex, token_count: int) -> bool:
    """
    Benchmarks the lookup latency of the static index.
    
    Args:
        index: StaticIndex object.
        token_count: Number of lookups to simulate.
        
    Returns:
        True if latency < 50ms, False otherwise.
    """
    if not index.chunk_to_cluster:
        logger.warning("Empty chunk_to_cluster map, cannot benchmark.")
        return False
        
    keys = list(index.chunk_to_cluster.keys())
    if not keys:
        return False
        
    start_time = time.perf_counter()
    for _ in range(token_count):
        # Simulate random lookup
        _ = index.chunk_to_cluster[keys[0]] 
    end_time = time.perf_counter()
    
    latency_ms = (end_time - start_time) * 1000
    logger.info(f"Benchmark: {token_count} lookups took {latency_ms:.2f}ms")
    
    return latency_ms < 50.0

def main():
    """
    Main entry point for generating the static index from extracted profiles.
    This function assumes profiles have been generated and saved by T015.
    """
    # Load config
    config = Config()
    
    # Load profiles (simplified for this script context)
    profiles_path = "data/interim/relevance_profiles.json"
    try:
        with open(profiles_path, 'r') as f:
            profiles_data = json.load(f)
        profiles = [RelevanceProfile(**p) for p in profiles_data]
        logger.info(f"Loaded {len(profiles)} profiles from {profiles_path}")
    except FileNotFoundError:
        logger.error(f"Profiles file not found at {profiles_path}. Ensure T015 has run.")
        return
        
    # Generate Index
    static_index = generate_static_index(profiles, k=config.k_clusters)
    
    # Save Index
    output_path = "data/processed/static_index.json"
    save_static_index(static_index, output_path)
    
    # Benchmark
    benchmark_lookup(static_index, 1000)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()