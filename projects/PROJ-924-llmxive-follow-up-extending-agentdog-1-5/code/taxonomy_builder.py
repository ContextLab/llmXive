"""
taxonomy_builder.py

Builds centroid embeddings for the AgentDoG safety taxonomy using sentence-transformers.
Implements strict runtime memory monitoring via tracemalloc to enforce a < 7GB RAM limit.
"""

import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from config import get_path, get_max_memory_gb, set_seed
from utils import save_json_file, load_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom exception for memory limits
class MemoryLimitExceededError(Exception):
    """Raised when peak memory usage exceeds the configured limit."""
    pass


def load_taxonomy(taxonomy_path: Path) -> List[Dict[str, Any]]:
    """
    Load the taxonomy JSON file.

    Args:
        taxonomy_path: Path to the taxonomy JSON file.

    Returns:
        List of taxonomy entries.

    Raises:
        FileNotFoundError: If the taxonomy file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not taxonomy_path.exists():
        raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")
    
    logger.info(f"Loading taxonomy from {taxonomy_path}")
    return load_json_file(taxonomy_path)


def build_centroids(
    taxonomy: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    max_memory_gb: float = 7.0
) -> Dict[str, Any]:
    """
    Build centroid embeddings for the taxonomy entries.

    This function uses tracemalloc to monitor peak memory usage and raises
    MemoryLimitExceededError if the limit is exceeded.

    Args:
        taxonomy: List of taxonomy entries with 'name' or 'text' fields.
        model_name: Name of the sentence-transformer model to use.
        batch_size: Batch size for embedding generation.
        max_memory_gb: Maximum allowed RAM in GB.

    Returns:
        Dictionary containing taxonomy entries with 'centroid' embeddings.

    Raises:
        MemoryLimitExceededError: If peak memory usage exceeds max_memory_gb.
        ImportError: If sentence-transformers is not installed.
    """
    # Start memory monitoring
    tracemalloc.start()
    
    try:
        logger.info(f"Starting centroid generation with model: {model_name}")
        logger.info(f"Memory limit: {max_memory_gb} GB")
        
        # Import here to avoid circular imports and only when needed
        from sentence_transformers import SentenceTransformer
        import numpy as np
        
        # Load model
        logger.info("Loading SentenceTransformer model...")
        model = SentenceTransformer(model_name)
        
        # Extract texts for embedding
        texts = []
        for entry in taxonomy:
            # Support both 'name' and 'text' fields
            text = entry.get('name') or entry.get('text') or entry.get('category')
            if text and isinstance(text, str) and text.strip():
                texts.append(text.strip())
            else:
                logger.warning(f"Skipping entry with missing/empty text: {entry.get('id', 'unknown')}")
        
        if not texts:
            raise ValueError("No valid text entries found in taxonomy")
        
        logger.info(f"Processing {len(texts)} taxonomy entries...")
        
        # Generate embeddings in batches to control memory
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            # Check memory before processing batch
            current, peak = tracemalloc.get_traced_memory()
            current_gb = current / (1024 ** 3)
            peak_gb = peak / (1024 ** 3)
            
            logger.info(f"Batch {i//batch_size + 1}: Current RAM: {current_gb:.2f} GB, Peak RAM: {peak_gb:.2f} GB")
            
            # Enforce memory limit
            if peak_gb > max_memory_gb:
                raise MemoryLimitExceededError(
                    f"Peak memory usage ({peak_gb:.2f} GB) exceeded limit ({max_memory_gb} GB). "
                    "Consider reducing batch_size or processing fewer entries."
                )
            
            # Generate embeddings for batch
            batch_embeddings = model.encode(
                batch_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            all_embeddings.append(batch_embeddings)
            
            # Optional: Clear memory between batches
            if i + batch_size < len(texts):
                del batch_embeddings
                import gc
                gc.collect()
        
        # Concatenate all embeddings
        logger.info("Concatenating embeddings...")
        all_embeddings = np.vstack(all_embeddings)
        
        # Compute centroids (mean of embeddings for each category if hierarchical,
        # otherwise just store the embeddings directly)
        # For this implementation, we assume each taxonomy entry is its own centroid
        # unless there are parent-child relationships defined.
        
        centroids = {}
        for idx, entry in enumerate(taxonomy):
            entry_id = entry.get('id', f"entry_{idx}")
            if idx < len(all_embeddings):
                centroids[entry_id] = {
                    'text': entry.get('name') or entry.get('text'),
                    'centroid': all_embeddings[idx].tolist()
                }
        
        logger.info(f"Successfully generated {len(centroids)} centroids")
        
        # Final memory check
        current, peak = tracemalloc.get_traced_memory()
        peak_gb = peak / (1024 ** 3)
        logger.info(f"Final peak memory usage: {peak_gb:.2f} GB")
        
        if peak_gb > max_memory_gb:
            raise MemoryLimitExceededError(
                f"Final peak memory usage ({peak_gb:.2f} GB) exceeded limit ({max_memory_gb} GB)."
            )
        
        return {
            'model': model_name,
            'num_centroids': len(centroids),
            'centroids': centroids,
            'metadata': {
                'peak_memory_gb': peak_gb,
                'max_memory_gb': max_memory_gb,
                'batch_size': batch_size
            }
        }
        
    finally:
        # Stop memory monitoring
        tracemalloc.stop()


def save_centroids(centroids_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save centroid data to a JSON file.

    Args:
        centroids_data: Dictionary containing centroid information.
        output_path: Path to save the JSON file.
    """
    logger.info(f"Saving centroids to {output_path}")
    save_json_file(centroids_data, output_path)
    logger.info(f"Successfully saved centroids to {output_path}")


def main() -> None:
    """
    Main entry point for building taxonomy centroids.
    """
    try:
        # Get configuration
        config = get_config()
        set_seed(config.get('seed', 42))
        
        # Paths
        taxonomy_path = get_path('taxonomy_agentdog')
        output_path = get_path('taxonomy_centroids')
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load taxonomy
        logger.info(f"Loading taxonomy from {taxonomy_path}")
        taxonomy = load_taxonomy(taxonomy_path)
        logger.info(f"Loaded {len(taxonomy)} taxonomy entries")
        
        # Build centroids with memory monitoring
        max_memory = get_max_memory_gb()
        batch_size = config.get('batch_size', 32)
        model_name = config.get('centroid_model', 'all-MiniLM-L6-v2')
        
        logger.info(f"Building centroids with max memory: {max_memory} GB, batch size: {batch_size}")
        
        centroids_data = build_centroids(
            taxonomy=taxonomy,
            model_name=model_name,
            batch_size=batch_size,
            max_memory_gb=max_memory
        )
        
        # Save centroids
        save_centroids(centroids_data, output_path)
        
        logger.info("Centroid generation completed successfully")
        
    except MemoryLimitExceededError as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during centroid generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()