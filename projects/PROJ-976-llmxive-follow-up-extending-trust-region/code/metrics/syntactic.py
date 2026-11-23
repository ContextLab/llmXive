"""
Syntactic diversity metrics.

Computes parse tree depth variance using spaCy's en_core_web_sm model.
Designed for CPU-only execution.
"""
import spacy
import numpy as np
from typing import List, Dict, Any, Optional
import warnings
import logging

# Configure logging for parse failures
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# Load English model (CPU-only)
# This model is small (~10MB) and suitable for CPU inference.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    raise RuntimeError(
        "en_core_web_sm not found. Please run: python -m spacy download en_core_web_sm"
    )

def parse_tree_depth(doc) -> int:
    """
    Calculate the maximum depth of the dependency parse tree for a document.
    
    Args:
        doc: A spaCy Doc object.
        
    Returns:
        The maximum depth of any sentence's parse tree in the document.
        Returns 0 if the document has no sentences.
    """
    def get_depth(token: spacy.tokens.Token) -> int:
        children = list(token.children)
        if not children:
            return 1
        return 1 + max(get_depth(child) for child in children)

    if not doc.sents:
        return 0
    
    # Calculate max depth across all sentences in the document
    return max(get_depth(sent.root) for sent in doc.sents)

def parse_tree_depth_variance(texts: List[str]) -> Optional[float]:
    """
    Calculate the variance of parse tree depths across a list of texts.
    
    This function processes texts in batches (implicitly via spaCy's internal
    processing) to compute parse tree depth for each, then calculates the
    variance of these depths.
    
    Args:
        texts: A list of text strings to analyze.
        
    Returns:
        The variance of parse tree depths as a float.
        Returns np.nan if:
        - The input list is empty
        - All texts fail to parse
        - Fewer than 2 valid parse depths are available
        Returns 0.0 if only one valid depth is available (variance is undefined).
        On parse failure for a specific text, returns NaN for that text and logs a warning.
    """
    if not texts:
        logger.warning("parse_tree_depth_variance: Empty input list")
        return np.nan

    depths = []
    
    for i, text in enumerate(texts):
        if not text or not isinstance(text, str):
            logger.warning(f"parse_tree_depth_variance: Skipping invalid text at index {i}")
            depths.append(np.nan)
            continue
            
        try:
            # Process text with spaCy
            doc = nlp(text)
            depth = parse_tree_depth(doc)
            depths.append(depth)
        except Exception as e:
            # Log warning but continue processing other texts
            # This satisfies T015: fallback logic for parse failures
            logger.warning(f"Parse failed for text at index {i}: {type(e).__name__}: {e}")
            depths.append(np.nan)

    # Filter out NaN values
    valid_depths = [d for d in depths if not np.isnan(d)]
    
    if len(valid_depths) == 0:
        logger.warning("parse_tree_depth_variance: No valid parse depths found")
        return np.nan
        
    if len(valid_depths) < 2:
        # Variance requires at least 2 points; return 0.0 as per statistical convention
        # for single-point "variance" in this context
        return 0.0

    return float(np.var(valid_depths, ddof=0))  # Population variance

def compute_syntactic_features(texts: List[str]) -> Dict[str, float]:
    """
    Compute syntactic features for a list of texts.
    
    Args:
        texts: A list of text strings.
        
    Returns:
        A dictionary containing:
        - 'syntactic_variation_score': The variance of parse tree depths.
        - 'parse_tree_depth_variance': Same as above (alias for consistency).
    """
    variance = parse_tree_depth_variance(texts)
    return {
        "syntactic_variation_score": variance,
        "parse_tree_depth_variance": variance,
    }

def main():
    """Demo of syntactic metrics on sample texts."""
    sample_texts = [
        "This is a simple sentence.",
        "This is a more complex sentence with a relative clause that modifies the noun.",
        "Short.",
        "The quick brown fox jumps over the lazy dog.",
        "Although it was raining, we decided to go for a walk because the air was fresh.",
        "",  # Empty string test
        None, # Invalid type test (will be caught by type check)
        "Text with special chars: <html> & 'quotes' that might break parsers.",
    ]
    
    print("Computing syntactic features...")
    features = compute_syntactic_features(sample_texts)
    
    print(f"Input texts: {len(sample_texts)}")
    print(f"Syntactic Features: {features}")
    
    # Verify output types
    assert isinstance(features["syntactic_variation_score"], (float, int))
    assert isinstance(features["parse_tree_depth_variance"], (float, int))
    print("Verification passed.")

if __name__ == "__main__":
    main()