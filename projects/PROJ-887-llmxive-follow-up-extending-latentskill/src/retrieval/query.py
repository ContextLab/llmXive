"""
Query module for generating text embeddings and measuring latency.

Implements FR-002: Generate query vectors using all-MiniLM-L6-v2.
Satisfies SC-003: Measure and log wall-clock latency for text embedding generation.
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.error("sentence-transformers not installed. Please install it via pip.")
    sys.exit(1)

# Constants
MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_OUTPUT_PATH = Path("data/processed/query_embeddings.json")
DEFAULT_MODEL_CACHE = Path("data/models")

def load_embedding_model(model_name: str = MODEL_NAME, cache_dir: Optional[Path] = None) -> SentenceTransformer:
    """
    Load the sentence transformer model.
    
    Args:
        model_name: Name of the HuggingFace model to load.
        cache_dir: Directory to cache the model.
        
    Returns:
        Loaded SentenceTransformer model instance.
    """
    if cache_dir is None:
        cache_dir = DEFAULT_MODEL_CACHE
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading model '{model_name}' from cache: {cache_dir}")
    try:
        model = SentenceTransformer(model_name, cache_folder=str(cache_dir))
        logger.info(f"Model loaded successfully. Embedding dimension: {model.get_sentence_embedding_dimension()}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model '{model_name}': {e}")
        raise

def generate_query_vector(
    model: SentenceTransformer,
    text: str,
    log_latency: bool = True
) -> Tuple[List[float], float]:
    """
    Generate a query vector (embedding) for the given text.
    
    Args:
        model: Loaded SentenceTransformer model.
        text: Input text to embed.
        log_latency: Whether to measure and log latency.
        
    Returns:
        Tuple of (embedding vector as list of floats, latency in seconds).
    """
    if log_latency:
        start_time = time.perf_counter()
    
    try:
        embedding = model.encode(text, convert_to_numpy=True)
        embedding_list = embedding.tolist()
    except Exception as e:
        logger.error(f"Failed to generate embedding for text: '{text[:50]}...'")
        raise
    
    if log_latency:
        end_time = time.perf_counter()
        latency = end_time - start_time
        return embedding_list, latency
    
    return embedding_list, 0.0

def generate_query_vectors_batch(
    model: SentenceTransformer,
    texts: List[str],
    batch_size: int = 32,
    show_progress: bool = False
) -> Tuple[List[List[float]], List[float]]:
    """
    Generate embeddings for a batch of texts.
    
    Args:
        model: Loaded SentenceTransformer model.
        texts: List of input texts.
        batch_size: Batch size for encoding.
        show_progress: Whether to show progress.
        
    Returns:
        Tuple of (list of embedding vectors, list of latencies per text).
    """
    all_embeddings = []
    all_latencies = []
    
    # Process in batches if needed
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        start_batch = time.perf_counter()
        
        batch_embeddings = model.encode(
            batch_texts,
            convert_to_numpy=True,
            show_progress_bar=show_progress and (i == 0)
        )
        
        end_batch = time.perf_counter()
        batch_latency = end_batch - start_batch
        
        # Distribute latency across texts in batch (approximate)
        per_text_latency = batch_latency / len(batch_texts)
        
        for j, emb in enumerate(batch_embeddings):
            all_embeddings.append(emb.tolist())
            all_latencies.append(per_text_latency)
    
    return all_embeddings, all_latencies

def save_query_results(
    embeddings: List[List[float]],
    texts: List[str],
    latencies: List[float],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save query results to a JSON file.
    
    Args:
        embeddings: List of embedding vectors.
        texts: Original input texts.
        latencies: Latencies for each embedding.
        output_path: Path to save the results.
        metadata: Additional metadata to include.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "model": MODEL_NAME,
        "total_queries": len(texts),
        "total_latency": sum(latencies),
        "avg_latency": sum(latencies) / len(latencies) if latencies else 0.0,
        "results": []
    }
    
    if metadata:
        results["metadata"] = metadata
    
    for i, (text, emb, lat) in enumerate(zip(texts, embeddings, latencies)):
        results["results"].append({
            "index": i,
            "text": text,
            "embedding": emb,
            "latency_seconds": lat
        })
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(texts)} query results to {output_path}")

def main() -> None:
    """
    Main entry point for generating query embeddings.
    
    Reads tasks from a YAML file (if provided) or uses default test queries,
    generates embeddings, measures latency, and saves results.
    """
    import yaml
    
    # Default test queries if no input file is provided
    default_queries = [
        "Navigate to the kitchen and pick up the apple.",
        "Find a book about machine learning in the library.",
        "Clean the dirty plate in the sink.",
        "Open the drawer and take out the spoon."
    ]
    
    # Check for input file from command line or environment
    input_file = os.environ.get("QUERY_INPUT_FILE")
    if not input_file and len(sys.argv) > 1:
        input_file = sys.argv[1]
    
    queries = default_queries
    if input_file:
        input_path = Path(input_file)
        if not input_path.exists():
            logger.warning(f"Input file {input_path} not found. Using default queries.")
        else:
            try:
                with open(input_path, 'r') as f:
                    data = yaml.safe_load(f)
                    queries = data.get("queries", default_queries)
            except Exception as e:
                logger.error(f"Failed to load input file: {e}")
                queries = default_queries
    
    logger.info(f"Processing {len(queries)} queries")
    
    # Load model
    model = load_embedding_model()
    
    # Generate embeddings with latency measurement
    embeddings, latencies = generate_query_vectors_batch(model, queries)
    
    # Prepare metadata
    metadata = {
        "model_name": MODEL_NAME,
        "embedding_dimension": model.get_sentence_embedding_dimension(),
        "device": "cpu"  # Default to CPU for compatibility
    }
    
    # Save results
    output_path = Path(os.environ.get("QUERY_OUTPUT_PATH", DEFAULT_OUTPUT_PATH))
    save_query_results(embeddings, queries, latencies, output_path, metadata)
    
    # Log summary
    total_latency = sum(latencies)
    avg_latency = total_latency / len(latencies) if latencies else 0
    logger.info(f"Summary: {len(queries)} queries processed in {total_latency:.4f}s "
               f"(avg: {avg_latency:.4f}s per query)")

if __name__ == "__main__":
    main()
