import os
import gc
import logging
import json
import math
from typing import Dict, List, Optional, Any
import re
import unicodedata

import numpy as np
import pandas as pd
import spacy
from transformers import AutoTokenizer
from scipy.stats import entropy as scipy_entropy
from collections import Counter

# Attempt to import kenlm; if missing, the function will raise a clear error
try:
    import kenlm
    KENLM_AVAILABLE = True
except ImportError:
    KENLM_AVAILABLE = False
    logging.warning("kenlm not installed. Perplexity calculations will fail if used.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants for Edge Case Handling ---
# Categories for ambiguous tokens
AMBIGUOUS_CATEGORY_NEUTRAL = "neutral"
AMBIGUOUS_CATEGORY_SPECIAL = "special"
AMBIGUOUS_CATEGORY_EMOJI = "emoji"
AMBIGUOUS_CATEGORY_CONTROL = "control"

# Regex patterns for detection
# Matches emojis (broad range)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+", flags=re.UNICODE
)

# Matches control characters and other non-printable unicode
CONTROL_PATTERN = re.compile(r'[\x00-\x1F\x7F-\x9F]')

# --- Helper Functions for Edge Cases ---

def is_ambiguous_token(token_text: str) -> Dict[str, Any]:
    """
    Analyzes a token to determine if it is ambiguous (special char, emoji, control).
    
    Args:
        token_text: The raw string of the token.
        
    Returns:
        A dictionary with:
            - 'is_ambiguous': bool
            - 'category': str ('special', 'emoji', 'control', or 'neutral')
            - 'normalized': str (optional normalized version if applicable)
    """
    if not token_text or not isinstance(token_text, str):
        return {
            "is_ambiguous": True,
            "category": AMBIGUOUS_CATEGORY_CONTROL,
            "reason": "empty_or_invalid"
        }

    # Check for emojis
    if EMOJI_PATTERN.search(token_text):
        return {
            "is_ambiguous": True,
            "category": AMBIGUOUS_CATEGORY_EMOJI,
            "reason": "contains_emoji"
        }

    # Check for control characters
    if CONTROL_PATTERN.search(token_text):
        return {
            "is_ambiguous": True,
            "category": AMBIGUOUS_CATEGORY_CONTROL,
            "reason": "contains_control_char"
        }

    # Check for pure non-alphanumeric symbols (excluding standard punctuation)
    # This catches things like mathematical operators, dingbats, etc. that aren't emojis
    # but are still "special" in a linguistic context.
    # We define 'special' as: contains no alphanumeric characters
    if not any(c.isalnum() for c in token_text):
        # Exclude standard punctuation if it's a single char (like '.', ',', '!')
        # But if it's a sequence of symbols, it's special.
        if len(token_text) == 1 and token_text in '.,!?;:\'\"()[]{}':
            return {
                "is_ambiguous": False,
                "category": AMBIGUOUS_CATEGORY_NEUTRAL,
                "reason": "standard_punctuation"
            }
        return {
            "is_ambiguous": True,
            "category": AMBIGUOUS_CATEGORY_SPECIAL,
            "reason": "non_alphanumeric"
        }

    return {
        "is_ambiguous": False,
        "category": AMBIGUOUS_CATEGORY_NEUTRAL,
        "reason": "standard_token"
    }

def get_token_category(token_text: str) -> str:
    """
    Convenience wrapper to get the category string for a token.
    Returns 'neutral' for standard tokens, or the specific category for ambiguous ones.
    """
    info = is_ambiguous_token(token_text)
    return info["category"]

# --- Core Feature Extraction Functions ---

def get_spacy_nlp() -> spacy.language.Language:
    """
    Loads the spaCy English model. Caches the model globally to avoid reloading.
    """
    if not hasattr(get_spacy_nlp, "_nlp"):
        logger.info("Loading spaCy en_core_web_sm model...")
        try:
            get_spacy_nlp._nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            raise
    return get_spacy_nlp._nlp

def get_tokenizer() -> AutoTokenizer:
    """
    Loads the Llama-3 tokenizer.
    """
    if not hasattr(get_tokenizer, "_tokenizer"):
        logger.info("Loading Llama-3 tokenizer...")
        try:
            # Using a standard Llama-3 tokenizer path
            get_tokenizer._tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B")
        except Exception as e:
            logger.error(f"Failed to load tokenizer: {e}")
            raise
    return get_tokenizer._tokenizer

