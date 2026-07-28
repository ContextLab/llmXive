"""
Probe Generator Service for ArcANE (User Story 2).

This module handles the generation of "Out-of-World" scenario prompts
based on character axes, ensuring semantic distance from the source text.
"""
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np

# Import existing utilities from the project
# Note: Using the API surface provided in the prompt.
# If sentence_transformers is not installed, the environment is invalid for this task.
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from src.lib.utils import get_logger

logger = get_logger(__name__)

# Constants
SIMILARITY_THRESHOLD = 0.3
MAX_ATTEMPTS = 150
MIN_VALID_PROBES = 50
MODEL_NAME = "all-MiniLM-L6-v2"

# Global cache for the embedding model to avoid reloading
_model_cache: Optional[Any] = None

def load_sentence_model_cached() -> Any:
    """
    Load the sentence transformer model with a simple caching mechanism.
    Returns the model instance.
    """
    global _model_cache
    if _model_cache is None:
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise RuntimeError(
                "sentence-transformers library is required but not installed. "
                "Please install it via `pip install sentence-transformers`."
            )
        logger.info(f"Loading SentenceTransformer model: {MODEL_NAME}")
        _model_cache = SentenceTransformer(MODEL_NAME)
        logger.info("Model loaded successfully.")
    return _model_cache

def calculate_semantic_similarity(text1: str, text2: str, model: Any) -> float:
    """
    Calculate the cosine similarity between two text strings using the provided model.

    Args:
        text1: First text string.
        text2: Second text string.
        model: The SentenceTransformer model instance.

    Returns:
        Cosine similarity score between -1 and 1.
    """
    if not text1 or not text2:
        return 0.0

    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    vec1, vec2 = embeddings[0], embeddings[1]

    # Normalize vectors
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    cosine_sim = np.dot(vec1, vec2) / (norm1 * norm2)
    return float(cosine_sim)

def validate_probe_against_corpus(
    probe_text: str,
    source_corpus: List[str],
    model: Any,
    threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[bool, float]:
    """
    Validates a generated probe against a source text corpus.
    Returns (is_valid, max_similarity_score).

    The probe is considered valid if its maximum cosine similarity
    against any text in the source corpus is strictly less than the threshold.
    """
    if not source_corpus:
        logger.warning("Source corpus is empty. Skipping similarity check.")
        return True, 0.0

    max_sim = -1.0
    for i, source_text in enumerate(source_corpus):
        if not source_text:
            continue
        
        sim = calculate_semantic_similarity(probe_text, source_text, model)
        if sim > max_sim:
            max_sim = sim
        
        # Early exit if threshold is breached
        if max_sim >= threshold:
            logger.debug(f"Probe failed similarity check at index {i}: score {max_sim:.4f} >= {threshold}")
            return False, max_sim

    logger.debug(f"Probe passed similarity check. Max score: {max_sim:.4f} < {threshold}")
    return True, max_sim

def load_source_corpus(corpus_path: Path) -> List[str]:
    """
    Loads the source text corpus from a JSONL or JSON file.
    Expects a file with 'text' or 'content' fields.
    """
    corpus = []
    if not corpus_path.exists():
        logger.error(f"Source corpus file not found: {corpus_path}")
        return corpus

    logger.info(f"Loading source corpus from {corpus_path}")
    
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                # Support common field names
                text = data.get('text') or data.get('content') or data.get('narrative')
                if text:
                    corpus.append(str(text))
            except json.JSONDecodeError:
                # Treat as raw text if not JSON
                corpus.append(line)
    
    logger.info(f"Loaded {len(corpus)} segments into source corpus.")
    return corpus

def generate_probe_candidate(
    character_name: str,
    coarse_axis: Dict[str, Any],
    fine_axis: Dict[str, Any],
    attempt_number: int
) -> str:
    """
    Generates a single probe candidate text.
    In a real implementation, this would call an LLM.
    For this task, we simulate the generation logic structure.
    """
    # Placeholder for actual LLM generation logic.
    # In the full pipeline, this would invoke the model defined in config.
    # Since T017 is the generator implementation and T018 is the check,
    # we assume the text comes from T017's logic or an LLM call.
    # Here we construct a deterministic placeholder to demonstrate the check logic.
    # NOTE: In a real run, this string would be the output of the LLM.
    
    coarse_desc = coarse_axis.get('description', '')
    fine_desc = fine_axis.get('description', '')
    
    # Simulating a generated probe text
    return (
        f"Scenario {attempt_number} for {character_name}: "
        f"Given the coarse trait '{coarse_desc}' and fine trait '{fine_desc}', "
        f"how would the character react in a completely alien environment with no gravity?"
    )

def run_probe_validation_demo():
    """
    Demo function to demonstrate the semantic similarity check.
    """
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        print("sentence-transformers not available. Cannot run demo.")
        return

    model = load_sentence_model_cached()
    
    # Simulated source corpus
    source_corpus = [
        "The character walked down the dark alley, looking for trouble.",
        "He drew his sword, the metal cold against his hand.",
        "She whispered a spell, the air shimmering with magic."
    ]

    # Valid probe (semantically distant)
    valid_probe = "Imagine a character floating in a void of pure light, deciding whether to create a universe."
    
    # Invalid probe (semantically similar)
    invalid_probe = "The character walked down a dark street, looking for a fight and drew his weapon."

    is_valid, score = validate_probe_against_corpus(valid_probe, source_corpus, model)
    print(f"Valid Probe: {valid_probe[:50]}...")
    print(f"  Is Valid: {is_valid}, Max Similarity: {score:.4f}")

    is_valid, score = validate_probe_against_corpus(invalid_probe, source_corpus, model)
    print(f"Invalid Probe: {invalid_probe[:50]}...")
    print(f"  Is Valid: {is_valid}, Max Similarity: {score:.4f}")

def main():
    """
    Main entry point for testing the probe generator validation logic.
    """
    run_probe_validation_demo()

if __name__ == "__main__":
    main()