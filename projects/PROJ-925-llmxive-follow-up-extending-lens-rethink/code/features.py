"""
code/features.py

Implements linguistic and syntactic feature extraction for image captions.
Includes individual feature functions and a batch extraction pipeline with
robust edge case handling (short captions, BERT failures, timeouts).
"""
import math
import logging
import time
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import spacy
from transformers import AutoTokenizer, AutoModel
from dataclasses import dataclass

# Project imports
from config import get_project_root, get_config
from utils.logging import get_logger
from utils.errors import ModelInferenceError

# Constants
BERT_MODEL_NAME = "bert-base-uncased"
TIMEOUT_SECONDS = 5.0
MIN_CAPTION_LENGTH = 3  # Minimum words to consider a caption valid for syntactic depth

# Global cache for models to avoid reloading
_BERT_TOKENIZER = None
_BERT_MODEL = None
_SPACY_NLP = None

logger = get_logger(__name__)


def _get_bert_models() -> Tuple[Any, Any]:
    """
    Lazy initialization of BERT tokenizer and model.
    Returns (tokenizer, model) tuple.
    """
    global _BERT_TOKENIZER, _BERT_MODEL

    if _BERT_TOKENIZER is None:
        logger.info(f"Loading BERT tokenizer: {BERT_MODEL_NAME}")
        _BERT_TOKENIZER = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
    
    if _BERT_MODEL is None:
        logger.info(f"Loading BERT model: {BERT_MODEL_NAME}")
        # Explicitly set to evaluation mode and CPU
        _BERT_MODEL = AutoModel.from_pretrained(BERT_MODEL_NAME)
        _BERT_MODEL.eval()
        # Ensure CPU usage as per project constraints
        if torch.cuda.is_available():
            logger.warning("CUDA available but forcing CPU usage per project constraints.")
        _BERT_MODEL.to("cpu")
        
    return _BERT_TOKENIZER, _BERT_MODEL


def _get_spacy_nlp() -> Any:
    """
    Lazy initialization of spaCy English model.
    """
    global _SPACY_NLP
    
    if _SPACY_NLP is None:
        logger.info("Loading spaCy 'en_core_web_sm' model")
        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy 'en_core_web_sm' model not found. Please run: python -m spacy download en_core_web_sm")
            raise
    return _SPACY_NLP


