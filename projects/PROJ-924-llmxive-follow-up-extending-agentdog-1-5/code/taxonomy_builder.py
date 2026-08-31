import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
from sentence_transformers import SentenceTransformer
from config import get_path, ensure_directories, RANDOM_SEED, MAX_RAM_GB
from config import set_seed

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the limit."""
    pass

class TaxonomyLoadError(Exception):
    """Raised when taxonomy loading fails."""
    pass

def load_taxonomy(source: str = "local") -> Dict[str, Any]:
    """
    Load taxonomy definition.
    
    Args:
        source: Source of taxonomy ('local' or 'paper').
    
    Returns:
        Dictionary containing taxonomy definition.
    
    Raises:
        TaxonomyLoadError: If taxonomy cannot be loaded.
    """
    taxonomy_path = get_path("processed") / "taxonomy_agentdog.json"
    
    if not taxonomy_path.exists():
        raise TaxonomyLoadError(f"Taxonomy file not found at {taxonomy_path}.")
    
    try:
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise TaxonomyLoadError(f"Failed to load taxonomy: {e}")

def build_centroids(taxonomy: Dict[str, Any], model_name: str = "all-MiniLM-L6-v2") -> Dict[str, List[float]]:
    """
    Build centroid embeddings for taxonomy categories.
    
    Args:
        taxonomy: Taxonomy definition dictionary.
        model_name: Name of the sentence transformer model.
    
    Returns:
        Dictionary mapping category names to centroid embeddings.
    
    Raises:
        MemoryLimitExceededError: If memory usage exceeds limit.
    """
    # Start memory tracking
    tracemalloc.start()
    
    try:
        # Load model
        model = SentenceTransformer(model_name)
        
        centroids = {}
        categories = taxonomy.get("categories", {})
        
        for category_name, category_def in categories.items():
            definition = category_def.get("definition", "")
            
            # Encode definition
            embedding = model.encode([definition])[0]
            centroids[category_name] = embedding.tolist()
            
            # Check memory usage
            current, peak = tracemalloc.get_traced_memory()
            if peak > MAX_RAM_GB * 1024 * 1024 * 1024:
                raise MemoryLimitExceededError(f"Memory limit exceeded: {peak / (1024**3):.2f}GB")
        
        return centroids
    
    finally:
        tracemalloc.stop()

def save_centroids(centroids: Dict[str, List[float]], output_path: Path) -> None:
    """
    Save centroids to a JSON file.
    
    Args:
        centroids: Dictionary of centroids.
        output_path: Path to save the centroids.
    """
    ensure_directories([str(output_path.parent)])
    
    # Convert numpy arrays to lists for JSON serialization
    serializable_centroids = {k: v for k, v in centroids.items()}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_centroids, f, indent=2)

def main():
    """Main entry point for taxonomy_builder script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build taxonomy centroids")
    parser.add_argument("--source", type=str, default="local", help="Source of taxonomy")
    parser.add_argument("--output", type=str, help="Output path for centroids")
    parser.add_argument("--model", type=str, default="all-MiniLM-L6-v2", help="Sentence transformer model")
    
    args = parser.parse_args()
    
    # Set seed
    set_seed(RANDOM_SEED)
    
    # Load taxonomy
    taxonomy = load_taxonomy(args.source)
    
    # Build centroids
    centroids = build_centroids(taxonomy, args.model)
    
    # Save centroids
    output = Path(args.output) if args.output else get_path("processed") / "taxonomy_centroids.json"
    save_centroids(centroids, output)
    
    print(f"Saved centroids to {output}")

if __name__ == "__main__":
    main()
