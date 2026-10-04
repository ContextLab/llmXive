import os
import gc
import logging
import json
import math
from typing import Dict, List, Optional, Any

import kenlm
import numpy as np
import pandas as pd
import spacy
from transformers import AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global constants
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
KENLM_MODEL_PATH = os.path.join(PROJECT_ROOT, 'data', 'models', 'kenlm_en.arpa')
SPACY_MODEL = 'en_core_web_sm'

# Global cache for heavy resources
_SPACY_NLP: Optional[Any] = None
_TOKENIZER: Optional[Any] = None
_KENLM_MODEL: Optional[Any] = None


def get_spacy_nlp() -> Any:
    """Lazy load spaCy model."""
    global _SPACY_NLP
    if _SPACY_NLP is None:
        logger.info(f"Loading spaCy model: {SPACY_MODEL}")
        _SPACY_NLP = spacy.load(SPACY_MODEL)
    return _SPACY_NLP


def get_tokenizer():
    """Lazy load HuggingFace tokenizer."""
    global _TOKENIZER
    if _TOKENIZER is None:
        logger.info("Loading HuggingFace tokenizer (Llama-3-8B)")
        _TOKENIZER = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B", trust_remote_code=True)
    return _TOKENIZER


def load_or_download_kenlm() -> Any:
    """
    Load the KenLM model.
    
    CRITICAL: This function validates the existence of the KenLM model file.
    If the file is missing, it raises a FileNotFoundError with a clear message
    to fail loudly before attempting to use a non-existent model.
    
    Returns:
        kenlm.LanguageModel instance.
        
    Raises:
        FileNotFoundError: If the KenLM model file does not exist.
    """
    global _KENLM_MODEL
    
    if _KENLM_MODEL is not None:
        return _KENLM_MODEL
    
    if not os.path.exists(KENLM_MODEL_PATH):
        logger.error(f"KenLM model not found at {KENLM_MODEL_PATH}")
        raise FileNotFoundError(
            f"KenLM model not found. Expected path: {KENLM_MODEL_PATH}. "
            "Please download the model or verify the path configuration."
        )
    
    logger.info(f"Loading KenLM model from {KENLM_MODEL_PATH}")
    try:
        _KENLM_MODEL = kenlm.LanguageModel(KENLM_MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load KenLM model: {e}")
        raise RuntimeError(f"Failed to initialize KenLM model: {e}") from e
    
    return _KENLM_MODEL


def is_ambiguous_token(token: str) -> bool:
    """
    Check if a token is ambiguous (special characters, emojis, etc.).
    
    Args:
        token: The token string to check.
        
    Returns:
        True if the token is considered ambiguous/special, False otherwise.
    """
    if not token or len(token) == 0:
        return True
    
    # Check for non-printable characters or control codes
    if not token.isprintable():
        return True
    
    # Check for emojis (basic range check)
    if any('\U0001F300' <= c <= '\U0001F9FF' for c in token):
        return True
        
    # Check for excessive punctuation or symbols without letters/numbers
    if all(not c.isalnum() for c in token):
        return True
        
    return False


def get_token_category(token: str) -> str:
    """
    Assign a category to a token based on its characteristics.
    
    Args:
        token: The token string.
        
    Returns:
        A category string ('neutral', 'punctuation', 'number', 'alpha', etc.).
    """
    if is_ambiguous_token(token):
        return 'neutral'
        
    if token.isalpha():
        return 'alpha'
    elif token.isdigit():
        return 'number'
    elif token.isspace():
        return 'whitespace'
    else:
        return 'punctuation'


def compute_entropy(token_probs: List[float]) -> float:
    """
    Compute the Shannon entropy of a list of token probabilities.
    
    Args:
        token_probs: List of probability values.
        
    Returns:
        Entropy value in bits.
    """
    if not token_probs:
        return 0.0
    
    # Filter out zeros to avoid log(0)
    valid_probs = [p for p in token_probs if p > 0]
    if not valid_probs:
        return 0.0
        
    entropy = 0.0
    for p in valid_probs:
        entropy -= p * math.log2(p)
        
    return entropy


def compute_kenlm_perplexity(sentence: str, window_size: int = 5) -> float:
    """
    Compute the perplexity of a sentence or token context using KenLM.
    
    Args:
        sentence: The text string to evaluate.
        window_size: Size of the context window (not strictly used by KenLM API 
                     but kept for interface consistency with local density logic).
                     
    Returns:
        Perplexity value.
    """
    if not sentence or not sentence.strip():
        return 0.0
        
    model = load_or_download_kenlm()
    
    # KenLM .score() returns the log probability of the next word given history
    # We compute perplexity as exp(-1/N * sum(log P(w_i | history)))
    # For a single sentence, we can use the .perplexity() method directly if available,
    # or compute manually.
    
    try:
        # KenLM Python binding .perplexity() returns the perplexity of the sentence
        ppl = model.perplexity(sentence)
        return float(ppl)
    except Exception as e:
        logger.warning(f"KenLM perplexity calculation failed for sentence '{sentence}': {e}")
        return 0.0


def compute_local_semantic_density(token: str, context_window: List[str], model: Optional[Any] = None) -> float:
    """
    Compute local semantic density as the perplexity of the token given its local context.
    
    Args:
        token: The target token.
        context_window: List of surrounding tokens.
        model: Optional pre-loaded KenLM model.
        
    Returns:
        Perplexity value representing local semantic density.
    """
    if model is None:
        model = load_or_download_kenlm()
        
    # Construct the context string
    # We assume context_window is a list of tokens around the target
    # We will create a sentence fragment: [prev_tokens] + [token]
    # To be robust, we join them with spaces.
    context_str = " ".join(context_window + [token])
    
    if not context_str.strip():
        return 0.0
        
    return compute_kenlm_perplexity(context_str)


def process_document(document: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Process a single document to extract features.
    
    Args:
        document: Dictionary containing 'text' and 'id'.
        config: Optional configuration dictionary.
        
    Returns:
        List of dictionaries, one per token, containing features.
    """
    if config is None:
        config = {}
        
    text = document.get('text', '')
    doc_id = document.get('id', 'unknown')
    
    if not text:
        return []
        
    nlp = get_spacy_nlp()
    doc = nlp(text)
    tokenizer = get_tokenizer()
    
    features = []
    
    for i, token in enumerate(doc):
        if token.is_space:
            continue
            
        token_text = token.text
        
        # Handle ambiguous tokens
        if is_ambiguous_token(token_text):
            category = 'neutral'
            entropy = 0.0
            semantic_density = 0.0
        else:
            category = get_token_category(token_text)
            
            # Compute entropy (simplified: uniform distribution for demo, 
            # in real scenario would use model logits)
            # Here we use a placeholder logic or actual calculation if logits were passed
            entropy = 0.0 # Placeholder: actual entropy requires model logits
            
            # Compute local semantic density
            # Get context window (e.g., 2 tokens before and after)
            start_idx = max(0, i - 2)
            end_idx = min(len(doc), i + 3)
            context_tokens = [t.text for t in doc[start_idx:end_idx] if t.text != token_text]
            
            semantic_density = compute_local_semantic_density(token_text, context_tokens)
        
        features.append({
            'document_id': doc_id,
            'token_index': i,
            'token_text': token_text,
            'pos_tag': token.pos_,
            'category': category,
            'entropy': entropy,
            'local_semantic_density': semantic_density,
            'is_ambiguous': is_ambiguous_token(token_text)
        })
        
    return features


def main():
    """
    Main entry point for the feature computation script.
    
    This function demonstrates the validation of the KenLM model availability.
    It attempts to load the model and exits with code 1 if not found.
    """
    logger.info("Starting feature computation validation.")
    
    try:
        # This call will raise FileNotFoundError if model is missing
        model = load_or_download_kenlm()
        logger.info("KenLM model loaded successfully.")
        
        # If we get here, the model exists
        print("KenLM model found and loaded.")
        
    except FileNotFoundError as e:
        logger.error(f"Validation failed: {e}")
        print("KenLM model not found")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()