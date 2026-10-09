"""
Semantic validation logic for Coarse and Fine axis definitions.

Implements constraints:
1. Lexical Overlap (Jaccard similarity) > 0.4
2. Semantic Distance (Cosine distance) < 0.3
3. Source observation is non-empty and distinct from descriptions.
"""

import re
from typing import Any, Dict, List, Tuple

# Using nltk for tokenization as per task spec
# Note: nltk must be installed. The task spec implies it is available via requirements.
try:
    import nltk
    from nltk.tokenize import word_tokenize

    # Ensure punkt tokenizer is available (download if missing in CI)
    try:
        word_tokenize("test")
    except LookupError:
        nltk.download("punkt", quiet=True)
except ImportError:
    raise ImportError("nltk is required for axis validation. Please install it.")

# Using sentence-transformers for embeddings as per task spec
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("sentence-transformers is required for axis validation. Please install it.")

from src.lib.utils import get_logger

logger = get_logger(__name__)

# Global cache for the model to avoid reloading
_MODEL = None


def load_sentence_model_cached() -> SentenceTransformer:
    """Load the sentence-transformer model once and reuse."""
    global _MODEL
    if _MODEL is None:
        logger.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def preprocess_text(text: str) -> List[str]:
    """Tokenize, lowercase, and strip punctuation."""
    if not isinstance(text, str):
        return []
    # Lowercase
    text = text.lower()
    # Tokenize using nltk
    try:
        tokens = word_tokenize(text)
    except Exception as e:
        logger.warning(f"Failed to tokenize text: {e}")
        return []

    # Strip punctuation and filter empty strings
    cleaned_tokens = [token for token in tokens if re.match(r"^[a-zA-Z]+$", token)]
    return cleaned_tokens


def calculate_lexical_overlap(text_a: str, text_b: str) -> float:
    """
    Calculate Jaccard similarity between two texts.
    Jaccard = |A ∩ B| / |A ∪ B|
    """
    tokens_a = set(preprocess_text(text_a))
    tokens_b = set(preprocess_text(text_b))

    if not tokens_a and not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def calculate_semantic_distance(text_a: str, text_b: str) -> float:
    """
    Calculate cosine distance between embeddings of two texts.
    Distance = 1 - CosineSimilarity
    """
    model = load_sentence_model_cached()

    try:
        embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
        emb_a = embeddings[0]
        emb_b = embeddings[1]

        # Normalize vectors
        norm_a = (emb_a**2).sum() ** 0.5
        norm_b = (emb_b**2).sum() ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 1.0

        cos_sim = (emb_a @ emb_b) / (norm_a * norm_b)
        # Clamp to [-1, 1] to avoid numerical issues
        cos_sim = max(-1.0, min(1.0, cos_sim))

        # Cosine distance
        return 1.0 - cos_sim
    except Exception as e:
        logger.error(f"Error computing semantic distance: {e}")
        raise


def validate_coarse_fine_independence(
    coarse_desc: str, fine_desc: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that Coarse and Fine descriptions meet independence constraints.

    Constraints:
    1. Lexical Overlap > 0.4
    2. Semantic Distance < 0.3

    Returns:
        Tuple (is_valid, metrics_dict)
    """
    metrics = {}

    # 1. Lexical Overlap
    lexical_overlap = calculate_lexical_overlap(coarse_desc, fine_desc)
    metrics["lexical_overlap"] = lexical_overlap
    lexical_pass = lexical_overlap > 0.4
    metrics["lexical_pass"] = lexical_pass

    if not lexical_pass:
        logger.warning(
            f"Lexical overlap {lexical_overlap:.4f} <= 0.4. Descriptions are too distinct."
        )

    # 2. Semantic Distance
    semantic_dist = calculate_semantic_distance(coarse_desc, fine_desc)
    metrics["semantic_distance"] = semantic_dist
    semantic_pass = semantic_dist < 0.3
    metrics["semantic_pass"] = semantic_pass

    if not semantic_pass:
        logger.warning(
            f"Semantic distance {semantic_dist:.4f} >= 0.3. Descriptions are too similar."
        )

    is_valid = lexical_pass and semantic_pass
    return is_valid, metrics


def validate_source_observation_distinctness(
    fine_desc: str, source_obs: str
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that the source_observation is non-empty and distinct from the fine description.
    """
    metrics = {}

    if not source_obs or not source_obs.strip():
        metrics["source_observation_valid"] = False
        metrics["source_observation_distinct"] = False
        logger.warning("Source observation is empty.")
        return False, metrics

    # Check distinctness via lexical overlap (strict threshold)
    # If they are too similar, the observation is just a copy of the description
    overlap = calculate_lexical_overlap(fine_desc, source_obs)
    metrics["source_obs_lexical_overlap"] = overlap

    # If overlap is extremely high (e.g., > 0.8), it's likely a copy/paste error
    distinct = overlap < 0.8
    metrics["source_observation_distinct"] = distinct

    if not distinct:
        logger.warning(
            f"Source observation too similar to Fine description (overlap {overlap:.4f})."
        )

    return distinct, metrics


def validate_axis_definition(axis_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a complete axis definition (Coarse + Fine).

    Expected structure (matches T010 schema):
    {
      "coarse": { "character": str, "axis_name": str, "description": str },
      "fine": { "character": str, "axis_name": str, "description": str, "source_observation": str }
    }
    """
    result = {"valid": False, "metrics": {}, "errors": []}

    if "coarse" not in axis_data or "fine" not in axis_data:
        result["errors"].append("Missing 'coarse' or 'fine' keys.")
        return False, result

    coarse = axis_data["coarse"]
    fine = axis_data["fine"]

    # Extract descriptions
    coarse_desc = coarse.get("description", "")
    fine_desc = fine.get("description", "")
    source_obs = fine.get("source_observation", "")

    # 1. Validate Coarse vs Fine Independence
    is_independent, indep_metrics = validate_coarse_fine_independence(coarse_desc, fine_desc)
    result["metrics"]["coarse_fine_independence"] = indep_metrics

    if not is_independent:
        result["errors"].append("Coarse and Fine descriptions fail independence constraints.")

    # 2. Validate Source Observation
    is_distinct, obs_metrics = validate_source_observation_distinctness(fine_desc, source_obs)
    result["metrics"]["source_observation_check"] = obs_metrics

    if not is_distinct:
        result["errors"].append(
            "Source observation is empty or not distinct from Fine description."
        )

    result["valid"] = is_independent and is_distinct
    return result["valid"], result


def main():
    """
    Demo/CLI entry point for testing the validator.
    Loads two JSON files (coarse and fine) and validates them.
    """
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Validate Coarse and Fine axis definitions.")
    parser.add_argument(
        "--coarse-file", required=True, help="Path to JSON file with Coarse definition."
    )
    parser.add_argument(
        "--fine-file", required=True, help="Path to JSON file with Fine definition."
    )
    args = parser.parse_args()

    try:
        with open(args.coarse_file, "r") as f:
            coarse_data = json.load(f)
        with open(args.fine_file, "r") as f:
            fine_data = json.load(f)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        sys.exit(1)

    # Construct the combined axis data
    axis_data = {"coarse": coarse_data, "fine": fine_data}

    is_valid, result = validate_axis_definition(axis_data)

    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print(f"Metrics: {result['metrics']}")
    if result["errors"]:
        print(f"Errors: {result['errors']}")

    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    import sys

    main()