def load_or_download_kenlm(model_path: str = "data/config/kenlm.arpa") -> Optional[Any]:
    """
    Loads the KenLM language model.
    If the model file doesn't exist, it attempts to download it (placeholder logic for now).
    Returns the compiled kenlm model object or None if unavailable.
    """
    if not KENLM_AVAILABLE:
        logger.warning("KenLM library not available. Cannot load model.")
        return None

    if not os.path.exists(model_path):
        logger.warning(f"KenLM model file not found at {model_path}. Perplexity features will be skipped.")
        return None

    try:
        model = kenlm.Model(model_path)
        logger.info(f"KenLM model loaded from {model_path}")
        return model
    except Exception as e:
        logger.error(f"Failed to load KenLM model: {e}")
        return None

def compute_entropy(token_context: List[str], window_size: int = 5) -> float:
    """
    Computes the entropy of a token's context distribution.
    For simplicity in this static feature set, we calculate entropy of character frequencies
    within the token itself, or a simple context window if provided.
    
    Args:
        token_context: List of tokens or characters representing the context.
        window_size: Size of the window.
        
    Returns:
        Entropy value (float).
    """
    if not token_context:
        return 0.0
    
    # Flatten context if it's a list of lists (unlikely but safe)
    flat_context = [c for item in token_context for c in str(item)]
    
    if not flat_context:
        return 0.0

    counts = Counter(flat_context)
    total = sum(counts.values())
    probs = [count / total for count in counts.values()]
    
    # Avoid log(0)
    probs = [p for p in probs if p > 0]
    if not probs:
        return 0.0
        
    return scipy_entropy(probs)

def compute_kenlm_perplexity(token_text: str, kenlm_model: Optional[Any]) -> float:
    """
    Computes perplexity using the KenLM model.
    
    Args:
        token_text: The text string to evaluate.
        kenlm_model: The loaded KenLM model object.
        
    Returns:
        Perplexity value (float), or float('inf') if model is unavailable.
    """
    if not kenlm_model:
        return float('inf')
    
    if not token_text or not isinstance(token_text, str):
        return float('inf')
        
    try:
        # KenLM expects a sentence. We wrap the token in a sentence structure.
        score = kenlm_model.score(token_text)
        # Perplexity = exp(-score / N) where N is number of tokens/chars
        # KenLM.score returns log10 probability usually, or we can use log_prob
        # Standard formula: PPL = exp(-1/N * sum(log P(w_i)))
        # The kenlm library .score() returns log10 probability of the sentence.
        # We need to convert to natural log for standard perplexity or use base 10.
        # Let's assume standard perplexity (base e).
        # score is log10(P). So P = 10^score.
        # -log(P) = -score * ln(10).
        # Perplexity = exp(-log(P) / N) = exp(-score * ln(10) / N) = 10^(-score/N)
        
        # Approximate N as length of token text
        n = len(token_text)
        if n == 0:
            return float('inf')
            
        ppl = 10 ** (-score / n)
        return ppl
    except Exception as e:
        logger.warning(f"KenLM score calculation failed for token '{token_text}': {e}")
        return float('inf')

def compute_local_semantic_density(tokens: List[str], center_idx: int, window_size: int = 3) -> float:
    """
    Calculates the density of unique 3-grams (n=3) within a sliding window around the target token.
    
    Definition:
    - Extract a window of tokens around center_idx.
    - Generate all 3-grams in that window.
    - Calculate density = (unique n-grams) / (total n-grams).
    
    Args:
        tokens: Full list of tokens in the document.
        center_idx: Index of the target token.
        window_size: Radius of the window (total window size = 2 * window_size + 1).
        
    Returns:
        Density value between 0.0 and 1.0.
    """
    start = max(0, center_idx - window_size)
    end = min(len(tokens), center_idx + window_size + 1)
    window_tokens = tokens[start:end]
    
    if len(window_tokens) < 3:
        # Not enough tokens to form a trigram
        return 0.0
    
    trigrams = []
    for i in range(len(window_tokens) - 2):
        trigram = tuple(window_tokens[i:i+3])
        trigrams.append(trigram)
    
    if not trigrams:
        return 0.0
        
    unique_trigrams = set(trigrams)
    density = len(unique_trigrams) / len(trigrams)
    
    return density

