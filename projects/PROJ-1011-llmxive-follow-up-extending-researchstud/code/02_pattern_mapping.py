"""
Pattern Mapping Module (T020)

Implements retrieve_top_k_patterns() using sentence-transformers for CPU-tractable embeddings.
Uses 'all-MiniLM-L6-v2' quantized model to stay within memory constraints.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from utils.config import get_model_config, set_seed

# Configure logging
logger = logging.getLogger(__name__)

# Global model instance to avoid reloading
_model_instance = None

def get_model(model_name: str = "all-MiniLM-L6-v2"):
    """
    Load or retrieve the sentence-transformers model.
    Uses CPU-optimized settings for memory constraints.
    """
    global _model_instance
    
    if _model_instance is not None:
        return _model_instance

    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {model_name}")
        # Load with CPU optimization
        _model_instance = SentenceTransformer(model_name, device="cpu")
        
        # Quantize for memory efficiency if available
        try:
            _model_instance.quantize()
            logger.info("Model quantized for memory efficiency")
        except Exception as qe:
            logger.warning(f"Quantization failed (expected on some devices): {qe}")

        logger.info("Model loaded successfully")
        return _model_instance

    except ImportError:
        logger.error("sentence-transformers not installed. Please install: pip install sentence-transformers")
        raise
    except Exception as e:
        logger.error(f"Failed to load model {model_name}: {e}")
        raise

def encode_text(model, texts: List[str]) -> np.ndarray:
    """
    Encode a list of texts into embeddings.
    
    Args:
        model: The loaded SentenceTransformer model
        texts: List of text strings to encode
    
    Returns:
        numpy array of shape (n_texts, embedding_dim)
    """
    if not texts:
        return np.empty((0, model.get_sentence_embedding_dimension()))

    try:
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings
    except Exception as e:
        logger.error(f"Encoding failed: {e}")
        raise

def cosine_similarity_matrix(embeddings: np.ndarray, query_embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query embeddings and corpus embeddings.
    
    Args:
        embeddings: Corpus embeddings of shape (N, D)
        query_embeddings: Query embeddings of shape (M, D)
    
    Returns:
        Similarity matrix of shape (M, N)
    """
    # Normalize embeddings
    norm_corpus = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9)
    norm_queries = query_embeddings / (np.linalg.norm(query_embeddings, axis=1, keepdims=True) + 1e-9)

    # Compute cosine similarity
    similarity = np.dot(norm_queries, norm_corpus.T)
    return similarity

def retrieve_top_k_patterns(
    problem_statement: str,
    pattern_cards: List[Dict[str, Any]],
    model_name: str = "all-MiniLM-L6-v2",
    k: int = 5,
    threshold: float = 0.6,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k patterns for a given problem statement based on cosine similarity.
    
    Logic:
        1. Encode the problem statement.
        2. Encode all pattern card descriptions (or titles/abstracts).
        3. Compute cosine similarity.
        4. Filter by threshold (>= 0.6).
        5. Return top-k patterns sorted by similarity.
    
    Args:
        problem_statement: The text of the problem to find patterns for.
        pattern_cards: List of pattern card dictionaries. Must contain 'id' and 'description' (or 'abstract').
        model_name: Sentence-transformers model name.
        k: Number of top patterns to return.
        threshold: Minimum cosine similarity threshold.
        seed: Random seed for reproducibility (if needed).
    
    Returns:
        List of pattern cards that meet the threshold, sorted by similarity (descending).
    """
    set_seed(seed)

    if not pattern_cards:
        logger.warning("No pattern cards provided for retrieval.")
        return []

    # Load model
    model = get_model(model_name)

    # Prepare texts for encoding
    # Prioritize 'description', fallback to 'abstract', then 'title'
    pattern_texts = []
    valid_indices = []

    for idx, card in enumerate(pattern_cards):
        text = card.get("description") or card.get("abstract") or card.get("title", "")
        if text and text.strip():
            pattern_texts.append(text)
            valid_indices.append(idx)

    if not pattern_texts:
        logger.warning("No valid pattern descriptions found.")
        return []

    # Encode
    query_embedding = encode_text(model, [problem_statement])[0]
    pattern_embeddings = encode_text(model, pattern_texts)

    # Compute similarity
    similarities = cosine_similarity_matrix(pattern_embeddings, query_embedding.reshape(1, -1))[0]

    # Filter by threshold
    valid_mask = similarities >= threshold
    valid_similarities = similarities[valid_mask]
    valid_pattern_indices = np.array(valid_indices)[valid_mask]

    if len(valid_pattern_indices) == 0:
        logger.info(f"No patterns found above threshold {threshold} for problem: {problem_statement[:50]}...")
        return []

    # Sort by similarity (descending) and take top k
    top_k_indices = np.argsort(valid_similarities)[::-1][:k]

    result = []
    for i in top_k_indices:
        original_idx = valid_pattern_indices[i]
        pattern_card = pattern_cards[original_idx]
        pattern_card_with_score = pattern_card.copy()
        pattern_card_with_score["similarity_score"] = float(valid_similarities[i])
        result.append(pattern_card_with_score)

    logger.info(f"Retrieved {len(result)} patterns for problem statement.")
    return result

def main():
    """
    Main function to demonstrate pattern retrieval.
    Reads processed corpus and pattern cards (if available), and performs retrieval.
    """
    # Paths
    corpus_path = Path("data/processed/corpus.jsonl")
    patterns_path = Path("data/processed/patterns.jsonl")  # Assumed location
    output_path = Path("data/results/pattern_mapping_sample.json")

    # Load configuration
    config = get_model_config()
    seed = config.get("seed", 42)
    model_name = config.get("pattern_model", "all-MiniLM-L6-v2")
    threshold = config.get("similarity_threshold", 0.6)
    k = config.get("top_k_patterns", 5)

    set_seed(seed)

    # Load corpus (problem statements)
    if not corpus_path.exists():
        logger.error(f"Corpus not found at {corpus_path}. Please run data acquisition first.")
        return

    problem_statements = []
    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            # Extract problem statement (e.g., from abstract or specific field)
            problem_statements.append({
                "id": data.get("id"),
                "text": data.get("abstract") or data.get("title")
            })

    if not problem_statements:
        logger.error("No problem statements found in corpus.")
        return

    # Load pattern cards
    pattern_cards = []
    if patterns_path.exists():
        with open(patterns_path, "r", encoding="utf-8") as f:
            for line in f:
                pattern_cards.append(json.loads(line))
    else:
        logger.warning(f"Pattern cards not found at {patterns_path}. Using empty list.")

    # Perform retrieval for the first few problem statements
    results = []
    sample_size = min(10, len(problem_statements))  # Demo on first 10

    logger.info(f"Processing {sample_size} problem statements...")

    for i in range(sample_size):
        ps = problem_statements[i]
        matched_patterns = retrieve_top_k_patterns(
            problem_statement=ps["text"],
            pattern_cards=pattern_cards,
            model_name=model_name,
            k=k,
            threshold=threshold,
            seed=seed
        )
        results.append({
            "problem_id": ps["id"],
            "problem_text_preview": ps["text"][:100],
            "matched_patterns": matched_patterns
        })

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Pattern mapping results saved to {output_path}")

    return results

if __name__ == "__main__":
    main()
