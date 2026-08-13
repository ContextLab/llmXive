import json
import os
import sys
import tracemalloc
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from config import (
    get_config,
    get_path,
    get_output_path,
    ensure_directories,
    get_max_memory_gb,
    get_centroid_model,
    set_seed,
)
from utils import load_json_file, save_json_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the configured limit."""

    pass

class TaxonomyLoadError(Exception):
    """Raised when taxonomy cannot be loaded or is invalid."""

    pass

def load_taxonomy() -> Dict[str, Any]:
    """
    Load the taxonomy data from the configured path.
    Expects 'raw_taxonomy' to be defined in config.
    """
    try:
        taxonomy_path = str(get_path("raw_taxonomy"))
    except KeyError as e:
        raise TaxonomyLoadError(f"Path 'raw_taxonomy' not found in configuration.") from e

    if not os.path.exists(taxonomy_path):
        raise TaxonomyLoadError(f"Taxonomy file not found at {taxonomy_path}")

    logger.info(f"Loading taxonomy from {taxonomy_path}")
    try:
        with open(taxonomy_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise TaxonomyLoadError(f"Invalid JSON in taxonomy file: {e}") from e

    # Validate structure
    if not isinstance(data, list):
        raise TaxonomyLoadError("Taxonomy must be a list of category objects.")

    required_keys = {"category", "description"}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise TaxonomyLoadError(f"Taxonomy item {i} is not a dictionary.")
        missing = required_keys - set(item.keys())
        if missing:
            raise TaxonomyLoadError(
                f"Taxonomy item {i} missing required keys: {missing}"
            )

    return data

def build_centroids(taxonomy: List[Dict[str, Any]], batch_size: int = 64) -> Dict[str, np.ndarray]:
    """
    Build centroid embeddings for each taxonomy category.
    Uses sentence-transformers with dynamic batching to respect RAM limits.
    """
    model_name = get_centroid_model()
    logger.info(f"Loading model: {model_name}")

    # Ensure deterministic behavior
    set_seed(42)

    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        raise RuntimeError(f"Failed to load sentence transformer model: {e}") from e

    # Prepare inputs: combine category name and description
    categories = []
    texts = []
    for item in taxonomy:
        cat_name = item["category"]
        cat_desc = item.get("description", "")
        # Combine for better context
        text = f"{cat_name}: {cat_desc}".strip()
        categories.append(cat_name)
        texts.append(text)

    logger.info(f"Building centroids for {len(categories)} categories")

    # Start memory tracking
    tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    max_ram_gb = get_max_memory_gb()

    try:
        # Encode in batches to manage memory
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_embeddings = model.encode(batch_texts, convert_to_numpy=True)
            embeddings.append(batch_embeddings)

            # Check memory usage after each batch
            current, peak = tracemalloc.get_traced_memory()
            peak_gb = peak / (1024**3)
            logger.info(
                f"Processed batch {i//batch_size + 1}, peak RAM: {peak_gb:.2f} GB"
            )

            if peak_gb > max_ram_gb:
                raise MemoryLimitExceededError(
                    f"Peak RAM ({peak_gb:.2f} GB) exceeds limit ({max_ram_gb} GB)"
                )

        embeddings = np.vstack(embeddings)

        # Normalize embeddings for cosine distance
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms

        # Build centroid dictionary
        centroids = {cat: emb for cat, emb in zip(categories, embeddings)}

        logger.info(f"Successfully built {len(centroids)} centroids")
        return centroids

    finally:
        tracemalloc.stop()

def save_centroids(centroids: Dict[str, np.ndarray], output_path: str) -> None:
    """
    Save centroids to a JSON file.
    Converts numpy arrays to lists for JSON serialization.
    """
    # Convert numpy arrays to lists
    serializable_centroids = {
        cat: emb.tolist() for cat, emb in centroids.items()
    }

    # Ensure output directory exists
    ensure_directories([str(Path(output_path).parent)])

    logger.info(f"Saving centroids to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(serializable_centroids, f, indent=2)

    logger.info("Centroids saved successfully")

def main():
    """
    Main entry point for taxonomy centroid building.
    Usage:
        python -m code.taxonomy_builder --source <source_name> --output <output_path>
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Build and save taxonomy centroids"
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Taxonomy source name (e.g., 'agentdog_1_5_paper')",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output path for centroids JSON file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for encoding (default: 64)",
    )

    args = parser.parse_args()

    # Set seed for reproducibility
    set_seed(42)

    # Ensure directories
    ensure_directories([str(Path(args.output).parent)])

    try:
        # Load taxonomy
        taxonomy = load_taxonomy()

        # Build centroids
        centroids = build_centroids(taxonomy, batch_size=args.batch_size)

        # Save centroids
        save_centroids(centroids, args.output)

        logger.info("Taxonomy centroid building completed successfully")

    except MemoryLimitExceededError as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except TaxonomyLoadError as e:
        logger.error(f"Taxonomy load error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
