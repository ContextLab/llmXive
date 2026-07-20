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

import numpy as np
from sentence_transformers import SentenceTransformer
from config import get_path, get_max_memory_gb, get_centroid_model
from utils import save_json_file, load_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_MEMORY_GB = 7.0
RAM_LIMIT_BYTES = MAX_MEMORY_GB * (1024 ** 3)

def load_taxonomy(taxonomy_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the AgentDoG taxonomy from a JSON file.
    
    Args:
        taxonomy_path: Path to the taxonomy JSON file. If None, uses the default path.
        
    Returns:
        List of taxonomy entries with 'category', 'description', etc.
    """
    if taxonomy_path is None:
        taxonomy_path = get_path("data/raw/taxonomy_agentdog.json")
    
    path_obj = Path(taxonomy_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")
    
    return load_json_file(path_obj)

def build_centroids(taxonomy: List[Dict[str, Any]], model_name: Optional[str] = None) -> Dict[str, np.ndarray]:
    """
    Build centroid embeddings for each category in the taxonomy.
    
    This function uses tracemalloc to monitor memory usage and enforces a strict
    peak RAM limit of < 7GB. If the limit is exceeded, it raises a MemoryError.
    
    Args:
        taxonomy: List of taxonomy entries.
        model_name: Name of the sentence-transformer model to use. Defaults to config.
        
    Returns:
        Dictionary mapping category names to their centroid embeddings (numpy arrays).
        
    Raises:
        MemoryError: If peak memory usage exceeds the configured limit.
        ValueError: If taxonomy is empty or invalid.
    """
    if not taxonomy:
        raise ValueError("Taxonomy list is empty. Cannot build centroids.")
    
    if model_name is None:
        model_name = get_centroid_model()
    
    # Start memory tracking
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
        # Load the model
        model = SentenceTransformer(model_name)
        
        # Group texts by category
        category_texts: Dict[str, List[str]] = {}
        for entry in taxonomy:
            category = entry.get("category")
            description = entry.get("description", "")
            
            if not category:
                continue
            
            if category not in category_texts:
                category_texts[category] = []
            
            # Use description as the text for embedding
            if description:
                category_texts[category].append(description)
            
            # Optionally include category name itself
            category_texts[category].append(category)
        
        if not category_texts:
            raise ValueError("No valid categories found in taxonomy.")
        
        centroids = {}
        
        for category, texts in category_texts.items():
            # Check memory before processing each category
            current, peak = tracemalloc.get_traced_memory()
            if peak > RAM_LIMIT_BYTES:
                raise MemoryError(
                    f"Peak memory usage ({peak / (1024**3):.2f}GB) exceeded limit ({MAX_MEMORY_GB}GB) "
                    f"while processing category '{category}'"
                )
            
            # Encode texts for this category
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            
            # Compute centroid (mean of embeddings)
            centroid = np.mean(embeddings, axis=0)
            centroids[category] = centroid
            
            # Optional: Clear embeddings to free memory
            del embeddings
        
        # Final memory check
        current, peak = tracemalloc.get_traced_memory()
        if peak > RAM_LIMIT_BYTES:
            raise MemoryError(
                f"Peak memory usage ({peak / (1024**3):.2f}GB) exceeded limit ({MAX_MEMORY_GB}GB) "
                f"during centroid generation"
            )
        
        return centroids
        
    finally:
        # Stop memory tracking
        tracemalloc.stop()

def save_centroids(centroids: Dict[str, np.ndarray], output_path: Optional[str] = None) -> str:
    """
    Save centroids to a JSON file.
    
    Args:
        centroids: Dictionary mapping category names to centroid embeddings.
        output_path: Path to save the centroids. If None, uses default path.
        
    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_path("data/processed/taxonomy_centroids.json")
    
    # Convert numpy arrays to lists for JSON serialization
    centroids_serializable = {
        category: embedding.tolist() 
        for category, embedding in centroids.items()
    }
    
    # Add metadata
    output_data = {
        "metadata": {
            "num_categories": len(centroids),
            "embedding_dimension": len(next(iter(centroids.values()))) if centroids else 0,
            "model_used": get_centroid_model()
        },
        "centroids": centroids_serializable
    }
    
    save_json_file(output_data, output_path)
    return output_path

def main():
    """
    Main entry point for building taxonomy centroids with memory monitoring.
    """
    print("Starting taxonomy centroid generation with memory monitoring...")
    print(f"Memory limit: {MAX_MEMORY_GB}GB")
    
    try:
        # Load taxonomy
        taxonomy = load_taxonomy()
        print(f"Loaded {len(taxonomy)} taxonomy entries")
        
        # Build centroids with memory monitoring
        centroids = build_centroids(taxonomy)
        print(f"Generated centroids for {len(centroids)} categories")
        
        # Save centroids
        output_path = save_centroids(centroids)
        print(f"Centroids saved to: {output_path}")
        
        # Final memory stats
        current, peak = tracemalloc.get_traced_memory()
        print(f"Final memory usage: current={current / 1024**2:.2f}MB, peak={peak / 1024**2:.2f}MB")
        
    except MemoryError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print("Centroid generation completed successfully.")

if __name__ == "__main__":
    main()