def compute_linguistic_uncertainty_proxy(caption: str) -> float:
    """
    Computes the linguistic uncertainty proxy using BERT perplexity.
    
    Logic:
    1. Tokenize caption.
    2. Run BERT inference to get hidden states.
    3. Compute next-token prediction probabilities (simplified via language modeling head logic or hidden state norms if head unavailable).
       *Note: Since we are using base BERT (encoder only) without the LM head, we approximate perplexity 
       using the entropy of the hidden state representations or a proxy based on reconstruction error if a head is not loaded.
       However, standard practice for 'BERT perplexity' usually implies a masked LM setup. 
       Given the constraint to use 'bert-base-uncased' (encoder), we will use the masked LM head if available via AutoModelForMaskedLM,
       or fallback to a proxy if strictly restricted to AutoModel.
       *Correction per FR-001*: The task asks for perplexity. We must use a model capable of LM. 
       We will switch to 'bert-base-uncased' via AutoModelForMaskedLM to get valid perplexity.
    4. Apply natural logarithm: ln(perplexity).
    
    Args:
        caption: The input caption string.
        
    Returns:
        float: ln(perplexity).
        
    Raises:
        ModelInferenceError: If BERT inference fails (timeout or model error).
    """
    # Re-implementing to ensure we use MaskedLM for valid perplexity
    # We need to reload the model type for this specific function if we want strict LM
    # But to keep global cache efficient, we'll check if we have an LM model.
    # For simplicity and strict adherence to "bert-base-uncased", we will use AutoModelForMaskedLM here.
    
    tokenizer = None
    model = None
    
    # Initialize LM specific models if needed (separate from encoder cache to avoid type mismatch)
    # We use a module-level cache for the LM model too to avoid reloading
    global _BERT_LM_MODEL, _BERT_LM_TOKENIZER
    
    if '_BERT_LM_MODEL' not in globals() or _BERT_LM_MODEL is None:
        logger.debug("Initializing BERT MaskedLM model for perplexity")
        _BERT_LM_TOKENIZER = AutoTokenizer.from_pretrained(BERT_MODEL_NAME)
        _BERT_LM_MODEL = AutoModelForMaskedLM.from_pretrained(BERT_MODEL_NAME)
        _BERT_LM_MODEL.eval()
        _BERT_LM_MODEL.to("cpu")
    
    tokenizer = _BERT_LM_TOKENIZER
    model = _BERT_LM_MODEL

    start_time = time.time()
    
    try:
        # Tokenize
        inputs = tokenizer(caption, return_tensors="pt", truncation=True, padding=True)
        
        # Timeout check for tokenization (unlikely to exceed, but for safety)
        if time.time() - start_time > TIMEOUT_SECONDS:
            raise TimeoutError("Tokenization exceeded timeout")

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits

        # Calculate perplexity
        # Shift logits to align with labels (next token prediction)
        # For a simple caption, we can compute the cross-entropy loss against the input IDs (shifted)
        # Perplexity = exp(CE)
        
        # Shift inputs and logits for next token prediction
        # inputs.input_ids shape: (batch, seq_len)
        # logits shape: (batch, seq_len, vocab)
        
        # We calculate the probability of the actual next token
        # Label for position i is input_ids[i+1]
        
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = inputs.input_ids[..., 1:].contiguous()
        
        # Flatten for loss calculation
        flat_logits = shift_logits.view(-1, shift_logits.size(-1))
        flat_labels = shift_labels.view(-1)
        
        # Compute cross entropy
        loss_fct = torch.nn.CrossEntropyLoss(reduction='mean')
        loss = loss_fct(flat_logits, flat_labels)
        
        perplexity = torch.exp(loss).item()
        
        # Apply natural log as per FR-001
        ln_perplexity = math.log(perplexity)
        
        elapsed = time.time() - start_time
        if elapsed > TIMEOUT_SECONDS:
            logger.warning(f"Caption processing exceeded timeout ({elapsed:.2f}s). Excluding.")
            raise TimeoutError("Inference exceeded timeout")
            
        return ln_perplexity

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"BERT inference failed for caption (len={len(caption)}): {e} (Time: {elapsed:.2f}s)")
        raise ModelInferenceError(f"BERT inference failure: {str(e)}")


def compute_syntactic_depth(caption: str) -> int:
    """
    Computes the syntactic depth of a caption using spaCy dependency tree.
    
    Logic:
    1. Parse caption with spaCy.
    2. Calculate the maximum depth of the dependency tree.
    3. If the caption is too short (e.g., single word), exclude it.
    
    Args:
        caption: The input caption string.
        
    Returns:
        int: The depth of the dependency tree.
        
    Raises:
        ValueError: If the caption is too short to compute meaningful depth.
    """
    nlp = _get_spacy_nlp()
    doc = nlp(caption)
    
    # Check for minimum length
    tokens = [token for token in doc if not token.is_space]
    if len(tokens) < MIN_CAPTION_LENGTH:
        raise ValueError(f"Citation too short (len={len(tokens)}) to compute syntactic depth.")
    
    # Calculate max depth
    def get_depth(token):
        if not list(token.children):
            return 1
        return 1 + max(get_depth(child) for child in token.children)
    
    # Find the root
    root = None
    for token in doc:
        if token.head == token:
            root = token
            break
    
    if root is None:
        # Fallback if no explicit root found (shouldn't happen in valid text)
        raise ValueError("Could not identify dependency tree root.")
        
    depth = get_depth(root)
    return depth


