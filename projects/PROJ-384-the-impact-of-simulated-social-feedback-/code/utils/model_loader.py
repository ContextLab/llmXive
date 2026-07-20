"""
Model loader module for initializing the RoBERTa sentiment model and Rosenberg lexicon.

This module provides singleton-style caching for:
1. A CPU-optimized RoBERTa sentiment analysis pipeline (via Hugging Face transformers)
2. The Rosenberg self-esteem lexicon loaded from a text file

The models and lexicons are loaded once and cached in memory to avoid reloading
during repeated calls.
"""
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from threading import Lock

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Import project paths from config
from .config import DATA_RAW_DIR

# Global cache variables
_sentiment_pipeline: Optional[Any] = None
_rosenberg_lexicon: Optional[Set[str]] = None
_cache_lock = Lock()

# Model configuration
SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment"
LEXICON_FILENAME = "rosenberg_words.txt"

def get_sentiment_pipeline() -> Any:
    """
    Initialize and return the RoBERTa sentiment analysis pipeline.
    
    The pipeline is cached in memory after the first initialization.
    Uses CPU-optimized settings as required by the project constraints.
    
    Returns:
        A Hugging Face pipeline for sentiment analysis.
        
    Raises:
        RuntimeError: If the model fails to load.
    """
    global _sentiment_pipeline
    
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline
    
    with _cache_lock:
        # Double-check after acquiring lock
        if _sentiment_pipeline is not None:
            return _sentiment_pipeline
        
        try:
            # Ensure CPU-only usage as per project requirements
            device = 0 if torch.cuda.is_available() else -1
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(
                SENTIMENT_MODEL_NAME,
                trust_remote_code=True
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                SENTIMENT_MODEL_NAME,
                trust_remote_code=True
            )
            
            # Create the pipeline with CPU optimization
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=device,
                truncation=True,
                max_length=512
            )
            
            return _sentiment_pipeline
            
        except Exception as e:
            raise RuntimeError(f"Failed to load sentiment model: {e}")

def get_rosenberg_lexicon() -> Set[str]:
    """
    Load and return the Rosenberg self-esteem lexicon.
    
    The lexicon is loaded from 'data/raw/lexicons/rosenberg_words.txt'
    and cached in memory. Words are normalized to lowercase.
    
    Returns:
        A set of lowercase Rosenberg lexicon words.
        
    Raises:
        FileNotFoundError: If the lexicon file does not exist.
        RuntimeError: If the lexicon fails to load.
    """
    global _rosenberg_lexicon
    
    if _rosenberg_lexicon is not None:
        return _rosenberg_lexicon
    
    with _cache_lock:
        # Double-check after acquiring lock
        if _rosenberg_lexicon is not None:
            return _rosenberg_lexicon
        
        lexicon_path = DATA_RAW_DIR / "lexicons" / LEXICON_FILENAME
        
        if not lexicon_path.exists():
            raise FileNotFoundError(
                f"Rosenberg lexicon not found at {lexicon_path}. "
                f"Please ensure the file exists in the data/raw/lexicons directory."
            )
        
        try:
            with open(lexicon_path, 'r', encoding='utf-8') as f:
                # Read lines, strip whitespace, filter empty lines, convert to lowercase
                words = set(
                    line.strip().lower() 
                    for line in f 
                    if line.strip() and not line.startswith('#')
                )
            
            if not words:
                raise ValueError("Rosenberg lexicon file is empty or contains no valid words.")
            
            _rosenberg_lexicon = words
            return _rosenberg_lexicon
            
        except Exception as e:
            raise RuntimeError(f"Failed to load Rosenberg lexicon: {e}")

def clear_cache() -> None:
    """
    Clear the cached models and lexicons.
    
    Useful for testing or when memory needs to be freed.
    """
    global _sentiment_pipeline, _rosenberg_lexicon
    with _cache_lock:
        _sentiment_pipeline = None
        _rosenberg_lexicon = None
