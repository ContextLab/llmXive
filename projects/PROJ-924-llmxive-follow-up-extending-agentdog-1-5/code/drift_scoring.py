import os
import sys
import tracemalloc
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from config import get_path, ensure_directories, RANDOM_SEED, MAX_RAM_GB, BATCH_SIZE
from config import set_seed

def load_centroids(centroid_path: Optional[Path] = None) -> Dict[str, np.ndarray]:
    """
    Load taxonomy centroids from a JSON file.
    
    Args:
        centroid_path: Path to the centroids file. Defaults to configured path.
    
    Returns:
        Dictionary mapping category names to centroid embeddings.
    """
    if centroid_path is None:
        centroid_path = get_path("data", "processed", "taxonomy_centroids.json")
    
    with open(centroid_path, 'r', encoding='utf-8') as f:
        centroids = json.load(f)
    
    # Convert lists to numpy arrays
    return {k: np.array(v) for k, v in centroids.items()}

def compute_cosine_distance(embedding: np.ndarray, centroids: Dict[str, np.ndarray]) -> Tuple[float, str]:
    """
    Compute minimum cosine distance to any centroid.
    
    Args:
        embedding: Log embedding vector.
        centroids: Dictionary of category centroids.
    
    Returns:
        Tuple of (minimum_distance, closest_category).
    """
    min_distance = float('inf')
    closest_category = None
    
    for category, centroid in centroids.items():
        # Cosine distance = 1 - cosine_similarity
        cosine_sim = np.dot(embedding, centroid) / (np.linalg.norm(embedding) * np.linalg.norm(centroid))
        distance = 1 - cosine_sim
        
        if distance < min_distance:
            min_distance = distance
            closest_category = category
    
    return min_distance, closest_category

def batch_process_logs(logs: List[Dict[str, Any]], model: SentenceTransformer, centroids: Dict[str, np.ndarray], batch_size: int = BATCH_SIZE) -> List[Dict[str, Any]]:
    """
    Process logs in batches to stay within memory limits.
    
    Args:
        logs: List of log records.
        model: Sentence transformer model.
        centroids: Dictionary of centroids.
        batch_size: Number of logs to process at once.
    
    Returns:
        List of processed log records with drift scores.
    """
    results = []
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        for i in range(0, len(logs), batch_size):
            batch = logs[i:i + batch_size]
            texts = [log.get("text", "") for log in batch]
            
            # Encode batch
            embeddings = model.encode(texts)
            
            for log, embedding in zip(batch, embeddings):
                # Handle empty embeddings
                if np.linalg.norm(embedding) == 0:
                    drift_score = 2.0  # Maximum distance
                    review_flag = True
                    closest_category = "unknown"
                else:
                    drift_score, closest_category = compute_cosine_distance(embedding, centroids)
                    review_flag = drift_score > 0.5  # Threshold
                
                results.append({
                    "log_id": log.get("log_id"),
                    "drift_score": drift_score,
                    "review_flag": review_flag,
                    "closest_category": closest_category
                })
            
            # Check memory usage
            current, peak = tracemalloc.get_traced_memory()
            if peak > MAX_RAM_GB * 1024 * 1024 * 1024:
                raise MemoryError(f"Memory limit exceeded: {peak / (1024**3):.2f}GB")
    
    finally:
        tracemalloc.stop()
    
    return results

def handle_empty_logs(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Handle empty or whitespace-only logs.
    
    Args:
        logs: List of log records.
    
    Returns:
        List of processed log records with max drift score.
    """
    results = []
    for log in logs:
        text = log.get("text", "")
        if not text or text.strip() == "":
            results.append({
                "log_id": log.get("log_id"),
                "drift_score": 2.0,  # Maximum theoretical distance
                "review_flag": True,
                "closest_category": "unknown"
            })
    return results

def export_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Export results to a CSV file.
    
    Args:
        results: List of processed log records.
        output_path: Path to save the results.
    """
    ensure_directories([str(output_path.parent)])
    
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)

def main():
    """Main entry point for drift_scoring script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute drift scores for logs")
    parser.add_argument("--input", type=str, help="Input data file")
    parser.add_argument("--taxonomy", type=str, help="Taxonomy centroids file")
    parser.add_argument("--output", type=str, help="Output file for drift scores")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Sentence transformer model")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(RANDOM_SEED)
    
    # Load centroids
    print("Loading taxonomy centroids...")
    centroid_path = Path(args.taxonomy) if args.taxonomy else None
    centroids = load_centroids(centroid_path)
    
    # Load model
    print("Loading sentence transformer model...")
    model = SentenceTransformer(args.model)
    
    # Load logs
    input_path = Path(args.input) if args.input else None
    if input_path:
        if input_path.suffix == '.parquet':
            logs = pd.read_parquet(input_path).to_dict('records')
        else:
            logs = pd.read_csv(input_path).to_dict('records')
    else:
        # Default test data
        test_path = get_path("data", "test", "test_static_logs.json")
        with open(test_path, 'r') as f:
            logs = json.load(f)
    
    # Process logs
    print("Processing logs...")
    results = batch_process_logs(logs, model, centroids)
    
    # Export results
    output = Path(args.output) if args.output else get_path("data", "processed", "drift_scores.csv")
    export_results(results, output)
    
    print(f"Saved drift scores to {output}")

if __name__ == "__main__":
    main()
