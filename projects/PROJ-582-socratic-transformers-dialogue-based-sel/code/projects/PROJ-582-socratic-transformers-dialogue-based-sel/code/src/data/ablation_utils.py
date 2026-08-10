import logging
from typing import Optional, Tuple, List
import re
from transformers import AutoTokenizer
from src.utils.config import get_config

logger = logging.getLogger(__name__)

_tokenizer: Optional[AutoTokenizer] = None

def get_target_tokenizer() -> AutoTokenizer:
    """
    Retrieve the target tokenizer for the project.
    Uses the model path defined in the project configuration.
    """
    global _tokenizer
    if _tokenizer is None:
        config = get_config()
        model_path = getattr(config, 'critic_model_path', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
        logger.info(f"Loading tokenizer from {model_path}")
        _tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
    return _tokenizer

def calculate_token_length(text: str) -> int:
    """
    Calculate the exact token count of a string using the target tokenizer.
    
    Args:
        text: The input string to tokenize.
        
    Returns:
        The number of tokens in the input text.
    """
    if not text:
        return 0
    tokenizer = get_target_tokenizer()
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

def load_spacy_model() -> None:
    """
    Placeholder for Spacy model loading if needed in future ablation steps.
    Currently T015c explicitly forbids spaCy/nltk, so this is a stub for API compatibility.
    """
    logger.warning("Spacy is not used in T015c. This function exists for future compatibility.")

def calculate_syntactic_complexity(text: str) -> float:
    """
    Calculate a syntactic complexity score using regex patterns to detect 
    nesting depth of parenthetical clauses and dependency-like structures.
    
    This function adheres to the constraint of using only `re` and `tokenizers` (no spaCy/nltk).
    
    Logic:
    1. Detect nested parentheses `(...)`, brackets `[...]`, and braces `{...}`.
    2. Detect logical connectors that often imply complex sentence structures (e.g., "because", "therefore", "however").
    3. Return a score based on maximum nesting depth and connector density.
    
    Args:
        text: The critique string to analyze.
        
    Returns:
        A numeric score > 0 for valid critiques.
    """
    if not text or not isinstance(text, str):
        return 0.0
    
    # Normalize text for regex processing
    clean_text = text.strip()
    if not clean_text:
        return 0.0

    score = 0.0

    # 1. Calculate Maximum Nesting Depth for Parentheses, Brackets, Braces
    # We look for sequences of opening symbols followed eventually by closing symbols.
    # A simple stack-based approach via regex is tricky, so we iterate char by char
    # but use regex to find candidate complex structures.
    
    max_depth = 0
    current_depth = 0
    
    # Patterns to count nesting
    open_chars = "([{"
    close_chars = ")]}"
    
    for char in clean_text:
        if char in open_chars:
            current_depth += 1
            if current_depth > max_depth:
                max_depth = current_depth
        elif char in close_chars:
            # Ensure we don't go negative (malformed text)
            if current_depth > 0:
                current_depth -= 1
    
    # Weight for nesting depth: deeper nesting implies higher syntactic complexity
    # Normalizing slightly to keep the score in a reasonable range
    nesting_score = max_depth * 1.5
    score += nesting_score

    # 2. Detect Complex Logical Connectors (Dependency-like structures)
    # These words often introduce subordinate clauses or complex reasoning chains.
    # Using a case-insensitive regex search.
    complex_connectors = [
        r'\bbecause\b', r'\bsince\b', r'\bas\b', r'\balthough\b', r'\bwhile\b',
        r'\btherefore\b', r'\bthus\b', r'\bhence\b', r'\bconsequently\b',
        r'\bhowever\b', r'\bnevertheless\b', r'\bnonetheless\b',
        r'\bif.*then\b', r'\bunless\b', r'\binsofar\b', r'\binasmuch\b'
    ]
    
    connector_count = 0
    for pattern in complex_connectors:
        matches = re.findall(pattern, clean_text, re.IGNORECASE)
        connector_count += len(matches)
    
    # Weight for connector density
    connector_score = connector_count * 0.8
    score += connector_score

    # 3. Detect Parenthetical Clauses (e.g., "(i.e., ...)" or "(e.g., ...)")
    # These add syntactic layers.
    parenthetical_pattern = r'\([^)]+\)'
    parenthetical_matches = re.findall(parenthetical_pattern, clean_text)
    parenthetical_score = len(parenthetical_matches) * 0.5
    score += parenthetical_score

    # Ensure the score is strictly positive for valid text
    # If the text is very simple (no nesting, no connectors), return a base complexity
    if score <= 0.0:
        # Base complexity based on length if no structural markers found
        # This prevents a score of 0 for valid but simple sentences
        word_count = len(clean_text.split())
        score = max(0.1, word_count * 0.05)

    logger.debug(f"Syntactic complexity for text (len={len(clean_text)}): {score:.4f} (nesting={max_depth}, connectors={connector_count})")
    return score

def verify_token_match(text_a: str, text_b: str, tolerance: int = 0) -> bool:
    """
    Verify if two texts have the same token length within a tolerance.
    
    Args:
        text_a: First text.
        text_b: Second text.
        tolerance: Allowed difference in token count.
        
    Returns:
        True if token counts match within tolerance, False otherwise.
    """
    len_a = calculate_token_length(text_a)
    len_b = calculate_token_length(text_b)
    return abs(len_a - len_b) <= tolerance

def main():
    """
    Main entry point for CLI execution to test the ablation utilities.
    """
    logging.basicConfig(level=logging.INFO)
    
    sample_critique = "The variable X is defined as Y, which implies Z; however, this contradicts the initial premise because (as shown in step 4) the assumption fails."
    
    print(f"Analyzing: {sample_critique}")
    
    token_len = calculate_token_length(sample_critique)
    print(f"Token Length: {token_len}")
    
    syntax_score = calculate_syntactic_complexity(sample_critique)
    print(f"Syntactic Complexity Score: {syntax_score:.4f}")
    
    assert token_len > 0, "Token length must be > 0 for valid text"
    assert syntax_score > 0, "Syntactic complexity must be > 0 for valid text"
    
    print("Verification passed.")

if __name__ == "__main__":
    main()