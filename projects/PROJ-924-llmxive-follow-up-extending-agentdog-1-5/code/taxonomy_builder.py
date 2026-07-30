"""
Taxonomy Builder Module

Generates centroid embeddings for the AgentDoG safety taxonomy and saves them
as a persistent artifact for reproducibility.
"""
import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from sibling modules (API surface check)
from config import get_path, get_max_memory_gb, get_centroid_model, set_seed
from utils import load_json_file, save_json_file

# Import sentence-transformers inside function to avoid import errors if not installed
# and to allow for lazy loading in test environments
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the configured limit."""
    pass

def load_taxonomy(taxonomy_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load the taxonomy from a JSON file.

    Args:
        taxonomy_path: Path to the taxonomy file. If None, uses config path.

    Returns:
        List of taxonomy entries.
    """
    if taxonomy_path is None:
        taxonomy_path = str(get_path("raw_taxonomy"))

    logger.info(f"Loading taxonomy from {taxonomy_path}")
    if not os.path.exists(taxonomy_path):
        raise FileNotFoundError(f"Taxonomy file not found: {taxonomy_path}")

    return load_json_file(taxonomy_path)

def build_centroids(taxonomy: List[Dict[str, Any]], model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Build centroid embeddings for the taxonomy categories.

    Args:
        taxonomy: List of taxonomy entries with 'category' and 'examples'.
        model_name: Name of the sentence-transformer model to use.

    Returns:
        Dictionary containing category names and their centroid embeddings.
    """
    if SentenceTransformer is None:
        raise ImportError("sentence-transformers is not installed. Please install it to build centroids.")

    if model_name is None:
        model_name = get_centroid_model()

    logger.info(f"Loading model: {model_name}")
    model = SentenceTransformer(model_name)

    result = {}
    categories_with_examples = []

    # Filter categories that have examples
    for entry in taxonomy:
        if 'category' in entry and 'examples' in entry and entry['examples']:
            categories_with_examples.append(entry)

    if not categories_with_examples:
        logger.warning("No categories with examples found in taxonomy.")
        return {"categories": [], "embeddings": [], "model_used": model_name}

    logger.info(f"Processing {len(categories_with_examples)} categories with examples")

    # Process each category
    for entry in categories_with_examples:
        category_name = entry['category']
        examples = entry['examples']

        if not examples or len(examples) == 0:
            logger.warning(f"Skipping category '{category_name}' - no examples")
            continue

        # Encode examples in batches to manage memory
        try:
            # Use batch_size=16 to be safe with memory constraints
            embeddings = model.encode(examples, batch_size=16, show_progress_bar=True)

            # Calculate centroid (mean of embeddings)
            centroid = embeddings.mean(axis=0)

            # Normalize the centroid
            centroid = centroid / (np.linalg.norm(centroid) + 1e-8)

            result[category_name] = centroid.tolist()

            # Check memory usage
            current, peak = tracemalloc.get_traced_memory()
            max_memory_gb = get_max_memory_gb()
            if peak / 1024**3 > max_memory_gb:
                raise MemoryLimitExceededError(
                    f"Peak memory usage ({peak/1024**3:.2f} GB) exceeded limit ({max_memory_gb} GB)"
                )

        except Exception as e:
            logger.error(f"Error processing category '{category_name}': {e}")
            raise

    # Prepare output structure
    output = {
        "model_used": model_name,
        "categories": list(result.keys()),
        "embeddings": [result[cat] for cat in result.keys()],
        "metadata": {
            "num_categories": len(result),
            "embedding_dimension": len(list(result.values())[0]) if result else 0
        }
    }

    return output

def save_centroids(centroids_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save the centroids to a JSON file.

    Args:
        centroids_data: Dictionary containing centroid data.
        output_path: Path to save the centroids. If None, uses config path.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = str(get_path("processed_taxonomy"))

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Saving centroids to {output_path}")
    save_json_file(centroids_data, output_path)

    # Verify the file was saved
    if not os.path.exists(output_path):
        raise RuntimeError(f"Failed to save centroids to {output_path}")

    logger.info(f"Successfully saved centroids to {output_path}")
    return output_path

def main():
    """Main entry point for taxonomy building."""
    import numpy as np  # Import here to ensure it's available

    # Set random seed for reproducibility
    set_seed()

    # Start memory tracing
    tracemalloc.start()

    try:
        # Load taxonomy
        taxonomy = load_taxonomy()
        logger.info(f"Loaded {len(taxonomy)} taxonomy entries")

        # Build centroids
        centroids_data = build_centroids(taxonomy)
        logger.info(f"Built centroids for {centroids_data['metadata']['num_categories']} categories")

        # Save centroids
        output_path = save_centroids(centroids_data)
        logger.info(f"Centroids saved to {output_path}")

        # Print final memory stats
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Peak memory usage: {peak / 1024**3:.2f} GB")

        return output_path

    except MemoryLimitExceededError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()
