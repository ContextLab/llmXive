import os
import sys
import tracemalloc
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from config import get_path, ensure_directories, get_max_memory_gb, get_batch_size
from utils import load_json_file, save_csv_file

# Constants
MAX_MEMORY_GB = get_max_memory_gb()
MAX_MEMORY_BYTES = MAX_MEMORY_GB * (1024 ** 3)
BATCH_SIZE = get_batch_size()
CENTROID_MODEL_NAME = "all-MiniLM-L6-v2"

def load_centroids(centroid_path: Optional[str] = None) -> np.ndarray:
    """
    Load pre-computed centroid embeddings from a JSON file.
    
    Args:
        centroid_path: Path to the centroids JSON file. If None, uses default config path.
        
    Returns:
        np.ndarray: Array of centroid embeddings (shape: n_centroids x embedding_dim).
        
    Raises:
        FileNotFoundError: If the centroid file does not exist.
        ValueError: If the file format is invalid.
    """
    if centroid_path is None:
        centroid_path = get_path("centroids_file")
    
    path_obj = Path(centroid_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Centroid file not found at {centroid_path}")
    
    data = load_json_file(path_obj)
    
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Centroid file {centroid_path} must contain a non-empty list of centroids.")
    
    # Extract embeddings (assuming structure: [{"category": "...", "embedding": [...]}, ...])
    embeddings = [item["embedding"] for item in data]
    
    if not embeddings:
        raise ValueError("No embeddings found in the centroid file.")
        
    return np.array(embeddings, dtype=np.float32)

def compute_cosine_distance(
    log_embeddings: np.ndarray, 
    centroids: np.ndarray
) -> np.ndarray:
    """
    Calculate the minimum cosine distance from each log embedding to any centroid.
    
    Cosine distance = 1 - cosine_similarity.
    The minimum distance indicates how close the log is to the nearest known category.
    
    Args:
        log_embeddings: Array of log embeddings (shape: n_logs x embedding_dim).
        centroids: Array of centroid embeddings (shape: n_centroids x embedding_dim).
        
    Returns:
        np.ndarray: Array of minimum cosine distances (shape: n_logs,).
    """
    if log_embeddings.shape[0] == 0:
        return np.array([], dtype=np.float32)

    # Normalize vectors for cosine similarity
    log_norm = np.linalg.norm(log_embeddings, axis=1, keepdims=True)
    # Avoid division by zero
    log_norm[log_norm == 0] = 1e-9
    log_normalized = log_embeddings / log_norm

    cent_norm = np.linalg.norm(centroids, axis=1, keepdims=True)
    cent_norm[cent_norm == 0] = 1e-9
    centroids_normalized = centroids / cent_norm

    # Cosine similarity matrix: (n_logs, n_centroids)
    similarity = np.dot(log_normalized, centroids_normalized.T)
    
    # Cosine distance = 1 - similarity
    distance = 1.0 - similarity
    
    # Minimum distance to any centroid
    min_distances = np.min(distance, axis=1)
    
    return min_distances

def _embed_logs_batched(
    texts: List[str], 
    model: SentenceTransformer
) -> np.ndarray:
    """
    Embed a list of texts using the model, processing in batches to manage memory.
    
    Args:
        texts: List of log texts.
        model: The SentenceTransformer model instance.
        
    Returns:
        np.ndarray: Array of embeddings (shape: n_logs x embedding_dim).
    """
    if not texts:
        return np.array([])
        
    embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i : i + BATCH_SIZE]
        batch_embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
        embeddings.append(batch_embeddings)
        
        # Check memory usage periodically
        current_mem = tracemalloc.get_traced_memory()[1]
        if current_mem > MAX_MEMORY_BYTES:
            raise MemoryError(
                f"Memory limit exceeded: {current_mem / (1024**3):.2f}GB > {MAX_MEMORY_GB}GB"
            )
            
    return np.vstack(embeddings)

