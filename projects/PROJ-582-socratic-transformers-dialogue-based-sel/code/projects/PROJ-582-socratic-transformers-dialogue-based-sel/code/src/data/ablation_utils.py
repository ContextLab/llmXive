"""
Ablation utilities for generating neutral placeholders and calculating token metrics.

This module provides functions to calculate the token count of critique strings
and generate neutral placeholders with equivalent token lengths for ablation studies.
"""

import logging
from typing import Optional, Tuple, List, Union

import re
from transformers import AutoTokenizer

from src.utils.config import get_config

logger = logging.getLogger(__name__)

_tokenizer: Optional[AutoTokenizer] = None


def get_target_tokenizer() -> AutoTokenizer:
    """
    Retrieve the tokenizer for the base model defined in config.

    Returns:
        AutoTokenizer: The configured tokenizer instance.

    Raises:
        ValueError: If the tokenizer cannot be loaded or configuration is missing.
    """
    global _tokenizer
    if _tokenizer is None:
        config = get_config()
        if not hasattr(config, 'BASE_MODEL_ID') or config.BASE_MODEL_ID is None:
            raise ValueError(
                "BASE_MODEL_ID is not defined in config. "
                "Please ensure src/utils/config.py is properly configured."
            )
        
        logger.info(f"Loading tokenizer for base model: {config.BASE_MODEL_ID}")
        try:
            _tokenizer = AutoTokenizer.from_pretrained(config.BASE_MODEL_ID)
            # Ensure padding token is set if not already
            if _tokenizer.pad_token is None:
                _tokenizer.pad_token = _tokenizer.eos_token
        except Exception as e:
            logger.error(f"Failed to load tokenizer for {config.BASE_MODEL_ID}: {e}")
            raise
    
    return _tokenizer


def calculate_token_count(text: Union[str, List[str]]) -> Union[int, List[int]]:
    """
    Calculate the token count of a text string (or list of strings) using the base model tokenizer.

    This function is critical for T015a (FR-007) to ensure ablation placeholders
    match the original critique's token length.

    Args:
        text: The string or list of strings to tokenize.

    Returns:
        The number of tokens (int) or a list of token counts (List[int]).

    Raises:
        ValueError: If the input is empty or not a string/list of strings.
        RuntimeError: If the tokenizer fails to encode the input.
    """
    if text is None:
        raise ValueError("Input text cannot be None.")
    
    tokenizer = get_target_tokenizer()

    if isinstance(text, str):
        if not text.strip():
            return 0
        try:
            # Use encode to get the list of token IDs
            # add_special_tokens=False ensures we only count the text tokens
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            return len(token_ids)
        except Exception as e:
            logger.error(f"Tokenization failed for text: '{text[:50]}...'. Error: {e}")
            raise RuntimeError(f"Failed to encode text: {e}")
    
    elif isinstance(text, list):
        if not text:
            return []
        if not all(isinstance(item, str) for item in text):
            raise ValueError("All items in the list must be strings.")
        
        counts = []
        for item in text:
            if not item.strip():
                counts.append(0)
            else:
                try:
                    token_ids = tokenizer.encode(item, add_special_tokens=False)
                    counts.append(len(token_ids))
                except Exception as e:
                    logger.error(f"Tokenization failed for list item: '{item[:50]}...'. Error: {e}")
                    raise RuntimeError(f"Failed to encode list item: {e}")
        return counts
    
    else:
        raise ValueError(f"Input must be a string or list of strings, got {type(text)}")


def load_spacy_model(lang: str = "en_core_web_sm") -> Optional[object]:
    """
    Attempt to load a spaCy model for syntactic complexity analysis.

    Note: This is a fallback utility. The primary tokenization is handled by
    the transformer tokenizer via calculate_token_count.

    Args:
        lang: The spaCy language model to load.

    Returns:
        The loaded spaCy nlp object, or None if not available.
    """
    try:
        import spacy
        return spacy.load(lang)
    except (ImportError, OSError) as e:
        logger.warning(f"spaCy model '{lang}' not available. Syntactic complexity analysis will be skipped. Error: {e}")
        return None


def calculate_syntactic_complexity(text: str, nlp: Optional[object] = None) -> float:
    """
    Calculate a proxy for syntactic complexity (e.g., average dependency depth).

    Requires a loaded spaCy model. If nlp is None, it attempts to load the default.

    Args:
        text: The text to analyze.
        nlp: Optional loaded spaCy model.

    Returns:
        A float representing the complexity score, or 0.0 if analysis fails.
    """
    if nlp is None:
        nlp = load_spacy_model()
    
    if nlp is None:
        logger.warning("spaCy not available; returning 0.0 for syntactic complexity.")
        return 0.0

    try:
        doc = nlp(text)
        # Simple metric: average depth of dependency tree
        # This is a proxy; more complex metrics can be derived from doc.sents
        total_depth = 0
        node_count = 0
        for token in doc:
            depth = 0
            ancestor = token.head
            while ancestor != token:
                depth += 1
                ancestor = ancestor.head
                if depth > 10: # Safety break
                    break
            total_depth += depth
            node_count += 1
        
        return total_depth / node_count if node_count > 0 else 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate syntactic complexity: {e}")
        return 0.0


def verify_token_match(original_text: str, placeholder_text: str, tolerance: int = 1) -> bool:
    """
    Verify that the placeholder text matches the token count of the original text.

    Args:
        original_text: The original critique string.
        placeholder_text: The generated neutral placeholder string.
        tolerance: Allowed difference in token count (default 1).

    Returns:
        True if the token counts match within tolerance, False otherwise.
    """
    orig_count = calculate_token_count(original_text)
    place_count = calculate_token_count(placeholder_text)
    
    diff = abs(orig_count - place_count)
    is_match = diff <= tolerance
    
    if not is_match:
        logger.warning(
            f"Token count mismatch: Original={orig_count}, Placeholder={place_count}, Diff={diff}"
        )
    
    return is_match


def main():
    """
    Main entry point for testing the ablation utilities.
    """
    logging.basicConfig(level=logging.INFO)
    
    test_text = "This is a test critique to verify the token counting mechanism."
    print(f"Input text: {test_text}")
    
    try:
        count = calculate_token_count(test_text)
        print(f"Token count: {count}")
        
        # Verify against direct tokenizer call
        tokenizer = get_target_tokenizer()
        direct_count = len(tokenizer.encode(test_text, add_special_tokens=False))
        print(f"Direct tokenizer count: {direct_count}")
        
        assert count == direct_count, f"Counts do not match: {count} != {direct_count}"
        print("Verification successful: Token count matches direct tokenizer output.")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        raise


if __name__ == "__main__":
    main()