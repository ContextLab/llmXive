"""
Utility functions for text preprocessing and linguistic analysis.
Implements FR-008: Unicode NFKC normalization and text cleaning helpers.
Also implements T007: POS tagging and dependency parsing wrappers using spaCy.
"""
import unicodedata
import re
from typing import Set, List, Optional, Tuple

try:
    import spacy
    from spacy.tokens import Doc
except ImportError:
    spacy = None
    Doc = None

# Global variable to hold the loaded spaCy model (lazy loaded)
_nlp_model: Optional["spacy.Language"] = None
_model_name = "en_core_web_sm"


def _load_spacy_model() -> "spacy.Language":
    """
    Lazily load the spaCy English model.
    
    Ensures the model is loaded only once and reused for subsequent calls.
    Handles the requirement to download the model if it's not present.
    
    Returns:
        The loaded spaCy pipeline.
        
    Raises:
        ImportError: If spaCy is not installed.
        RuntimeError: If the model cannot be loaded or downloaded.
    """
    global _nlp_model
    
    if spacy is None:
        raise ImportError(
            "spaCy is not installed. Please install it via requirements.txt: "
            "pip install spacy && python -m spacy download en_core_web_sm"
        )
    
    if _nlp_model is not None:
        return _nlp_model
    
    try:
        _nlp_model = spacy.load(_model_name)
    except OSError:
        # Model not found, attempt to download
        raise RuntimeError(
            f"The spaCy model '{_model_name}' is not installed. "
            f"Please run: python -m spacy download {_model_name}"
        )
    
    return _nlp_model


def get_pos_tags(text: str) -> List[str]:
    """
    Extract Part-of-Speech (POS) tags from text using spaCy.
    
    FR-002 Requirement: Compute syntactic similarity based on POS tag sets.
    This function provides the POS tags necessary for that calculation.
    
    Args:
        text: Input text string to analyze.
        
    Returns:
        List of POS tags (strings) corresponding to each token in the text.
        
    Raises:
        TypeError: If input is not a string.
        ImportError: If spaCy is not installed.
        RuntimeError: If the spaCy model is unavailable.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    if not text.strip():
        return []
    
    nlp = _load_spacy_model()
    doc = nlp(text)
    
    return [token.pos_ for token in doc]


def get_dependency_relations(text: str) -> List[str]:
    """
    Extract dependency relation labels from text using spaCy.
    
    Used for sensitivity analysis (FR-009) to compare POS-based metrics
    against dependency-parse-based metrics.
    
    Args:
        text: Input text string to analyze.
        
    Returns:
        List of dependency relation labels (strings) for each token.
        
    Raises:
        TypeError: If input is not a string.
        ImportError: If spaCy is not installed.
        RuntimeError: If the spaCy model is unavailable.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    if not text.strip():
        return []
    
    nlp = _load_spacy_model()
    doc = nlp(text)
    
    return [token.dep_ for token in doc]


def get_syntactic_features(text: str) -> Tuple[List[str], List[str]]:
    """
    Extract both POS tags and dependency relations from text.
    
    Convenience wrapper for efficiency when both features are needed.
    
    Args:
        text: Input text string to analyze.
        
    Returns:
        Tuple of (pos_tags, dep_relations), both lists of strings.
        
    Raises:
        TypeError: If input is not a string.
        ImportError: If spaCy is not installed.
        RuntimeError: If the spaCy model is unavailable.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    if not text.strip():
        return [], []
    
    nlp = _load_spacy_model()
    doc = nlp(text)
    
    pos_tags = [token.pos_ for token in doc]
    dep_relations = [token.dep_ for token in doc]
    
    return pos_tags, dep_relations


def normalize_text(text: str) -> str:
    """
    Apply Unicode NFKC normalization to input text.
    
    FR-008 Requirement: All text data must be normalized using Unicode NFKC
    to ensure consistent representation of characters (e.g., compatibility
    decomposition, canonical composition).
    
    Args:
        text: Raw input string to normalize.
        
    Returns:
        NFKC-normalized string.
        
    Raises:
        TypeError: If input is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    return unicodedata.normalize('NFKC', text)


def clean_text(text: str) -> str:
    """
    Clean text by normalizing, stripping whitespace, and removing control characters.
    
    This function applies NFKC normalization and removes non-printable control
    characters (except newlines and tabs which may be meaningful in dialogue).
    
    Args:
        text: Raw input string to clean.
        
    Returns:
        Cleaned and normalized string.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    # Apply NFKC normalization
    normalized = normalize_text(text)
    
    # Remove control characters (category 'Cc') except newline (\n) and tab (\t)
    # We keep \n and \t as they might be meaningful in dialogue structure
    cleaned_chars = []
    for char in normalized:
        category = unicodedata.category(char)
        if category == 'Cc' and char not in ('\n', '\t'):
            continue
        cleaned_chars.append(char)
    
    result = ''.join(cleaned_chars)
    
    # Strip leading/trailing whitespace
    result = result.strip()
    
    return result


def is_valid_text(text: str) -> bool:
    """
    Check if a string contains valid, non-empty text after cleaning.
    
    Used to filter out empty or purely whitespace records from dialogue data.
    
    Args:
        text: Input string to validate.
        
    Returns:
        True if text is non-empty after cleaning, False otherwise.
    """
    if not isinstance(text, str):
        return False
    
    cleaned = clean_text(text)
    return len(cleaned) > 0


def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """
    Calculate Jaccard similarity between two sets.
    
    Jaccard similarity = |A ∩ B| / |A ∪ B|
    
    Args:
        set_a: First set of elements.
        set_b: Second set of elements.
        
    Returns:
        Jaccard similarity coefficient (0.0 to 1.0).
        
    Note:
        This is a helper function for lexical and POS similarity calculations.
        Implemented for T006 to support lexical (token sets) and syntactic (POS sets)
        accommodation metric computations.
    """
    if not isinstance(set_a, set) or not isinstance(set_b, set):
        raise TypeError("Both arguments must be sets")
    
    if len(set_a) == 0 and len(set_b) == 0:
        return 1.0  # Empty sets are considered identical
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    return intersection / union if union > 0 else 0.0


def tokenize_simple(text: str) -> List[str]:
    """
    Simple tokenization by splitting on whitespace and punctuation.
    
    Converts text to lowercase and splits on non-alphanumeric characters.
    Useful for lexical overlap calculations without external dependencies.
    
    Args:
        text: Input text to tokenize.
        
    Returns:
        List of lowercase tokens.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected string input, got {type(text).__name__}")
    
    # Convert to lowercase
    text = text.lower()
    
    # Split on non-alphanumeric characters
    tokens = re.findall(r'\b\w+\b', text)
    
    return tokens
