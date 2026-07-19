import json
import os
import sys
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from config import get_path, get_max_memory_gb, get_centroid_model, set_seed
from utils import load_json_file, save_json_file

# Constants
DEFAULT_MAX_MEMORY_GB = 4.0
BATCH_SIZE = 32  # Small batch to fit memory constraints during embedding

def load_taxonomy(taxonomy_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the taxonomy definition from a JSON file.
    
    Args:
        taxonomy_path: Path to taxonomy.json. If None, uses config default.
        
    Returns:
        Dictionary containing taxonomy structure.
    """
    if taxonomy_path is None:
        taxonomy_path = str(get_path("taxonomy_file"))
    
    if not os.path.exists(taxonomy_path):
        raise FileNotFoundError(f"Taxonomy file not found at: {taxonomy_path}")
    
    return load_json_file(taxonomy_path)

def build_centroids(taxonomy: Dict[str, Any], model_name: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Build centroid embeddings for each category in the taxonomy.
    
    Uses `tracemalloc` to monitor peak memory usage and enforces a strict
    RAM limit. If the limit is exceeded, a MemoryError is raised.
    
    Args:
        taxonomy: The loaded taxonomy dictionary.
        model_name: Name of the sentence-transformer model. Uses config default if None.
        
    Returns:
        Dictionary mapping category names to their centroid embeddings (numpy arrays).
        
    Raises:
        MemoryError: If peak memory usage exceeds the configured limit.
    """
    set_seed(42)
    if model_name is None:
        model_name = get_centroid_model()
    
    max_memory_gb = get_max_memory_gb()
    if max_memory_gb is None:
        max_memory_gb = DEFAULT_MAX_MEMORY_GB
    
    max_memory_bytes = max_memory_gb * (1024 ** 3)
    
    print(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)
    
    centroids = {}
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        # Iterate through taxonomy categories
        # Assuming taxonomy structure: {"categories": [{"name": "...", "examples": [...]}]}
        categories = taxonomy.get("categories", [])
        
        if not categories:
            print("Warning: No categories found in taxonomy.")
            return centroids
        
        for cat in categories:
            cat_name = cat.get("name")
            examples = cat.get("examples", [])
            
            if not cat_name or not examples:
                continue
            
            # Filter out empty examples
            valid_examples = [ex for ex in examples if ex and ex.strip()]
            
            if not valid_examples:
                print(f"Warning: No valid examples for category '{cat_name}'. Skipping.")
                continue
            
            # Process examples in batches to manage memory
            all_embeddings = []
            
            for i in range(0, len(valid_examples), BATCH_SIZE):
                batch = valid_examples[i : i + BATCH_SIZE]
                
                # Check memory before processing batch
                current, peak = tracemalloc.get_traced_memory()
                if peak > max_memory_bytes:
                    raise MemoryError(
                        f"Peak memory usage ({peak / (1024**3):.2f} GB) exceeded limit ({max_memory_gb} GB). "
                        f"Cannot process category '{cat_name}'."
                    )
                
                batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
                all_embeddings.append(batch_embeddings)
                
                # Force garbage collection of batch to free memory
                del batch_embeddings
            
            if all_embeddings:
                # Concatenate all batch embeddings
                combined_embeddings = np.vstack(all_embeddings)
                
                # Compute centroid (mean embedding)
                centroid = np.mean(combined_embeddings, axis=0)
                centroids[cat_name] = centroid
                
                print(f"Built centroid for '{cat_name}' (n={len(valid_examples)})")
            
            # Clear memory after each category
            del all_embeddings
            del combined_embeddings
            if 'centroid' in locals():
                del centroid
        
        # Final memory check
        current, peak = tracemalloc.get_traced_memory()
        print(f"Peak memory usage during centroid building: {peak / (1024**3):.2f} GB (Limit: {max_memory_gb} GB)")
        
        if peak > max_memory_bytes:
            raise MemoryError(
                f"Peak memory usage ({peak / (1024**3):.2f} GB) exceeded limit ({max_memory_gb} GB)."
            )
        
    finally:
        # Stop memory tracking
        tracemalloc.stop()
        
        # Clear model from memory if possible
        del model
        import gc
        gc.collect()
    
    return centroids

def main():
    """
    Main entry point for building the taxonomy centroids.
    
    Loads the taxonomy, builds centroids with memory monitoring, and saves
    the resulting centroids to a JSON file.
    """
    print("Starting taxonomy centroid builder...")
    
    # Load taxonomy
    try:
        taxonomy = load_taxonomy()
    except FileNotFoundError as e:
        print(f"Error loading taxonomy: {e}")
        sys.exit(1)
    
    # Build centroids with memory monitoring
    try:
        centroids = build_centroids(taxonomy)
    except MemoryError as e:
        print(f"Memory limit exceeded: {e}")
        sys.exit(1)
    
    if not centroids:
        print("Warning: No centroids were built.")
        sys.exit(0)
    
    # Save centroids to JSON
    output_path = get_path("centroids_file")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    centroids_serializable = {k: v.tolist() for k, v in centroids.items()}
    save_json_file(output_path, centroids_serializable)
    
    print(f"Centroids saved to: {output_path}")
    print(f"Total categories processed: {len(centroids)}")

if __name__ == "__main__":
    main()