import os
import sys
import tracemalloc
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

from config import get_path, get_batch_size, get_max_memory_gb, get_centroid_model, ensure_directories
from utils import load_json_file, save_csv_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Maximum theoretical cosine distance is 2.0 (angle 180 degrees)
MAX_COSINE_DISTANCE = 2.0

def load_centroids() -> Dict[str, np.ndarray]:
    """
    Load taxonomy centroids from the processed JSON file.
    Returns a dictionary mapping category names to embedding arrays.
    """
    centroids_path = get_path('data/processed/taxonomy_centroids.json')
    if not os.path.exists(centroids_path):
        raise FileNotFoundError(f"Centroids file not found at {centroids_path}. Run taxonomy_builder first.")
    
    logger.info(f"Loading centroids from {centroids_path}")
    data = load_json_file(centroids_path)
    
    centroids = {}
    for category, embedding_list in data.items():
        centroids[category] = np.array(embedding_list, dtype=np.float32)
    
    logger.info(f"Loaded {len(centroids)} centroids")
    return centroids

def compute_cosine_distance(log_text: str, centroids: Dict[str, np.ndarray], model: SentenceTransformer) -> float:
    """
    Calculate the minimum cosine distance between a log text and all taxonomy centroids.
    
    Args:
        log_text: The log content to evaluate.
        centroids: Dictionary of category -> embedding vector.
        model: The SentenceTransformer model instance.
    
    Returns:
        The minimum cosine distance (float). Returns MAX_COSINE_DISTANCE if input is empty.
    """
    # Edge case: Handle empty or whitespace-only logs
    if not log_text or not log_text.strip():
        logger.debug("Empty or whitespace log detected. Assigning max drift score.")
        return MAX_COSINE_DISTANCE

    try:
        log_embedding = model.encode([log_text], convert_to_numpy=True, show_progress_bar=False)[0]
    except Exception as e:
        logger.error(f"Failed to encode log text: {e}")
        raise

    min_distance = float('inf')
    
    for category, centroid in centroids.items():
        # Ensure both are numpy arrays of same dtype for calculation
        vec1 = log_embedding.astype(np.float64)
        vec2 = centroid.astype(np.float64)
        
        # Normalize
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            continue
            
        vec1_norm = vec1 / norm1
        vec2_norm = vec2 / norm2
        
        # Cosine similarity
        sim = np.dot(vec1_norm, vec2_norm)
        # Clip to avoid numerical errors > 1.0 or < -1.0
        sim = np.clip(sim, -1.0, 1.0)
        
        # Cosine distance = 1 - similarity
        distance = 1.0 - sim
        
        if distance < min_distance:
            min_distance = distance
    
    if min_distance == float('inf'):
        # Fallback if no valid centroids were found or all were zero vectors
        logger.warning("No valid centroids found. Returning max distance.")
        return MAX_COSINE_DISTANCE
        
    return float(min_distance)

def batch_process_logs(logs: List[Dict[str, Any]], centroids: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
    """
    Process a batch of logs to compute drift scores.
    Handles empty logs explicitly and respects memory constraints via config.
    
    Args:
        logs: List of dicts containing 'log_id' and 'text'.
        centroids: Dictionary of centroids.
    
    Returns:
        List of dicts with 'log_id', 'drift_score', and 'review_flag'.
    """
    if not logs:
        logger.warning("No logs provided for batch processing.")
        return []

    model_name = get_centroid_model()
    logger.info(f"Initializing model: {model_name}")
    model = SentenceTransformer(model_name)
    
    results = []
    batch_size = get_batch_size()
    max_mem_gb = get_max_memory_gb()
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        for i in range(0, len(logs), batch_size):
            batch = logs[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} logs)")
            
            # Check memory usage periodically
            current, peak = tracemalloc.get_traced_memory()
            peak_gb = peak / (1024**3)
            if peak_gb > max_mem_gb * 0.9:
                logger.warning(f"Memory usage high: {peak_gb:.2f}GB / {max_mem_gb}GB limit. Proceeding with caution.")
            
            for log_entry in batch:
                log_id = log_entry.get('log_id', f'unknown_{i}')
                text = log_entry.get('text', '')
                
                # Compute score (handles empty internally)
                score = compute_cosine_distance(text, centroids, model)
                
                # Determine review flag
                # If score is MAX_COSINE_DISTANCE (2.0), it implies empty/whitespace
                # or potentially a complete outlier. Per spec: empty logs get review_flag='true'.
                review_flag = 'true' if score == MAX_COSINE_DISTANCE else 'false'
                
                results.append({
                    'log_id': log_id,
                    'drift_score': score,
                    'review_flag': review_flag
                })
                
    finally:
        tracemalloc.stop()
        
    logger.info(f"Batch processing complete. Processed {len(results)} logs.")
    return results

def export_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Export drift scoring results to a CSV file.
    
    Args:
        results: List of result dicts.
        output_path: Optional path override. Defaults to config.
    
    Returns:
        The path to the created file.
    """
    if not output_path:
        output_path = get_path('data/processed/drift_scores.csv')
    
    ensure_directories(output_path)
    
    logger.info(f"Exporting {len(results)} results to {output_path}")
    
    # Convert to DataFrame and save
    if results:
        df = pd.DataFrame(results)
        # Ensure column order matches spec
        df = df[['log_id', 'drift_score', 'review_flag']]
        save_csv_file(df, output_path)
    else:
        # Create empty file with headers
        pd.DataFrame(columns=['log_id', 'drift_score', 'review_flag']).to_csv(output_path, index=False)
        
    logger.info(f"Export complete: {output_path}")
    return output_path

def main():
    """
    Main entry point for running the drift scoring pipeline.
    """
    logger.info("Starting Drift Scoring Pipeline")
    
    # 1. Load Centroids
    try:
        centroids = load_centroids()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Load Input Data (Assuming a generic input path or command line arg, 
    #    but for now we assume the existence of a processed logs file or 
    #    we iterate over a standard location if defined in config.
    #    Since tasks.md implies running on logs, we look for a standard input 
    #    or require one to be passed. For this specific task T014 implementation,
    #    we focus on the logic. We will assume a standard input file location
    #    defined in config or a default fallback for the pipeline run.)
    
    input_path = get_path('data/processed/merged_logs.json') # Hypothetical standard input
    if not os.path.exists(input_path):
        # Fallback for testing if the specific merged file doesn't exist yet
        # In a real pipeline, this would likely be the output of data_loader or a previous step
        logger.warning(f"Standard input {input_path} not found. Checking for raw logs...")
        # We might need to fetch or locate the actual logs. 
        # For this task, we assume the caller provides the logs or they are at a known location.
        # If no logs are found, we exit gracefully or error.
        logger.error("No input logs found to process. Please ensure data is available.")
        sys.exit(1)

    logger.info(f"Loading logs from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    
    if not isinstance(logs, list):
        logger.error("Input logs must be a list of log entries.")
        sys.exit(1)

    # 3. Process
    results = batch_process_logs(logs, centroids)
    
    # 4. Export
    output_file = export_results(results)
    
    logger.info(f"Pipeline finished. Results saved to {output_file}")

if __name__ == '__main__':
    main()
