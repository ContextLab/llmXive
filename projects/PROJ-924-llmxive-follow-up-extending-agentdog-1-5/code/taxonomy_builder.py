"""
Taxonomy Builder Module

Generates centroid embeddings for the AgentDoG taxonomy using Sentence Transformers.
Includes runtime memory profiling using tracemalloc for observability.
"""
import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Local imports matching API surface
from config import get_path, get_centroid_model
from utils import load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
MAX_BATCH_SIZE = 32  # Batch size to fit <100MB RAM constraint
MEMORY_LOG_PATH = "data/processed/taxonomy_memory_profile.json"

def load_taxonomy(path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load taxonomy definitions from a JSON file.

    Args:
        path: Optional path to the taxonomy file. Defaults to config path.

    Returns:
        List of taxonomy entries containing 'category' and 'description'.
    """
    if path is None:
        path = get_path("raw_taxonomy_definitions.json")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Taxonomy file not found at: {path}")
    
    logger.info(f"Loading taxonomy from {path}")
    return load_json_file(path)

def build_centroids(taxonomy: List[Dict[str, Any]], model_name: str = MODEL_NAME) -> Dict[str, Any]:
    """
    Build centroid embeddings for taxonomy categories.

    Uses 'all-MiniLM-L6-v2' on CPU with batched processing to respect memory limits.
    Includes runtime memory profiling via tracemalloc.

    Args:
        taxonomy: List of taxonomy entries.
        model_name: Name of the sentence-transformers model to use.

    Returns:
        Dictionary containing category names and their centroid embeddings.
    """
    logger.info(f"Initializing model: {model_name}")
    
    # Start memory profiling
    tracemalloc.start()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    start_mem_mb = current_mem / 1024 / 1024
    
    profile_data = {
        "start_memory_mb": start_mem_mb,
        "peak_memory_mb": 0.0,
        "end_memory_mb": 0.0,
        "processing_steps": []
    }

    try:
        from sentence_transformers import SentenceTransformer
        
        # Load model on CPU
        model = SentenceTransformer(model_name, device="cpu")
        
        # Prepare texts for embedding
        texts = []
        category_map = {}
        
        for idx, entry in enumerate(taxonomy):
            # Combine category and description for better embedding context
            text = f"{entry.get('category', '')}: {entry.get('description', '')}".strip()
            texts.append(text)
            category_map[idx] = entry.get('category', f"category_{idx}")
        
        logger.info(f"Processing {len(texts)} taxonomy entries...")
        
        # Process in batches to respect memory limits
        centroids = []
        batch_results = []
        
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch_texts = texts[i:i + MAX_BATCH_SIZE]
            batch_idx = i // MAX_BATCH_SIZE
            
            # Log memory before batch
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            current_mb = current_mem / 1024 / 1024
            peak_mb = peak_mem / 1024 / 1024
            
            profile_data["processing_steps"].append({
                "batch_index": batch_idx,
                "start_idx": i,
                "end_idx": min(i + MAX_BATCH_SIZE, len(texts)),
                "memory_mb": round(current_mb, 2),
                "peak_memory_mb": round(peak_mb, 2)
            })
            
            # Generate embeddings for the batch
            logger.info(f"Processing batch {batch_idx}: {len(batch_texts)} items")
            batch_embeddings = model.encode(batch_texts, convert_to_numpy=True, show_progress_bar=False)
            
            centroids.append(batch_embeddings)
            batch_results.append({
                "batch": batch_idx,
                "count": len(batch_embeddings)
            })
        
        # Concatenate all batches
        import numpy as np
        all_centroids = np.vstack(centroids)
        
        # Final memory check
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        end_mem_mb = current_mem / 1024 / 1024
        final_peak_mb = peak_mem / 1024 / 1024
        
        profile_data["end_memory_mb"] = round(end_mem_mb, 2)
        profile_data["peak_memory_mb"] = round(final_peak_mb, 2)
        
        logger.info(f"Centroid generation complete. Peak memory: {final_peak_mb:.2f} MB")
        
        # Stop memory profiling
        tracemalloc.stop()
        
        # Build result dictionary
        result = {
            "model": model_name,
            "categories": {},
            "metadata": {
                "total_categories": len(category_map),
                "embedding_dimension": all_centroids.shape[1],
                "memory_profile": profile_data
            }
        }
        
        # Map centroids to categories
        for idx, category_name in category_map.items():
            result["categories"][category_name] = all_centroids[idx].tolist()
        
        return result

    except Exception as e:
        # Stop profiling on error
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        profile_data["error"] = str(e)
        profile_data["peak_memory_mb"] = round(peak_mem / 1024 / 1024, 2)
        tracemalloc.stop()
        
        logger.error(f"Error building centroids: {e}")
        raise e

def main():
    """
    Main entry point for taxonomy centroid generation.
    
    Reads taxonomy from data/raw/taxonomy_definitions.json
    Outputs centroids to data/processed/taxonomy_centroids.json
    Outputs memory profile to data/processed/taxonomy_memory_profile.json
    """
    logger.info("Starting taxonomy centroid generation...")
    
    # Ensure output directories exist
    from config import ensure_directories
    ensure_directories()
    
    # Load taxonomy
    taxonomy_path = get_path("raw_taxonomy_definitions.json")
    taxonomy = load_taxonomy(taxonomy_path)
    
    if not taxonomy:
        logger.error("Taxonomy is empty. Cannot build centroids.")
        sys.exit(1)
    
    # Build centroids
    centroids_data = build_centroids(taxonomy)
    
    # Save centroids
    output_path = get_path("taxonomy_centroids.json", base_dir="processed")
    save_json_file(centroids_data, output_path)
    logger.info(f"Centroids saved to {output_path}")
    
    # Save memory profile separately for easier analysis
    memory_profile_path = get_path(MEMORY_LOG_PATH, base_dir="processed")
    save_json_file(centroids_data["metadata"]["memory_profile"], memory_profile_path)
    logger.info(f"Memory profile saved to {memory_profile_path}")
    
    print(f"SUCCESS: Generated {centroids_data['metadata']['total_categories']} centroids.")
    print(f"Peak RAM usage: {centroids_data['metadata']['memory_profile']['peak_memory_mb']:.2f} MB")

if __name__ == "__main__":
    main()