"""
Query module for generating text embeddings using sentence-transformers.

This module implements FR-002: Generate query vectors using a lightweight
sentence-transformer model and measure wall-clock latency.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.utils.config import get_project_root, get_data_path, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default model - lightweight sentence-transformer
DEFAULT_MODEL = "all-MiniLM-L6-v2"
MODEL_DIMENSION = 384  # Dimension for all-MiniLM-L6-v2

def load_embedding_model(model_name: str = DEFAULT_MODEL) -> SentenceTransformer:
    """
    Load a sentence-transformer model for generating embeddings.

    Args:
        model_name: Name of the sentence-transformer model to load.

    Returns:
        Loaded SentenceTransformer model.
    """
    logger.info(f"Loading embedding model: {model_name}")
    try:
        model = SentenceTransformer(model_name)
        logger.info(f"Successfully loaded model: {model_name}")
        logger.info(f"Model dimension: {model.get_sentence_embedding_dimension()}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def generate_query_embeddings(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = 32
) -> Tuple[np.ndarray, float]:
    """
    Generate embeddings for a list of text queries.

    Measures wall-clock latency for the embedding generation process.

    Args:
        model: Loaded SentenceTransformer model.
        texts: List of text strings to embed.
        batch_size: Batch size for embedding generation.

    Returns:
        Tuple of (embeddings as numpy array, wall-clock latency in seconds).
    """
    if not texts:
        logger.warning("No texts provided for embedding generation")
        return np.array([]), 0.0

    logger.info(f"Generating embeddings for {len(texts)} queries (batch_size={batch_size})")

    start_time = time.perf_counter()

    try:
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
    except Exception as e:
        logger.error(f"Error during embedding generation: {e}")
        raise

    end_time = time.perf_counter()
    latency = end_time - start_time

    logger.info(f"Generated embeddings in {latency:.4f} seconds "
               f"({len(texts) / latency:.2f} queries/sec)")

    # Ensure embeddings are 2D (even for single input)
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)

    return embeddings, latency

def get_query_vector(
    model: SentenceTransformer,
    query_text: str
) -> Tuple[np.ndarray, float]:
    """
    Generate embedding for a single query text.

    Args:
        model: Loaded SentenceTransformer model.
        query_text: Single text string to embed.

    Returns:
        Tuple of (embedding as 1D numpy array, wall-clock latency in seconds).
    """
    embeddings, latency = generate_query_embeddings(model, [query_text])
    return embeddings[0], latency

def save_query_results(
    embeddings: np.ndarray,
    latencies: List[float],
    output_path: Path,
    query_texts: Optional[List[str]] = None
) -> None:
    """
    Save query embeddings and latency metrics to disk.

    Args:
        embeddings: Array of embeddings (N x D).
        latencies: List of latency measurements.
        output_path: Path to save results.
        query_texts: Optional list of original query texts for reference.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = {
        'embeddings': embeddings,
        'latencies': latencies,
        'total_queries': len(embeddings),
        'avg_latency_ms': np.mean(latencies) * 1000 if latencies else 0,
        'max_latency_ms': np.max(latencies) * 1000 if latencies else 0,
        'min_latency_ms': np.min(latencies) * 1000 if latencies else 0,
    }

    if query_texts:
        results['query_texts'] = query_texts

    # Save as NPZ (embeddings are large)
    np.savez(
        output_path,
        embeddings=embeddings,
        latencies=np.array(latencies),
        metadata={
            'total_queries': results['total_queries'],
            'avg_latency_ms': results['avg_latency_ms'],
            'max_latency_ms': results['max_latency_ms'],
            'min_latency_ms': results['min_latency_ms'],
        }
    )

    logger.info(f"Saved query results to {output_path}")

def main() -> None:
    """
    Main entry point for the query module.

    Demonstrates loading the model, generating embeddings for sample queries,
    and saving results with latency metrics.
    """
    # Ensure directories exist
    ensure_directories()
    data_path = get_data_path()
    output_dir = data_path / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sample queries for demonstration
    sample_queries = [
        "Navigate to the kitchen and pick up the knife",
        "Find a book about machine learning",
        "Organize the desk by sorting papers",
        "Answer the question: What is the capital of France?",
        "Plan a route from the bedroom to the living room"
    ]

    try:
        # Load model
        model = load_embedding_model()

        # Generate embeddings with latency measurement
        embeddings, total_latency = generate_query_embeddings(model, sample_queries)

        logger.info(f"Generated {embeddings.shape[0]} embeddings with shape {embeddings.shape}")
        logger.info(f"Total latency: {total_latency:.4f} seconds")

        # Save results
        output_path = output_dir / "query_embeddings.npz"
        save_query_results(embeddings, [total_latency], output_path, sample_queries)

        logger.info("Query generation completed successfully")

    except Exception as e:
        logger.error(f"Query generation failed: {e}")
        raise

if __name__ == "__main__":
    main()
