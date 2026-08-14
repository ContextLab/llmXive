"""
Ablation utilities for calculating token lengths and generating neutral placeholders.

This module provides tools to measure the token count of critique strings
using the target tokenizer (loaded from config) and to generate neutral
placeholder text of equivalent token length for ablation studies.

Philosophical Note:
This utility supports the "negative selection on belief" framework by allowing
the isolation of semantic content from token count. By replacing critiques
with neutral placeholders of identical length, we can determine if the
learning signal comes from the *content* of the critique or merely the
*presence* of a selection pressure (token duration/complexity).
"""
import logging
from typing import Optional, Tuple, List
import re

from transformers import AutoTokenizer
from src.utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

def get_target_tokenizer() -> AutoTokenizer:
    """
    Loads the target tokenizer based on the BASE_MODEL_ID from config.

    Returns:
        AutoTokenizer: The loaded tokenizer instance.

    Raises:
        ValueError: If the tokenizer cannot be loaded or config is missing.
    """
    config = get_config()
    model_id = config.BASE_MODEL_ID

    if not model_id:
        raise ValueError("BASE_MODEL_ID is not defined in configuration.")

    logger.info(f"Loading tokenizer for model: {model_id}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Ensure pad token is set if not already
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer
    except Exception as e:
        logger.error(f"Failed to load tokenizer for {model_id}: {e}")
        raise

def calculate_token_length(text: str, tokenizer: Optional[AutoTokenizer] = None) -> int:
    """
    Calculates the exact token count of a given string using the target tokenizer.

    This function is critical for the ablation study (T015b) to ensure that
    neutral placeholders match the original critique's token length exactly.

    Args:
        text (str): The string to tokenize (e.g., a critique).
        tokenizer (AutoTokenizer, optional): The tokenizer to use. If None,
            loads the target tokenizer from config.

    Returns:
        int: The number of tokens in the text.
    """
    if tokenizer is None:
        tokenizer = get_target_tokenizer()

    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text)}")

    # Encode the text and count tokens
    # add_special_tokens=False ensures we only count the content tokens
    encoding = tokenizer.encode(text, add_special_tokens=False)
    token_count = len(encoding)

    logger.debug(f"Text length: {len(text)} chars -> {token_count} tokens")
    return token_count

def load_spacy_model() -> Optional[object]:
    """
    Attempts to load a spaCy model for syntactic complexity analysis.
    This is optional and used for advanced ablation metrics.

    Returns:
        object or None: The spaCy nlp model if available, None otherwise.
    """
    try:
        import spacy
        # Try loading a small model, fallback to None if not installed
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy 'en_core_web_sm' model not found. Install with 'python -m spacy download en_core_web_sm'")
            return None
    except ImportError:
        logger.warning("spaCy not installed. Syntactic complexity analysis will be skipped.")
        return None

def calculate_syntactic_complexity(text: str, nlp: Optional[object] = None) -> float:
    """
    Calculates a proxy for syntactic complexity (e.g., average dependency depth).

    Args:
        text (str): The text to analyze.
        nlp (object, optional): A loaded spaCy nlp model.

    Returns:
        float: A complexity score (0.0 if analysis fails).
    """
    if nlp is None:
        nlp = load_spacy_model()

    if nlp is None:
        return 0.0

    try:
        doc = nlp(text)
        # Simple metric: average depth of dependency tree
        depths = [token.dep_.count('-') + 1 for token in doc if token.dep_]
        if not depths:
            return 0.0
        return sum(depths) / len(depths)
    except Exception as e:
        logger.warning(f"Failed to calculate syntactic complexity: {e}")
        return 0.0

def verify_token_match(original_text: str, placeholder_text: str, tokenizer: Optional[AutoTokenizer] = None) -> bool:
    """
    Verifies that the placeholder text has the exact same token count as the original.

    Args:
        original_text (str): The original critique string.
        placeholder_text (str): The generated placeholder string.
        tokenizer (AutoTokenizer, optional): The tokenizer to use.

    Returns:
        bool: True if token counts match, False otherwise.
    """
    orig_len = calculate_token_length(original_text, tokenizer)
    placeholder_len = calculate_token_length(placeholder_text, tokenizer)
    match = orig_len == placeholder_len

    if not match:
        logger.warning(f"Token mismatch: Original={orig_len}, Placeholder={placeholder_len}")
    else:
        logger.debug("Token length verification passed.")

    return match

def main():
    """
    Main entry point for testing the token calculator utility.
    """
    import sys
    import json

    # Example usage
    sample_critique = "The initial answer is incorrect because it fails to account for the constraints of the problem. Specifically, the logic assumes a linear relationship where a non-linear one exists."

    try:
        tokenizer = get_target_tokenizer()
        length = calculate_token_length(sample_critique, tokenizer)
        print(f"Sample Critique Token Count: {length}")
        print(f"Sample Text: {sample_critique}")
    except Exception as e:
        print(f"Error running token calculator: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()