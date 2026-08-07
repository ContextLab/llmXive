"""
Clustering pipeline for Qwen-VLA dataset with adaptive K-reduction logic.

This module implements the core clustering functionality for the non-neural VLA approximation,
including:
- Streaming data loading
- Kinematic feature extraction
- Adaptive K-means clustering with silhouette score validation
- HAC fallback for degenerate cases
- Artifact generation and validation
"""
import os
import sys
import json
import argparse
import logging
import time
import itertools
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from datasets import load_dataset
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler
import psutil

# Import project utilities
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from utils.seeds import set_global_seed
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.config import get_clustering_params, get_config
from utils.validation import validate_cluster_assignments, compute_file_checksum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_K = 50
DEFAULT_MIN_SILHOUETTE = 0.25
DEFAULT_K_REDUCTION_STEP = 1
MAX_ITERATIONS = 100
MIN_CLUSTER_SIZE = 100
COVERAGE_THRESHOLD = 0.98

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def check_memory_usage(max_mb: float = 6000) -> bool:
    """Check if current memory usage is within limits."""
    current_mb = get_process_memory_mb()
    if current_mb > max_mb:
        logger.warning(f"Memory usage {current_mb:.2f}MB exceeds limit {max_mb}MB")
        return False
    return True

def stream_dataset_iterator(dataset, batch_size: int = 100):
    """
    Stream dataset in batches to manage memory.
    
    Args:
        dataset: HuggingFace dataset object
        batch_size: Number of samples per batch
        
    Yields:
        Batch of samples as dictionaries
    """
    batch = []
    for sample in dataset:
        batch.append(sample)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def process_sample(sample: Dict[str, Any], trajectory_length: int = 50) -> Optional[np.ndarray]:
    """
    Process a single sample from the dataset.
    
    Args:
        sample: Dictionary containing text and action data
        trajectory_length: Expected trajectory length
        
    Returns:
        Processed trajectory array or None if invalid
    """
    try:
        # Extract action sequence (assuming it's in 'action' or 'actions' field)
        action_key = 'action' if 'action' in sample else 'actions'
        if action_key not in sample:
            logger.warning(f"Sample missing action data: {sample.get('id', 'unknown')}")
            return None
        
        actions = sample[action_key]
        
        # Convert to numpy array
        if isinstance(actions, list):
            traj = np.array(actions)
        elif isinstance(actions, np.ndarray):
            traj = actions
        else:
            logger.warning(f"Unexpected action type: {type(actions)}")
            return None
        
        # Ensure correct shape
        if traj.ndim == 1:
            traj = traj.reshape(-1, 1)
        
        # Pad or truncate to trajectory_length
        if traj.shape[0] < trajectory_length:
            pad_width = ((0, trajectory_length - traj.shape[0]), (0, 0))
            traj = np.pad(traj, pad_width, mode='edge')
        elif traj.shape[0] > trajectory_length:
            traj = traj[:trajectory_length]
        
        return traj
    except Exception as e:
        logger.warning(f"Error processing sample: {e}")
        return None

def extract_features_batch(traj_batch: List[np.ndarray]) -> np.ndarray:
    """
    Extract kinematic features from a batch of trajectories.
    
    Args:
        traj_batch: List of trajectory arrays
        
    Returns:
        Array of extracted features (velocity, acceleration, joint angles)
    """
    features = []
    for traj in traj_batch:
        if traj is None:
            continue
        
        try:
            feats = extract_kinematic_features(traj)
            # Flatten features for clustering
            feat_vec = np.concatenate([
                feats['velocities'].flatten(),
                feats['accelerations'].flatten(),
                feats['joint_angles'].flatten()
            ])
            features.append(feat_vec)
        except Exception as e:
            logger.warning(f"Feature extraction failed: {e}")
            continue
    
    return np.array(features) if features else np.array([])

def normalize_features(features: np.ndarray) -> np.ndarray:
    """
    Normalize features to zero mean and unit variance.
    
    Args:
        features: Feature array to normalize
        
    Returns:
        Normalized feature array
    """
    if len(features) == 0:
        return features
    
    scaler = StandardScaler()
    return scaler.fit_transform(features)

def calculate_silhouette_score(X: np.ndarray, labels: np.ndarray) -> float:
    """
    Calculate silhouette score for clustering validation.
    
    Args:
        X: Feature matrix
        labels: Cluster assignments
        
    Returns:
        Silhouette score (or -1 if cannot be calculated)
    """
    if len(X) == 0 or len(labels) == 0:
        return -1.0
    
    unique_labels = len(set(labels))
    if unique_labels <= 1:
        return -1.0
    
    try:
        return silhouette_score(X, labels)
    except Exception as e:
        logger.warning(f"Silhouette score calculation failed: {e}")
        return -1.0

