"""
Axis Generator Service for ArcANE.

Implements semantic validation logic for Coarse and Fine character axes,
ensuring they meet lexical overlap and embedding distance constraints.
"""
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

# Lazy import to avoid heavy dependency if not used
_sentence_model = None

def load_sentence_model_cached():
    """
    Load the sentence-transformers model with caching to avoid reloading.
    Uses 'all-MiniLM-L6-v2' as specified in T012.
    """
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError(
                "The 'sentence-transformers' package is required for semantic validation. "
                "Please install it via: pip install sentence-transformers"
            )
    return _sentence_model

def _calculate_lexical_overlap(text_a: str, text_b: str) -> float:
    """
    Calculate the Jaccard index (lexical overlap) between two texts.
    Returns a float between 0.0 and 1.0.
    """
    if not text_a or not text_b:
        return 0.0

    # Tokenize: lowercase and split by non-alphanumeric characters
    tokens_a = set(re.findall(r'\w+', text_a.lower()))
    tokens_b = set(re.findall(r'\w+', text_b.lower()))

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    return len(intersection) / len(union)

def _calculate_embedding_cosine_distance(text_a: str, text_b: str, model) -> float:
    """
    Calculate the cosine distance between embeddings of two texts.
    Returns a float between 0.0 (identical) and 2.0 (opposite).
    Cosine Distance = 1 - Cosine Similarity.
    """
    try:
        embeddings = model.encode([text_a, text_b], convert_to_numpy=True, show_progress_bar=False)
        vec_a = embeddings[0]
        vec_b = embeddings[1]

        # Normalize to handle potential numerical instability
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 1.0 # Undefined similarity, treat as max distance

        similarity = np.dot(vec_a, vec_b) / (norm_a * norm_b)
        # Clamp similarity to [-1, 1] to avoid NaNs
        similarity = float(np.clip(similarity, -1.0, 1.0))

        return 1.0 - similarity
    except Exception as e:
        raise RuntimeError(f"Failed to compute embedding similarity: {e}")

def validate_axes_semantic_overlap(
    coarse_text: str,
    fine_text: str,
    lexical_threshold: float = 0.4,
    distance_threshold: float = 0.3
) -> Tuple[bool, Dict[str, float], str]:
    """
    Validates that Coarse and Fine axes satisfy semantic constraints:
    1. Lexical overlap (Jaccard) must be <= lexical_threshold (0.4).
    2. Embedding cosine distance must be >= distance_threshold (0.3).
       (i.e., they must be semantically distinct enough).

    Returns:
        (is_valid, metrics_dict, error_message)
        - is_valid: bool
        - metrics_dict: {'lexical_overlap': float, 'cosine_distance': float}
        - error_message: str describing failure if any
    """
    model = load_sentence_model_cached()

    # 1. Lexical Overlap Check
    lexical_overlap = _calculate_lexical_overlap(coarse_text, fine_text)
    if lexical_overlap > lexical_threshold:
        return (
            False,
            {'lexical_overlap': lexical_overlap, 'cosine_distance': None},
            f"Lexical overlap ({lexical_overlap:.4f}) exceeds threshold ({lexical_threshold}). "
            "Coarse and Fine axes share too many words."
        )

    # 2. Embedding Distance Check
    cosine_distance = _calculate_embedding_cosine_distance(coarse_text, fine_text, model)
    if cosine_distance < distance_threshold:
        return (
            False,
            {'lexical_overlap': lexical_overlap, 'cosine_distance': cosine_distance},
            f"Embedding cosine distance ({cosine_distance:.4f}) is below threshold ({distance_threshold}). "
            "Coarse and Fine axes are semantically too similar."
        )

    return (
        True,
        {'lexical_overlap': lexical_overlap, 'cosine_distance': cosine_distance},
        "Validation passed: Axes are sufficiently distinct."
    )

def generate_axes_from_input(coarse_input: str, fine_input: str) -> Dict[str, str]:
    """
    Constructs the axis objects from raw input strings.
    """
    return {
        "coarse": {
            "definition": coarse_input,
            "type": "Coarse"
        },
        "fine": {
            "definition": fine_input,
            "type": "Fine"
        }
    }

def serialize_axes_to_jsonl(axes: Dict[str, str], output_path: str) -> None:
    """
    Writes validated axes to a JSONL file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, 'a', encoding='utf-8') as f:
        json.dump(axes, f)
        f.write('\n')

def run_validation_demo():
    """
    A simple demonstration of the validation logic.
    """
    print("Running Axis Semantic Validation Demo...")
    
    # Example valid pair
    coarse = "The character is generally optimistic and hopeful about the future."
    fine = "The character exhibits a specific pattern of dopamine release when anticipating rewards."
    
    is_valid, metrics, msg = validate_axes_semantic_overlap(coarse, fine)
    print(f"Test 1 (Valid): {msg}")
    print(f"  Metrics: {metrics}")
    
    # Example invalid pair (too similar lexically)
    coarse_bad = "The character is brave and courageous."
    fine_bad = "The character is brave and courageous."
    
    is_valid, metrics, msg = validate_axes_semantic_overlap(coarse_bad, fine_bad)
    print(f"Test 2 (Invalid - Lexical): {msg}")
    print(f"  Metrics: {metrics}")

if __name__ == "__main__":
    run_validation_demo()