def process_document(doc_data: Dict[str, Any], spacy_nlp: Optional[spacy.language.Language] = None, 
                     kenlm_model: Optional[Any] = None, tokenizer: Optional[AutoTokenizer] = None) -> List[Dict[str, Any]]:
    """
    Processes a single document to extract features for every token.
    
    Args:
        doc_data: Dictionary containing 'id', 'text', and optionally 'rtpurbo_labels'.
        spacy_nlp: Loaded spaCy model.
        kenlm_model: Loaded KenLM model.
        tokenizer: Loaded tokenizer.
        
    Returns:
        List of dictionaries, one per token, containing:
            - token_id
            - text
            - pos
            - entropy
            - kenlm_perplexity
            - is_ambiguous
            - ambiguity_category
            - local_semantic_density
            - rtpurbo_label (if available)
    """
    if not spacy_nlp:
        spacy_nlp = get_spacy_nlp()
    if not tokenizer:
        tokenizer = get_tokenizer()
        
    doc_id = doc_data.get('id', 'unknown')
    text = doc_data.get('text', '')
    rtpurbo_labels = doc_data.get('rtpurbo_labels', [None] * len(text)) # Fallback if labels missing
    
    if not text:
        logger.warning(f"Empty text for document {doc_id}. Skipping.")
        return []
        
    # Run spaCy
    doc = spacy_nlp(text)
    tokens = [token.text for token in doc]
    pos_tags = [token.pos_ for token in doc]
    
    # Tokenize with Llama tokenizer to align if necessary, 
    # but for now we assume spaCy tokens align with the feature extraction logic.
    # If alignment is needed, we would map spaCy tokens to subwords.
    # For this task, we process token-by-token as defined by spaCy.
    
    results = []
    total_tokens = len(tokens)
    
    for i, token in enumerate(tokens):
        # Edge Case Handling
        ambiguity_info = is_ambiguous_token(token)
        
        # Compute Features
        # 1. Entropy (character level of token)
        entropy_val = compute_entropy(list(token))
        
        # 2. KenLM Perplexity
        ppl_val = compute_kenlm_perplexity(token, kenlm_model)
        
        # 3. Local Semantic Density
        density_val = compute_local_semantic_density(tokens, i, window_size=3)
        
        # 4. Position
        position = i
        
        # 5. POS Tag
        pos_tag = pos_tags[i]
        
        # 6. RTPurbo Label (if available)
        # We assume rtpurbo_labels is a list of booleans or 0/1 aligned with tokens
        label = None
        if rtpurbo_labels and i < len(rtpurbo_labels):
            label = rtpurbo_labels[i]
        
        row = {
            "document_id": doc_id,
            "token_index": i,
            "text": token,
            "pos": pos_tag,
            "entropy": entropy_val,
            "kenlm_perplexity": ppl_val,
            "is_ambiguous": ambiguity_info["is_ambiguous"],
            "ambiguity_category": ambiguity_info["category"],
            "local_semantic_density": density_val,
            "position": position,
            "rtpurbo_label": label
        }
        results.append(row)
        
    return results

def main():
    """
    Main entry point for the feature computation pipeline.
    This function is intended to be called by the downstream T013 task.
    It expects input data to be available (e.g., from T012) and processes it.
    
    For T015, the primary requirement is ensuring that `is_ambiguous_token`
    and the processing pipeline handle special characters and emojis without crashing.
    """
    logger.info("Starting Feature Computation Pipeline (T013/T015).")
    
    # Example test case to verify edge case handling without full pipeline
    test_tokens = [
        "Hello",
        "world",
        "!",
        "🚀",
        "test@domain.com",
        "normal",
        "\x00", # Control char
        "café",
        "..."
    ]
    
    logger.info("Running edge case verification tests...")
    for token in test_tokens:
        try:
            info = is_ambiguous_token(token)
            logger.info(f"Token: '{token}' -> Ambiguous: {info['is_ambiguous']}, Category: {info['category']}")
        except Exception as e:
            logger.error(f"CRASH on token '{token}': {e}")
            raise
    
    logger.info("Edge case verification passed. No crashes detected.")
    
    # In a real execution, this would load data from T012 (anomalies filtered)
    # and process the full dataset.
    # For now, we log that the pipeline is ready for T013.
    logger.info("Pipeline ready to process RULER dataset with edge case handling.")

if __name__ == "__main__":
    main()