def run_kmeans_clustering(X: np.ndarray, k: int, random_state: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Run K-means clustering.
    
    Args:
        X: Feature matrix
        k: Number of clusters
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (cluster labels, cluster centers)
    """
    if k <= 0:
        raise ValueError("k must be positive")
    
    if len(X) < k:
        logger.warning(f"Sample size {len(X)} less than k={k}, reducing k")
        k = max(1, len(X))
    
    kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10, max_iter=300)
    labels = kmeans.fit_predict(X)
    centers = kmeans.cluster_centers_
    
    return labels, centers

def run_clustering_with_adaptive_k_reduction(
    X: np.ndarray,
    max_k: int = DEFAULT_MAX_K,
    min_silhouette: float = DEFAULT_MIN_SILHOUETTE,
    k_reduction_step: int = DEFAULT_K_REDUCTION_STEP,
    random_state: int = 42,
    log_path: Optional[str] = None
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Run K-means clustering with adaptive K-reduction logic.
    
    This implements FR-002a:
    1. Calculate silhouette score for current k
    2. If score < threshold AND k > 1, reduce k and repeat
    3. If k reaches 1 and score < threshold, log warning and proceed
    
    Args:
        X: Normalized feature matrix
        max_k: Maximum number of clusters to try
        min_silhouette: Minimum acceptable silhouette score
        k_reduction_step: Step size for k reduction
        random_state: Random seed
        log_path: Path to save clustering log
        
    Returns:
        Tuple of (labels, centers, metadata)
    """
    logger.info(f"Starting adaptive K-reduction with max_k={max_k}, min_silhouette={min_silhouette}")
    
    k = max_k
    iteration = 0
    metadata = {
        'initial_k': max_k,
        'final_k': max_k,
        'final_silhouette': -1.0,
        'iterations': 0,
        'degenerate': False,
        'method': 'kmeans',
        'history': []
    }
    
    # Ensure we don't loop infinitely
    while k >= 1 and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Iteration {iteration}: Trying k={k}")
        
        try:
            labels, centers = run_kmeans_clustering(X, k, random_state)
            
            # Calculate silhouette score
            score = calculate_silhouette_score(X, labels)
            metadata['history'].append({
                'k': k,
                'silhouette_score': float(score) if score >= 0 else None,
                'unique_clusters': len(set(labels))
            })
            
            logger.info(f"  k={k}, silhouette_score={score:.4f}")
            
            # Check if score meets threshold
            if score >= min_silhouette:
                metadata['final_k'] = k
                metadata['final_silhouette'] = float(score)
                metadata['iterations'] = iteration
                logger.info(f"Success: Found valid clustering at k={k} with score={score:.4f}")
                break
            
            # If k=1 and score < threshold, we're done (degenerate case)
            if k == 1:
                metadata['final_k'] = 1
                metadata['final_silhouette'] = float(score) if score >= 0 else -1.0
                metadata['degenerate'] = True
                metadata['iterations'] = iteration
                logger.warning("Degenerate clustering: k=1 with silhouette score below threshold")
                break
            
            # Reduce k and continue
            k = max(1, k - k_reduction_step)
            
        except Exception as e:
            logger.error(f"Clustering failed at k={k}: {e}")
            k = max(1, k - k_reduction_step)
    
    if iteration >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, using current k={k}")
    
    # Save log if path provided
    if log_path:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Clustering log saved to {log_path}")
    
    return labels, centers, metadata

def run_hac_fallback(
    X: np.ndarray,
    max_clusters: int = DEFAULT_MAX_K,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Run Hierarchical Agglomerative Clustering as fallback.
    
    Triggered only if K-means fails completely (k=1, score < threshold).
    
    Args:
        X: Feature matrix
        max_clusters: Maximum number of clusters
        random_state: Random seed
        
    Returns:
        Tuple of (labels, centers, metadata)
    """
    logger.info("Running HAC fallback clustering")
    
    # Determine optimal number of clusters using silhouette analysis
    best_k = 2
    best_score = -1
    all_scores = []
    
    for k in range(2, min(max_clusters, len(X) // 2)):
        try:
            agg = AgglomerativeClustering(n_clusters=k, linkage='ward')
            labels = agg.fit_predict(X)
            
            if len(set(labels)) > 1:
                score = silhouette_score(X, labels)
                all_scores.append((k, score))
                
                if score > best_score:
                    best_score = score
                    best_k = k
        except Exception as e:
            logger.warning(f"HAC failed for k={k}: {e}")
            continue
    
    # If no valid clustering found, use 2 clusters
    if best_score < 0:
        best_k = 2
        best_score = -1
        logger.warning("HAC fallback: No valid clustering found, using k=2")
    
    # Run final HAC
    agg = AgglomerativeClustering(n_clusters=best_k, linkage='ward')
    labels = agg.fit_predict(X)
    
    # Compute centers (mean of each cluster)
    centers = np.array([X[labels == i].mean(axis=0) for i in range(best_k)])
    
    metadata = {
        'method': 'hac',
        'final_k': best_k,
        'final_silhouette': float(best_score),
        'all_scores': [{'k': k, 'score': float(s)} for k, s in all_scores]
    }
    
    logger.info(f"HAC fallback complete: k={best_k}, silhouette={best_score:.4f}")
    
    return labels, centers, metadata

def save_clustering_artifacts(
    labels: np.ndarray,
    centers: np.ndarray,
    metadata: Dict[str, Any],
    output_dir: str = 'data/processed'
) -> Dict[str, str]:
    """
    Save clustering artifacts to disk.
    
    Args:
        labels: Cluster assignments
        centers: Cluster centers
        metadata: Clustering metadata
        output_dir: Output directory
        
    Returns:
        Dictionary of saved file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save cluster centers
    centers_path = os.path.join(output_dir, 'cluster_centers.json')
    with open(centers_path, 'w') as f:
        json.dump({
            'centers': centers.tolist(),
            'n_clusters': len(centers),
            'feature_dim': centers.shape[1] if len(centers) > 0 else 0
        }, f, indent=2)
    
    # Save assignments (will be combined with sample IDs later)
    assignments_path = os.path.join(output_dir, 'assignments.parquet')
    df_assignments = pd.DataFrame({
        'cluster_id': labels,
        'sample_index': range(len(labels))
    })
    df_assignments.to_parquet(assignments_path, index=False)
    
    # Save metadata
    metadata_path = os.path.join(output_dir, 'clusters.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Calculate checksums
    centers_checksum = compute_file_checksum(centers_path)
    assignments_checksum = compute_file_checksum(assignments_path)
    
    logger.info(f"Saved artifacts: {centers_path}, {assignments_path}, {metadata_path}")
    
    return {
        'centers': centers_path,
        'assignments': assignments_path,
        'metadata': metadata_path,
        'centers_checksum': centers_checksum,
        'assignments_checksum': assignments_checksum
    }

def verify_clustering_coverage(
    labels: np.ndarray,
    total_samples: int,
    threshold: float = COVERAGE_THRESHOLD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify clustering coverage meets threshold.
    
    Args:
        labels: Cluster assignments
        total_samples: Total number of samples
        threshold: Minimum coverage threshold
        
    Returns:
        Tuple of (success, report)
    """
    assigned = len(labels)
    coverage = assigned / total_samples if total_samples > 0 else 0.0
    
    report = {
        'total_samples': total_samples,
        'assigned_samples': assigned,
        'coverage': coverage,
        'threshold': threshold,
        'passed': coverage >= threshold
    }
    
    logger.info(f"Coverage: {coverage:.4f} ({assigned}/{total_samples}), threshold: {threshold}")
    
    if coverage < threshold:
        error_msg = f"Clustering coverage {coverage:.4f} < {threshold} (SC-005 violation). Aborting."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    return True, report

def run_ingestion_pipeline(
    dataset_id: str = "Qwen/Qwen-VLA",
    split: str = "train",
    max_samples: Optional[int] = None,
    output_dir: str = "data/processed",
    results_dir: str = "data/results",
    streaming: bool = True,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Run the complete ingestion and clustering pipeline.
    
    Args:
        dataset_id: HuggingFace dataset ID
        split: Dataset split to use
        max_samples: Maximum number of samples to process
        output_dir: Output directory for artifacts
        results_dir: Directory for result logs
        streaming: Use streaming mode for large datasets
        batch_size: Batch size for processing
        
    Returns:
        Pipeline execution report
    """
    start_time = time.time()
    set_global_seed(42)
    
    logger.info(f"Starting ingestion pipeline for {dataset_id}")
    logger.info(f"Streaming mode: {streaming}, max_samples: {max_samples}")
    
    # Load dataset
    try:
        if streaming:
            dataset = load_dataset(dataset_id, split=split, streaming=True)
            logger.info("Dataset loaded in streaming mode")
        else:
            dataset = load_dataset(dataset_id, split=split)
            logger.info("Dataset loaded in memory mode")
    except Exception as e:
        error_msg = f"Failed to load dataset: {e}. Aborting."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Process samples
    all_trajectories = []
    sample_count = 0
    
    logger.info("Processing samples...")
    for batch in stream_dataset_iterator(dataset, batch_size):
        if max_samples and sample_count >= max_samples:
            break
        
        for sample in batch:
            traj = process_sample(sample)
            if traj is not None:
                all_trajectories.append(traj)
                sample_count += 1
            
            # Memory check
            if sample_count % 1000 == 0:
                if not check_memory_usage():
                    logger.warning("Memory usage high, continuing but monitoring...")
        
        if max_samples and sample_count >= max_samples:
            break
    
    logger.info(f"Processed {sample_count} valid samples")
    
    if sample_count == 0:
        raise RuntimeError("No valid samples found in dataset")
    
    # Extract features
    logger.info("Extracting kinematic features...")
    features = extract_features_batch(all_trajectories)
    logger.info(f"Extracted {len(features)} feature vectors")
    
    if len(features) == 0:
        raise RuntimeError("Feature extraction failed")
    
    # Normalize features
    logger.info("Normalizing features...")
    X_norm = normalize_features(features)
    
    # Get clustering parameters
    config = get_clustering_params()
    max_k = config.get('max_clusters', DEFAULT_MAX_K)
    min_silhouette = config.get('min_silhouette_score', DEFAULT_MIN_SILHOUETTE)
    k_reduction_step = config.get('k_reduction_step_size', DEFAULT_K_REDUCTION_STEP)
    
    # Run clustering with adaptive K-reduction
    log_path = os.path.join(results_dir, 'clustering_method_log.json')
    os.makedirs(results_dir, exist_ok=True)
    
    labels, centers, metadata = run_clustering_with_adaptive_k_reduction(
        X_norm,
        max_k=max_k,
        min_silhouette=min_silhouette,
        k_reduction_step=k_reduction_step,
        log_path=log_path
    )
    
    # Check for degenerate clustering and apply HAC fallback if needed
    if metadata.get('degenerate', False) and metadata.get('final_k', 1) == 1:
        logger.warning("K-means failed, applying HAC fallback...")
        labels, centers, metadata = run_hac_fallback(
            X_norm,
            max_clusters=max_k
        )
        metadata['fallback_used'] = True
        # Update log
        with open(log_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    # Verify coverage
    verify_clustering_coverage(labels, sample_count)
    
    # Save artifacts
    artifacts = save_clustering_artifacts(labels, centers, metadata, output_dir)
    
    # Generate coverage report
    coverage_report = {
        'total_samples': sample_count,
        'assigned_samples': len(labels),
        'coverage': len(labels) / sample_count,
        'threshold': COVERAGE_THRESHOLD,
        'passed': len(labels) / sample_count >= COVERAGE_THRESHOLD
    }
    
    coverage_path = os.path.join(results_dir, 'coverage_report.json')
    with open(coverage_path, 'w') as f:
        json.dump(coverage_report, f, indent=2)
    
    elapsed_time = time.time() - start_time
    
    report = {
        'status': 'success',
        'samples_processed': sample_count,
        'features_extracted': len(features),
        'clusters_found': metadata['final_k'],
        'silhouette_score': metadata['final_silhouette'],
        'method': metadata['method'],
        'degenerate': metadata.get('degenerate', False),
        'hac_fallback': metadata.get('fallback_used', False),
        'coverage': coverage_report['coverage'],
        'elapsed_time_seconds': elapsed_time,
        'artifacts': artifacts
    }
    
    logger.info(f"Pipeline complete in {elapsed_time:.2f}s")
    logger.info(f"Clusters: {report['clusters_found']}, Score: {report['silhouette_score']:.4f}")
    
    return report

def main():
    """Main entry point for the clustering pipeline."""
    parser = argparse.ArgumentParser(description='Qwen-VLA Clustering Pipeline')
    parser.add_argument('--dataset', type=str, default='Qwen/Qwen-VLA', help='Dataset ID')
    parser.add_argument('--split', type=str, default='train', help='Dataset split')
    parser.add_argument('--max-samples', type=int, default=None, help='Max samples to process')
    parser.add_argument('--output-dir', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--results-dir', type=str, default='data/results', help='Results directory')
    parser.add_argument('--no-streaming', action='store_true', help='Disable streaming mode')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    
    args = parser.parse_args()
    
    try:
        report = run_ingestion_pipeline(
            dataset_id=args.dataset,
            split=args.split,
            max_samples=args.max_samples,
            output_dir=args.output_dir,
            results_dir=args.results_dir,
            streaming=not args.no_streaming,
            batch_size=args.batch_size
        )
        
        print(json.dumps(report, indent=2))
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(json.dumps({'status': 'failed', 'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
