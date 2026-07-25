import os
import sys
import tracemalloc
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from config import get_path, get_config, get_batch_size, get_max_memory_gb
from utils import save_csv_file, load_json_file, save_json_file
from data_loader import LoudFailureError

def load_centroids(centroid_path: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Load taxonomy centroids from the processed JSON file.
    Returns a dictionary mapping category names to their L2-normalized embedding vectors.
    """
    if centroid_path is None:
        centroid_path = str(get_path("data", "processed", "taxonomy_centroids.json"))
    
    if not os.path.exists(centroid_path):
        raise LoudFailureError(f"Centroid file not found: {centroid_path}")
    
    data = load_json_file(centroid_path)
    centroids = {}
    for category, embedding in data["centroids"].items():
        # Ensure L2 normalization
        vec = np.array(embedding)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        centroids[category] = vec
    
    return centroids

def compute_cosine_distance(embeddings: np.ndarray, centroids: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Compute the minimum cosine distance from each log embedding to any taxonomy centroid.
    Formula: 1 - cosine_similarity(L2_normalized_vectors)
    Returns an array of shape (n_logs,) containing the minimum distance for each log.
    """
    if embeddings.size == 0:
        return np.array([])
    
    # Ensure embeddings are L2 normalized
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    # Avoid division by zero for zero vectors (though they should be handled separately)
    norms = np.where(norms == 0, 1, norms)
    embeddings_normalized = embeddings / norms
    
    # Stack centroids into a matrix
    centroid_names = list(centroids.keys())
    centroid_matrix = np.array([centroids[name] for name in centroid_names])
    
    # Compute cosine similarity (all embeddings x all centroids)
    # cosine_similarity returns values in [-1, 1], where 1 is identical
    similarities = cosine_similarity(embeddings_normalized, centroid_matrix)
    
    # Minimum distance = 1 - maximum similarity
    # max_sim shape: (n_logs,)
    max_sim = np.max(similarities, axis=1)
    min_distances = 1.0 - max_sim
    
    return min_distances

def batch_process_logs(
    logs: List[Dict[str, Any]],
    centroids: Dict[str, np.ndarray],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Process a list of logs in batches to compute drift scores.
    Handles memory constraints by processing in batches and monitoring RAM usage.
    
    Args:
        logs: List of log dictionaries with 'log_id' and 'text' keys
        centroids: Dictionary of category centroids
        model_name: SentenceTransformer model name
        batch_size: Number of logs to process at once (defaults to config)
    
    Returns:
        List of dictionaries with log_id, drift_score, and review_flag
    """
    if batch_size is None:
        batch_size = get_batch_size()
    
    max_memory_gb = get_max_memory_gb()
    max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
    
    # Track memory
    tracemalloc.start()
    
    # Initialize model
    model = SentenceTransformer(model_name)
    
    results = []
    n_logs = len(logs)
    
    try:
        for i in range(0, n_logs, batch_size):
            batch = logs[i:i + batch_size]
            
            # Check memory before processing batch
            current, peak = tracemalloc.get_traced_memory()
            if peak > max_memory_bytes:
                raise LoudFailureError(
                    f"Memory limit exceeded: {peak / (1024**3):.2f}GB > {max_memory_gb}GB"
                )
            
            # Process batch
            texts = [log.get("text", "") for log in batch]
            log_ids = [log.get("log_id", f"unknown_{i}") for log in batch]
            
            # Handle empty/whitespace logs
            empty_mask = [not text or not text.strip() for text in texts]
            non_empty_texts = [text for text, is_empty in zip(texts, empty_mask) if not is_empty]
            non_empty_indices = [idx for idx, is_empty in enumerate(empty_mask) if not is_empty]
            
            batch_results = []
            
            if non_empty_texts:
                # Encode non-empty texts
                embeddings = model.encode(non_empty_texts, convert_to_numpy=True, show_progress_bar=False)
                distances = compute_cosine_distance(embeddings, centroids)
                
                for idx, dist in zip(non_empty_indices, distances):
                    batch_results.append({
                        "log_id": log_ids[idx],
                        "drift_score": float(dist),
                        "review_flag": False
                    })
            
            # Handle empty logs
            for idx, is_empty in enumerate(empty_mask):
                if is_empty:
                    batch_results.append({
                        "log_id": log_ids[idx],
                        "drift_score": 2.0,  # Maximum deviation for empty logs
                        "review_flag": True
                    })
            
            results.extend(batch_results)
            
    finally:
        tracemalloc.stop()
    
    return results

def export_results(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Export drift scoring results to a CSV file.
    
    Args:
        results: List of result dictionaries with log_id, drift_score, review_flag
        output_path: Path for output CSV (defaults to data/processed/drift_scores.csv)
    
    Returns:
        Path to the generated CSV file
    
    Raises:
        LoudFailureError: If output path is invalid or file cannot be written
    """
    if output_path is None:
        output_path = str(get_path("data", "processed", "drift_scores.csv"))
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Validate results
    if not results:
        raise LoudFailureError("No results to export")
    
    # Check required columns
    required_columns = {"log_id", "drift_score", "review_flag"}
    if not required_columns.issubset(set(results[0].keys())):
        raise LoudFailureError(
            f"Results missing required columns. Expected: {required_columns}, "
            f"Got: {set(results[0].keys())}"
        )
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure correct column order
    df = df[["log_id", "drift_score", "review_flag"]]
    
    # Verify data types
    df["log_id"] = df["log_id"].astype(str)
    df["drift_score"] = df["drift_score"].astype(float)
    df["review_flag"] = df["review_flag"].astype(bool)
    
    # Save to CSV
    try:
        df.to_csv(output_path, index=False)
    except Exception as e:
        raise LoudFailureError(f"Failed to write CSV file: {str(e)}")
    
    # Verify file was created and has content
    if not os.path.exists(output_path):
        raise LoudFailureError(f"Output file was not created: {output_path}")
    
    file_size = os.path.getsize(output_path)
    if file_size == 0:
        raise LoudFailureError(f"Output file is empty: {output_path}")
    
    # Verify columns in saved file
    saved_df = pd.read_csv(output_path)
    saved_columns = set(saved_df.columns)
    if not required_columns.issubset(saved_columns):
        raise LoudFailureError(
            f"Saved CSV missing required columns. Expected: {required_columns}, "
            f"Got: {saved_columns}"
        )
    
    return output_path

def main():
    """
    Main entry point for drift scoring pipeline.
    Loads centroids, processes logs, and exports results.
    """
    print("Starting drift scoring pipeline...")
    
    # Load centroids
    print("Loading taxonomy centroids...")
    centroids = load_centroids()
    print(f"Loaded {len(centroids)} centroids")
    
    # Load logs from test fixture (for demonstration)
    # In a real scenario, this would load from raw data
    logs_path = get_path("data", "test", "test_static_logs.json")
    if not os.path.exists(logs_path):
        # Try alternative path
        logs_path = get_path("data", "test", "real_ground_truth_fixture.json")
    
    if not os.path.exists(logs_path):
        raise LoudFailureError(f"Log file not found: {logs_path}")
    
    print(f"Loading logs from {logs_path}...")
    logs = load_json_file(logs_path)
    print(f"Loaded {len(logs)} logs")
    
    # Process logs
    print("Processing logs...")
    results = batch_process_logs(logs, centroids)
    print(f"Processed {len(results)} logs")
    
    # Export results
    print("Exporting results...")
    output_path = export_results(results)
    print(f"Results exported to {output_path}")
    
    # Summary
    df = pd.read_csv(output_path)
    print(f"\nSummary statistics:")
    print(f"  Total logs: {len(df)}")
    print(f"  Mean drift score: {df['drift_score'].mean():.4f}")
    print(f"  Std drift score: {df['drift_score'].std():.4f}")
    print(f"  Logs flagged for review: {df['review_flag'].sum()}")
    
    return output_path

if __name__ == "__main__":
    main()