import os
import sys
import json
import argparse
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from datasets import load_dataset
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from scipy.stats import zscore
import psutil

# Import local utilities
from utils.seeds import set_global_seed
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.config import get_config, get_clustering_params
from utils.data_loader import load_qwen_vla_dataset, DataFetchError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MAX_CLUSTERS = 50
MIN_SILHOUETTE_THRESHOLD = 0.25
OUTPUT_LOG_PATH = "data/results/clustering_method_log.json"

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_usage(limit_mb: float = 6000) -> bool:
    """Check if current memory usage is within limits."""
    current = get_process_memory_mb()
    if current > limit_mb:
        logger.warning(f"Memory usage {current:.2f}MB exceeds limit {limit_mb}MB")
        return False
    return True

def stream_dataset_iterator(dataset, chunk_size: int = 1000):
    """Iterator to process dataset in chunks."""
    buffer = []
    for item in dataset:
        buffer.append(item)
        if len(buffer) >= chunk_size:
            yield buffer
            buffer = []
    if buffer:
        yield buffer

def process_sample(sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single dataset sample to extract features."""
    try:
        # Extract action sequence (assuming 'action' field exists)
        action_seq = sample.get('action', [])
        text_instruction = sample.get('instruction', "")
        
        if not action_seq:
            return None

        # Extract kinematic features
        features = extract_kinematic_features(action_seq)
        
        if features is None or len(features) == 0:
            return None

        return {
            'instruction': text_instruction,
            'features': features,
            'sample_id': sample.get('id', hash(str(sample)))
        }
    except Exception as e:
        logger.warning(f"Failed to process sample: {e}")
        return None

def extract_features_batch(samples: List[Dict]) -> Tuple[np.ndarray, List[str], List[int]]:
    """Extract and stack features from a batch of processed samples."""
    features_list = []
    instructions = []
    ids = []
    
    for s in samples:
        if s:
            features_list.append(s['features'])
            instructions.append(s['instruction'])
            ids.append(s['sample_id'])
    
    if not features_list:
        return np.array([]), [], []
    
    return np.array(features_list), instructions, ids

def normalize_features(features: np.ndarray) -> np.ndarray:
    """Normalize features using z-score normalization."""
    if features.size == 0:
        return features
    return zscore(features, axis=0)

def calculate_silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
    """Calculate silhouette score for clustering validation."""
    if len(np.unique(labels)) < 2:
        return -1.0
    return silhouette_score(X, labels)

def calculate_calinski_harabasz_score(X: np.ndarray, labels: np.ndarray) -> float:
    """Calculate Calinski-Harabasz index for clustering validation."""
    if len(np.unique(labels)) < 2:
        return 0.0
    return calinski_harabasz_score(X, labels)

def run_kmeans_clustering(X: np.ndarray, k: int) -> Tuple[np.ndarray, float, float]:
    """Run K-means clustering and return labels and metrics."""
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    sil_score = calculate_silhouette_score(X, labels)
    ch_score = calculate_calinski_harabasz_score(X, labels)
    
    return labels, sil_score, ch_score

def run_hac_fallback(X: np.ndarray, max_clusters: int = 50) -> Tuple[np.ndarray, float, float, int]:
    """Run Hierarchical Agglomerative Clustering as fallback."""
    logger.info("Running HAC fallback clustering...")
    
    # Use a heuristic to determine number of clusters if not specified
    # For now, we'll try to find a valid number of clusters
    best_k = 2
    best_score = -1
    best_labels = None
    best_sil = -1
    best_ch = 0

    # Try a range of k values to find the best one
    # Since HAC requires n_clusters, we iterate
    for k in range(2, min(max_clusters + 1, len(X))):
        try:
            hac = AgglomerativeClustering(n_clusters=k, linkage='ward')
            labels = hac.fit_predict(X)
            sil = calculate_silhouette_score(X, labels)
            ch = calculate_calinski_harabasz_score(X, labels)
            
            if sil > best_score:
                best_score = sil
                best_k = k
                best_labels = labels
                best_sil = sil
                best_ch = ch
        except Exception as e:
            logger.warning(f"HAC failed for k={k}: {e}")
            continue

    if best_labels is None:
        # Fallback to 2 clusters if nothing worked
        hac = AgglomerativeClustering(n_clusters=2, linkage='ward')
        best_labels = hac.fit_predict(X)
        best_sil = calculate_silhouette_score(X, best_labels)
        best_ch = calculate_calinski_harabasz_score(X, best_labels)
        best_k = 2

    return best_labels, best_sil, best_ch, best_k

def run_clustering_with_adaptive_k_reduction(X: np.ndarray) -> Tuple[np.ndarray, int, float, float, str]:
    """
    Run K-means with adaptive k-reduction logic (FR-002a).
    Returns: labels, k_used, silhouette_score, calinski_harabasz_score, method
    """
    k = MAX_CLUSTERS
    final_labels = None
    final_sil = -1
    final_ch = 0
    method = "KMeans"

    logger.info(f"Starting adaptive K-reduction with k={k}")

    while k >= 1:
        if k == 1:
            # Degenerate case
            logger.warning("Reduced to k=1. Degenerate clustering.")
            # For k=1, silhouette is undefined/negative, set to -1
            final_labels = np.zeros(len(X), dtype=int)
            final_sil = -1.0
            final_ch = 0.0
            break

        try:
            labels, sil, ch = run_kmeans_clustering(X, k)
            logger.info(f"K-means k={k}: Silhouette={sil:.4f}, Calinski-Harabasz={ch:.4f}")

            if sil >= MIN_SILHOUETTE_THRESHOLD:
                final_labels = labels
                final_sil = sil
                final_ch = ch
                break
            
            # If score is too low, reduce k
            k -= 1
        except Exception as e:
            logger.error(f"K-means failed for k={k}: {e}")
            k -= 1
            continue

    if final_labels is None:
        # Should not happen if loop completes, but safety net
        final_labels = np.zeros(len(X), dtype=int)
        final_sil = -1.0
        final_ch = 0.0
    
    return final_labels, k, final_sil, final_ch, method

def run_hac_fallback_wrapper(X: np.ndarray, k_reduced: int, sil_score: float) -> Tuple[np.ndarray, float, float, int, str]:
    """
    Run HAC fallback if K-means reduction fails completely.
    Returns: labels, silhouette_score, calinski_harabasz_score, k_used, method
    """
    if k_reduced > 1 or sil_score >= MIN_SILHOUETTE_THRESHOLD:
        # No need for HAC
        return None, 0, 0, 0, ""

    logger.info("K-means reduction failed completely. Triggering HAC fallback.")
    labels, sil, ch, k_used = run_hac_fallback(X)
    return labels, sil, ch, k_used, "HAC"

def save_clustering_artifacts(
    labels: np.ndarray, 
    k: int, 
    sil_score: float, 
    ch_score: float, 
    method: str,
    sample_ids: List[int],
    output_dir: str = "data/processed"
):
    """Save clustering artifacts to disk."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save assignments
    assignments_df = pd.DataFrame({
        'sample_id': sample_ids,
        'cluster_id': labels
    })
    assignments_path = os.path.join(output_dir, "assignments.parquet")
    assignments_df.to_parquet(assignments_path, index=False)
    logger.info(f"Saved assignments to {assignments_path}")

    # Save cluster metadata (centers would need the original features, simplified here)
    metadata = {
        'k': k,
        'silhouette_score': sil_score,
        'calinski_harabasz_score': ch_score,
        'method': method,
        'timestamp': time.time(),
        'num_samples': len(labels)
    }
    metadata_path = os.path.join(output_dir, "clusters.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved cluster metadata to {metadata_path}")

    # Save the method log as required by T064
    log_entry = {
        'method': method,
        'k_used': k,
        'silhouette_score': sil_score,
        'calinski_harabasz_score': ch_score,
        'timestamp': time.time(),
        'threshold': MIN_SILHOUETTE_THRESHOLD
    }
    
    log_path = "data/results/clustering_method_log.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    logger.info(f"Saved clustering method log to {log_path}")

def verify_clustering_coverage(total_samples: int, assigned_samples: int) -> bool:
    """Verify clustering coverage meets threshold."""
    if total_samples == 0:
        return False
    ratio = assigned_samples / total_samples
    if ratio < 0.98:
        logger.error(f"Clustering coverage {ratio:.4f} < 0.98. Aborting.")
        return False
    return True

def run_ingestion_pipeline(
    dataset_name: str = "Qwen/Qwen-VLA",
    split: str = "train",
    streaming: bool = True,
    sample_limit: Optional[int] = None
) -> Dict[str, Any]:
    """Main pipeline function to ingest, cluster, and save artifacts."""
    logger.info(f"Starting ingestion pipeline for {dataset_name}")
    
    # Load dataset
    try:
        dataset = load_qwen_vla_dataset(dataset_name, split=split, streaming=streaming)
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        raise
    
    processed_samples = []
    chunk_count = 0
    
    # Process in streaming chunks
    for chunk in stream_dataset_iterator(dataset, chunk_size=500):
        for sample in chunk:
            processed = process_sample(sample)
            if processed:
                processed_samples.append(processed)
        
        chunk_count += 1
        if sample_limit and len(processed_samples) >= sample_limit:
            break
        
        if chunk_count % 10 == 0:
            logger.info(f"Processed {chunk_count} chunks, {len(processed_samples)} samples so far...")
            if not check_memory_usage():
                logger.warning("Memory limit approaching. Stopping ingestion.")
                break

    logger.info(f"Ingestion complete. Total samples: {len(processed_samples)}")

    if len(processed_samples) == 0:
        raise ValueError("No valid samples extracted from dataset.")

    # Extract features
    features, instructions, sample_ids = extract_features_batch(processed_samples)
    
    if features.size == 0:
        raise ValueError("No features extracted.")

    # Normalize
    X = normalize_features(features)
    
    # Adaptive K-reduction
    labels, k_used, sil_score, ch_score, method = run_clustering_with_adaptive_k_reduction(X)
    
    # Check for HAC fallback
    if k_used == 1 and sil_score < MIN_SILHOUETTE_THRESHOLD:
        labels, sil_score, ch_score, k_used, method = run_hac_fallback_wrapper(X, k_used, sil_score)
        if method == "HAC":
            logger.info("HAC Fallback applied.")
    
    # Verify coverage
    if not verify_clustering_coverage(len(sample_ids), len(labels)):
        sys.exit(1)

    # Save artifacts
    save_clustering_artifacts(
        labels, k_used, sil_score, ch_score, method, sample_ids
    )

    return {
        'k': k_used,
        'silhouette_score': sil_score,
        'calinski_harabasz_score': ch_score,
        'method': method,
        'num_samples': len(sample_ids)
    }

def main():
    parser = argparse.ArgumentParser(description="Ingest and cluster Qwen-VLA dataset")
    parser.add_argument('--dataset', type=str, default="Qwen/Qwen-VLA", help="Dataset name")
    parser.add_argument('--split', type=str, default="train", help="Dataset split")
    parser.add_argument('--stream', action='store_true', default=True, help="Use streaming")
    parser.add_argument('--limit', type=int, default=None, help="Max samples to process")
    
    args = parser.parse_args()
    
    set_global_seed(42)
    
    try:
        result = run_ingestion_pipeline(
            dataset_name=args.dataset,
            split=args.split,
            streaming=args.stream,
            sample_limit=args.limit
        )
        logger.info(f"Pipeline completed successfully. Result: {result}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