def batch_process_logs(
    logs: List[Dict[str, Any]], 
    centroids: np.ndarray
) -> List[Dict[str, Any]]:
    """
    Process a batch of logs to compute drift scores.
    
    Args:
        logs: List of log dictionaries, each containing 'log_id' and 'text'.
        centroids: Pre-loaded centroid embeddings.
        
    Returns:
        List[Dict[str, Any]]: List of results with 'log_id', 'drift_score', and 'review_flag'.
    """
    if not logs:
        return []

    # Start memory tracing
    tracemalloc.start()
    
    try:
        model = SentenceTransformer(CENTROID_MODEL_NAME, device="cpu")
        
        # Filter and process logs
        processed_logs = []
        texts_to_embed = []
        valid_indices = []
        
        for idx, log in enumerate(logs):
            text = log.get("text", "")
            if not text or not text.strip():
                # Handle empty logs per T014
                processed_logs.append({
                    "log_id": log.get("log_id", f"unknown_{idx}"),
                    "drift_score": 2.0, # Max theoretical distance
                    "review_flag": True
                })
            else:
                texts_to_embed.append(text)
                valid_indices.append(idx)
                processed_logs.append(None) # Placeholder for valid logs
        
        if texts_to_embed:
            log_embeddings = _embed_logs_batched(texts_to_embed, model)
            distances = compute_cosine_distance(log_embeddings, centroids)
            
            # Assign results back
            for i, (idx, dist) in enumerate(zip(valid_indices, distances)):
                # Threshold for review flag (e.g., > 0.5 indicates potential drift)
                # Using a heuristic threshold; can be made configurable
                review_flag = dist > 0.5 
                processed_logs[idx] = {
                    "log_id": logs[idx].get("log_id", f"unknown_{idx}"),
                    "drift_score": float(dist),
                    "review_flag": review_flag
                }
                
        return processed_logs
        
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"[Memory] Peak: {peak / (1024**3):.2f}GB")

def export_results(
    results: List[Dict[str, Any]], 
    output_path: Optional[str] = None
) -> str:
    """
    Export drift scoring results to a CSV file.
    
    Args:
        results: List of result dictionaries containing 'log_id', 'drift_score', 'review_flag'.
        output_path: Path to the output CSV. If None, uses default config path.
        
    Returns:
        str: The path to the generated CSV file.
        
    Raises:
        ValueError: If results are empty or missing required fields.
        IOError: If the file cannot be written.
    """
    if output_path is None:
        output_path = get_path("drift_scores_output")
        
    # Ensure directory exists
    ensure_directories()
    
    if not results:
        raise ValueError("Cannot export empty results list.")
    
    # Validate fields
    required_fields = {"log_id", "drift_score", "review_flag"}
    if not all(required_fields.issubset(set(r.keys())) for r in results):
        missing = required_fields - set(results[0].keys())
        raise ValueError(f"Results missing required fields: {missing}")
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Ensure column order
    df = df[["log_id", "drift_score", "review_flag"]]
    
    # Write to CSV
    save_csv_file(df, output_path)
    
    # Verify file generation
    if not os.path.exists(output_path):
        raise IOError(f"Failed to generate output file at {output_path}")
        
    # Verify columns
    df_check = pd.read_csv(output_path)
    if not set(df_check.columns).issuperset(required_fields):
        raise ValueError(f"Output CSV missing columns. Expected: {required_fields}, Got: {set(df_check.columns)}")
        
    return output_path

def main():
    """
    Main entry point for drift scoring and export.
    Loads centroids, processes logs (from a pre-existing source or passed in),
    and exports results.
    """
    print("Starting Drift Scoring Pipeline...")
    
    # 1. Load Centroids
    try:
        centroids = load_centroids()
        print(f"Loaded {centroids.shape[0]} centroids.")
    except Exception as e:
        print(f"Error loading centroids: {e}")
        sys.exit(1)
    
    # 2. Load Logs (Placeholder for actual data loading logic)
    # In a real pipeline, this would come from T005a/T005c or similar
    # For this task implementation, we assume logs are available in memory or 
    # a standard location. We'll simulate a load from a test file if it exists,
    # or just print that processing is ready.
    # Note: T017 specifically asks for export_results implementation.
    # We assume the caller (e.g., main.py) provides the 'logs' list.
    
    # For demonstration of the export function, we'll create a dummy result set
    # if no real logs are provided in this specific context, 
    # BUT the function export_results itself is fully implemented to handle real data.
    # The actual pipeline flow is: load -> process -> export.
    
    # Since T017 is about implementing export_results, we ensure it works.
    # We will not generate fake data here to avoid violating "Real data only" 
    # unless a real input file is detected.
    
    # Check for a standard processed input file if available (e.g. from T005c)
    input_logs_path = get_path("test_static_logs")
    logs = []
    
    if os.path.exists(input_logs_path):
        print(f"Loading logs from {input_logs_path}...")
        logs = load_json_file(input_logs_path)
        if not logs:
            print("Warning: Log file is empty.")
    else:
        print(f"Warning: No input logs found at {input_logs_path}. Skipping processing.")
    
    if logs:
        print(f"Processing {len(logs)} logs...")
        results = batch_process_logs(logs, centroids)
        
        if results:
            print(f"Exporting results to {get_path('drift_scores_output')}...")
            try:
                output_file = export_results(results)
                print(f"Successfully exported to {output_file}")
                print(f"Sample output:\n{pd.read_csv(output_file).head()}")
            except Exception as e:
                print(f"Error exporting results: {e}")
                sys.exit(1)
        else:
            print("No results to export.")
    else:
        print("No logs to process. Ensure T005c (test_static_logs) or data loader is run first.")

if __name__ == "__main__":
    main()
