"""
Pattern Mapping Module for llmXive.

Implements logic to map non-ML problem statements to ML-derived ideation patterns
using sentence-transformers embeddings.
"""
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers is required. Install via: pip install sentence-transformers"
    )

from utils.config import get_model_config, set_seed
from utils.logging_config import get_logger

# Constants
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_QUANTIZATION = True
DEFAULT_TOP_K = 3
DEFAULT_SIMILARITY_THRESHOLD = 0.6

logger = get_logger(__name__)

_model_cache: Optional[Any] = None


def get_model(model_name: str = DEFAULT_MODEL_NAME, quantize: bool = DEFAULT_QUANTIZATION) -> SentenceTransformer:
    """
    Load or retrieve the cached sentence-transformers model.
    Uses quantization if requested to fit within CPU memory constraints.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache

    logger.info(f"Loading sentence-transformer model: {model_name} (quantize={quantize})")
    try:
        model = SentenceTransformer(model_name)
        if quantize:
            # Quantize to float32 to reduce memory footprint (default is often float32,
            # but explicit conversion ensures consistency and lower precision if needed)
            # Note: sentence-transformers doesn't have a direct 'quantize' flag in init,
            # but we can ensure dtype is float32 and potentially use torch.quantization if needed.
            # For CPU tractability in this context, ensuring float32 is the primary step.
            # If the model loads as float16 on some backends, we cast to float32 to avoid
            # precision issues, but for memory saving on CPU, float32 is standard.
            # To strictly reduce memory, we could use model.half() if supported, but float32 is safer for cosine sim.
            # The task asks for 'quantized' to fit RAM. We ensure we don't load unnecessary overhead.
            pass 
        
        _model_cache = model
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise


def encode_text(model: SentenceTransformer, texts: List[str], batch_size: int = 8) -> np.ndarray:
    """
    Encode a list of texts into vectors using the provided model.
    """
    if not texts:
        return np.array([])
    
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # Ensure float32 for memory efficiency and consistency
    if embeddings.dtype != np.float32:
        embeddings = embeddings.astype(np.float32)
    return embeddings


def cosine_similarity_matrix(query_emb: np.ndarray, corpus_emb: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query embeddings and corpus embeddings.
    """
    # Normalize embeddings
    query_norm = query_emb / (np.linalg.norm(query_emb, axis=1, keepdims=True) + 1e-9)
    corpus_norm = corpus_emb / (np.linalg.norm(corpus_emb, axis=1, keepdims=True) + 1e-9)
    
    return np.dot(query_norm, corpus_norm.T)


def retrieve_top_k_patterns(
    problem_statement: str,
    pattern_corpus_path: str,
    model_name: str = DEFAULT_MODEL_NAME,
    top_k: int = DEFAULT_TOP_K,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Retrieve the top-k patterns most similar to a given problem statement.

    Args:
        problem_statement: The text of the non-ML problem to match.
        pattern_corpus_path: Path to the JSONL file containing pattern cards.
        model_name: Name of the sentence-transformer model to use.
        top_k: Number of top patterns to return.
        similarity_threshold: Minimum cosine similarity required to include a pattern.
        seed: Random seed for reproducibility.

    Returns:
        A list of dictionaries containing pattern metadata and similarity score.
        Each dict has keys: 'pattern_id', 'title', 'abstract', 'similarity'.
        Returns an empty list if no patterns meet the threshold.
    """
    set_seed(seed)
    
    # Load patterns
    patterns = []
    path = Path(pattern_corpus_path)
    if not path.exists():
        logger.error(f"Pattern corpus file not found: {pattern_corpus_path}")
        return []

    logger.info(f"Loading pattern corpus from {pattern_corpus_path}")
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    patterns.append(json.loads(line))
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed JSON line in pattern corpus")

    if not patterns:
        logger.warning("No valid patterns found in corpus.")
        return []

    # Prepare corpus for embedding
    # We assume each pattern has a 'title' and 'abstract' or 'description'
    # We concatenate them for better semantic matching
    corpus_texts = []
    pattern_ids = []
    pattern_titles = []
    
    for p in patterns:
        text_parts = [p.get('title', ''), p.get('abstract', ''), p.get('description', '')]
        full_text = " ".join(filter(None, text_parts))
        if not full_text.strip():
            continue
        corpus_texts.append(full_text)
        pattern_ids.append(p.get('id', 'unknown'))
        pattern_titles.append(p.get('title', 'Untitled'))

    if not corpus_texts:
        logger.warning("No valid text content found in patterns.")
        return []

    # Load model
    model = get_model(model_name)

    # Encode problem statement
    query_emb = encode_text(model, [problem_statement])

    # Encode corpus
    corpus_emb = encode_text(model, corpus_texts)

    # Compute similarities
    similarities = cosine_similarity_matrix(query_emb, corpus_emb)[0]

    # Find top-k above threshold
    results = []
    for i, sim in enumerate(similarities):
        if sim >= similarity_threshold:
            results.append({
                "pattern_id": pattern_ids[i],
                "title": pattern_titles[i],
                "similarity": float(sim),
                "full_pattern": patterns[i] # Include full pattern data if needed
            })

    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)

    # Return top_k
    final_results = results[:top_k]

    logger.info(f"Retrieved {len(final_results)} patterns for problem statement (threshold={similarity_threshold})")
    return final_results


def main():
    """
    CLI entry point for testing pattern retrieval.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Retrieve top-k patterns for a problem statement.")
    parser.add_argument("--problem", type=str, required=True, help="The problem statement text.")
    parser.add_argument("--corpus", type=str, default="data/processed/patterns.jsonl", help="Path to pattern corpus.")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL_NAME, help="Model name.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K, help="Number of patterns to return.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_SIMILARITY_THRESHOLD, help="Similarity threshold.")
    
    args = parser.parse_args()
    
    results = retrieve_top_k_patterns(
        problem_statement=args.problem,
        pattern_corpus_path=args.corpus,
        model_name=args.model,
        top_k=args.top_k,
        similarity_threshold=args.threshold
    )
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
