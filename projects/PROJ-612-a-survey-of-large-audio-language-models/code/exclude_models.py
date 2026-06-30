"""
Model Exclusion Logic (FR-013)

Implements fuzzy matching against a keyword list to skip models trained on
specific test datasets (esc-50, musicbench, audiobench, librispeech).
"""

import logging
import re
from typing import List, Dict, Any, Set

from fuzzywuzzy import fuzz

from config import load_config, get_exclusion_keywords

logger = logging.getLogger(__name__)


def normalize_string(text: str) -> str:
    """
    Normalize a string for comparison:
    - Convert to lowercase
    - Remove non-alphanumeric characters (keeping spaces)
    - Collapse multiple spaces
    """
    if not text:
        return ""
    text = text.lower()
    # Keep only alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def check_model_exclusion(model_name: str, exclusion_keywords: List[str], threshold: float = 0.8) -> bool:
    """
    Check if a model should be excluded based on its name containing
    references to test datasets using fuzzy matching.

    Args:
        model_name: The name of the model to check.
        exclusion_keywords: List of keywords representing test datasets.
        threshold: Similarity threshold (0.0 to 1.0). Default 0.8.

    Returns:
        True if the model should be excluded, False otherwise.
    """
    normalized_name = normalize_string(model_name)
    if not normalized_name:
        return False

    for keyword in exclusion_keywords:
        normalized_keyword = normalize_string(keyword)
        if not normalized_keyword:
            continue

        # Use token set ratio for better handling of word order and partial matches
        # fuzz.token_set_ratio returns 0-100, so we divide by 100
        similarity = fuzz.token_set_ratio(normalized_name, normalized_keyword) / 100.0

        if similarity >= threshold:
            logger.debug(
                "Model '%s' matches exclusion keyword '%s' with similarity %.2f (threshold: %.2f)",
                model_name, keyword, similarity, threshold
            )
            return True

    return False


def filter_models(models: List[Dict[str, Any]], exclusion_keywords: List[str], threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Filter a list of model instances, removing those that match exclusion criteria.

    Args:
        models: List of model dictionaries (must contain 'name' key).
        exclusion_keywords: List of keywords to check against.
        threshold: Similarity threshold.

    Returns:
        List of models that passed the exclusion check.
    """
    filtered_models = []
    excluded_count = 0

    for model in models:
        model_name = model.get("name", "")
        if not model_name:
            logger.warning("Model entry missing 'name' field, skipping exclusion check.")
            filtered_models.append(model)
            continue

        if check_model_exclusion(model_name, exclusion_keywords, threshold):
            excluded_count += 1
            logger.info("Excluding model: %s (matches exclusion criteria)", model_name)
        else:
            filtered_models.append(model)

    logger.info(
        "Model exclusion complete: %d excluded, %d remaining out of %d total.",
        excluded_count, len(filtered_models), len(models)
    )

    return filtered_models


def main():
    """
    Main entry point for testing exclusion logic.
    Reads config, loads a dummy model list, and prints excluded models.
    """
    logging.basicConfig(level=logging.INFO)

    config = load_config()
    keywords = get_exclusion_keywords()

    if not keywords:
        logger.warning("No exclusion keywords found in config. Skipping exclusion logic.")
        return

    # Dummy model list for demonstration if not provided via args
    dummy_models = [
        {"name": "LALM-Base", "domain": "speech"},
        {"name": "AudioBench-Model-V1", "domain": "music"},
        {"name": "LibriSpeech-Pretrained-XL", "domain": "speech"},
        {"name": "ESC-50-Classifier", "domain": "env"},
        {"name": "MusicBench-Generator", "domain": "music"},
        {"name": "Generic-Audio-Model", "domain": "speech"},
        {"name": "ESCAPE-50-variant", "domain": "env"},
    ]

    logger.info("Running model exclusion on dummy dataset...")
    logger.info("Exclusion keywords: %s", keywords)

    filtered = filter_models(dummy_models, keywords, threshold=0.8)

    print("\nExcluded Models:")
    for m in dummy_models:
        if m not in filtered:
            print(f"  - {m['name']}")

    print("\nRemaining Models:")
    for m in filtered:
        print(f"  - {m['name']}")


if __name__ == "__main__":
    main()