def compute_noun_phrase_density(caption: str) -> float:
    """
    Computes the density of noun phrases in a caption.
    
    Logic:
    1. Parse caption with spaCy.
    2. Count noun phrases (chunks).
    3. Divide by total number of tokens.
    
    Args:
        caption: The input caption string.
        
    Returns:
        float: Noun phrase density.
    """
    nlp = _get_spacy_nlp()
    doc = nlp(caption)
    
    total_tokens = len([t for t in doc if not t.is_space])
    if total_tokens == 0:
        return 0.0
        
    noun_phrases = list(doc.noun_chunks)
    density = len(noun_phrases) / total_tokens
    return density


def compute_token_diversity(caption: str) -> float:
    """
    Computes the token diversity (Type-Token Ratio) of a caption.
    
    Logic:
    1. Tokenize caption (lowercased).
    2. Count unique tokens (types) and total tokens (tokens).
    3. Return TTR = types / tokens.
    
    Args:
        caption: The input caption string.
        
    Returns:
        float: Token diversity ratio.
    """
    # Simple tokenization: split by whitespace and lowercase
    tokens = caption.lower().split()
    tokens = [t.strip(".,!?;:'\"()[]") for t in tokens] # Basic cleanup
    tokens = [t for t in tokens if t] # Remove empty strings
    
    if len(tokens) == 0:
        return 0.0
        
    unique_tokens = set(tokens)
    diversity = len(unique_tokens) / len(tokens)
    return diversity


def extract_features_batch(captions: List[str]) -> pd.DataFrame:
    """
    Extracts all features for a batch of captions.
    
    Logic:
    1. Iterate through captions.
    2. For each caption, attempt to compute all features.
    3. Handle exceptions:
       - Short captions: Exclude, log exclusion reason 'SHORT_CAPTION'.
       - BERT failure: Exclude, log exclusion reason 'BERT_FAILURE'.
       - Timeout: Exclude, log exclusion reason 'TIMEOUT_EXCEEDED'.
    4. Return a DataFrame with valid rows only.
    
    Args:
        captions: List of caption strings.
        
    Returns:
        pd.DataFrame: DataFrame containing extracted features.
    """
    results = []
    excluded_reasons = {
        'SHORT_CAPTION': 0,
        'BERT_FAILURE': 0,
        'TIMEOUT_EXCEEDED': 0,
        'OTHER': 0
    }
    
    logger.info(f"Starting batch feature extraction for {len(captions)} captions.")
    
    for i, caption in enumerate(captions):
        row = {
            'caption_id': i,
            'caption_text': caption,
            'linguistic_uncertainty': None,
            'syntactic_depth': None,
            'noun_phrase_density': None,
            'token_diversity': None
        }
        
        try:
            # 1. Syntactic Depth (checks length internally)
            row['syntactic_depth'] = compute_syntactic_depth(caption)
            
            # 2. Noun Phrase Density
            row['noun_phrase_density'] = compute_noun_phrase_density(caption)
            
            # 3. Token Diversity
            row['token_diversity'] = compute_token_diversity(caption)
            
            # 4. Linguistic Uncertainty (BERT)
            row['linguistic_uncertainty'] = compute_linguistic_uncertainty_proxy(caption)
            
            results.append(row)
            
        except ValueError as ve:
            # Likely short caption
            if "too short" in str(ve).lower():
                reason = 'SHORT_CAPTION'
            else:
                reason = 'OTHER'
            excluded_reasons[reason] += 1
            logger.warning(f"Excluding caption {i} (len={len(caption)}): {reason} - {ve}")
            
        except TimeoutError:
            excluded_reasons['TIMEOUT_EXCEEDED'] += 1
            logger.warning(f"Excluding caption {i} (len={len(caption)}): TIMEOUT_EXCEEDED")
            
        except ModelInferenceError:
            excluded_reasons['BERT_FAILURE'] += 1
            logger.warning(f"Excluding caption {i} (len={len(caption)}): BERT_FAILURE")
            
        except Exception as e:
            excluded_reasons['OTHER'] += 1
            logger.error(f"Unexpected error processing caption {i}: {e}")
            
    logger.info(f"Batch extraction complete. Processed: {len(results)}, Excluded: {len(captions) - len(results)}")
    logger.info(f"Exclusion breakdown: {excluded_reasons}")
    
    return pd.DataFrame(results)