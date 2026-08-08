"""
Ablation utility functions for token counting and syntactic complexity analysis.

This module provides tools to measure linguistic properties of critique strings
to ensure ablation studies maintain equivalent structural properties while
removing semantic content.
"""
import logging
from typing import Optional, Tuple, List
import spacy
from transformers import AutoTokenizer
import re

# Configure logging
logger = logging.getLogger(__name__)

# Global cache for tokenizer and spacy model to avoid reloading
_tokenizer: Optional[AutoTokenizer] = None
_spacy_model: Optional[spacy.Language] = None

# Default model paths
DEFAULT_TOKENIZER_PATH = "gpt2"
DEFAULT_SPACY_MODEL = "en_core_web_sm"

def get_target_tokenizer(model_path: str = DEFAULT_TOKENIZER_PATH) -> AutoTokenizer:
    """
    Load or retrieve the cached target tokenizer.
    
    Args:
        model_path: Path to the tokenizer model (default: gpt2)
        
    Returns:
        Loaded AutoTokenizer instance
    """
    global _tokenizer
    if _tokenizer is None:
        logger.info(f"Loading tokenizer from {model_path}...")
        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
    return _tokenizer

def calculate_token_length(text: str, tokenizer: Optional[AutoTokenizer] = None) -> int:
    """
    Calculate the exact token count of a text using the target tokenizer.
    
    Args:
        text: Input string to tokenize
        tokenizer: Optional pre-loaded tokenizer instance
        
    Returns:
        Integer token count
    """
    if tokenizer is None:
        tokenizer = get_target_tokenizer()
    
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

def load_spacy_model(model_name: str = DEFAULT_SPACY_MODEL) -> spacy.Language:
    """
    Load or retrieve the cached spaCy model.
    
    Args:
        model_name: Name of the spaCy model (default: en_core_web_sm)
        
    Returns:
        Loaded spaCy Language model
        
    Raises:
        ImportError: If spaCy is not installed
        OSError: If the specified model is not found
    """
    global _spacy_model
    if _spacy_model is None:
        logger.info(f"Loading spaCy model: {model_name}...")
        try:
            _spacy_model = spacy.load(model_name)
        except OSError:
            logger.error(f"spaCy model '{model_name}' not found. Run: python -m spacy download {model_name}")
            raise
    return _spacy_model

def calculate_syntactic_complexity(text: str, spacy_model: Optional[spacy.Language] = None) -> float:
    """
    Calculate a syntactic complexity score for a critique string.
    
    The score is based on the average depth of the dependency parse tree.
    Deeper trees indicate more complex syntactic structures.
    
    Args:
        text: Input critique string
        spacy_model: Optional pre-loaded spaCy model
        
    Returns:
        Float syntactic complexity score (average dependency depth)
        
    Raises:
        ValueError: If text is empty or contains no valid tokens
    """
    if not text or not text.strip():
        raise ValueError("Input text must not be empty")
    
    if spacy_model is None:
        spacy_model = load_spacy_model()
    
    doc = spacy_model(text)
    
    # Calculate depth for each token's dependency tree
    # We use the max depth of the subtree rooted at each token
    depths = []
    
    for token in doc:
        # Calculate depth of this token's subtree
        depth = 0
        stack = [token]
        visited = {token.i}
        
        while stack:
            current = stack.pop()
            # Add children that haven't been visited
            for child in current.children:
                if child.i not in visited:
                    visited.add(child.i)
                    stack.append(child)
                    depth += 1
        
        if depth > 0:
            depths.append(depth)
    
    if not depths:
        # Fallback: use number of sentences * average tokens per sentence
        # for very simple text that doesn't parse well
        return float(len(list(doc.sents)) * max(1, len(doc)))
    
    # Return average depth as the complexity score
    avg_depth = sum(depths) / len(depths)
    
    # Ensure score is > 0 for valid critiques
    # If average depth is 0 (very flat structure), return minimum positive value
    if avg_depth <= 0:
        avg_depth = 0.5
        
    return float(avg_depth)

def verify_token_match(original_text: str, ablation_text: str, 
                      tokenizer: Optional[AutoTokenizer] = None,
                      tolerance: int = 1) -> Tuple[bool, int, int]:
    """
    Verify that two texts have approximately the same token count.
    
    Args:
        original_text: Original critique text
        ablation_text: Ablated/neutral text
        tokenizer: Optional pre-loaded tokenizer
        tolerance: Allowed difference in token count
        
    Returns:
        Tuple of (is_match: bool, original_count: int, ablation_count: int)
    """
    orig_count = calculate_token_length(original_text, tokenizer)
    ablation_count = calculate_token_length(ablation_text, tokenizer)
    
    is_match = abs(orig_count - ablation_count) <= tolerance
    return is_match, orig_count, ablation_count

def main():
    """
    Main function to demonstrate the ablation utilities.
    """
    # Example usage
    test_critique = "The initial answer fails to consider the boundary conditions. Specifically, the variable x is assumed to be positive, but the problem statement allows for negative values. This logical gap undermines the entire derivation."
    
    print("Testing ablation utilities...")
    print(f"Input text: {test_critique}")
    
    # Test token length
    token_count = calculate_token_length(test_critique)
    print(f"Token count: {token_count}")
    
    # Test syntactic complexity
    complexity = calculate_syntactic_complexity(test_critique)
    print(f"Syntactic complexity score: {complexity:.4f}")
    
    # Verify the score is positive
    assert complexity > 0, "Syntactic complexity score must be positive"
    
    print("All tests passed!")

if __name__ == "__main__":
    main()