"""
Model loading utilities for sentiment analysis and lexicons.
"""
import os
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from threading import Lock
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

from utils.config import DATA_RAW_DIR

# Global cache for models
_sentiment_pipeline = None
_rosenberg_lexicon = None
_lock = Lock()

def get_sentiment_pipeline():
    """
    Loads the RoBERTa sentiment model (CPU-optimized) and returns the pipeline.
    Caches the model in memory.
    """
    global _sentiment_pipeline
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline

    with _lock:
        if _sentiment_pipeline is not None:
            return _sentiment_pipeline

        # Load a CPU-friendly sentiment model
        # Using a standard distilled model for speed
        model_name = "cardiffnlp/twitter-roberta-base-sentiment"
        # Note: This model outputs NEGATIVE, NEUTRAL, POSITIVE.
        # We map NEGATIVE -> -1, POSITIVE -> 1, NEUTRAL -> 0 (or handle as needed)
        
        try:
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                device=-1, # Force CPU
                torch_dtype=torch.float32
            )
        except Exception as e:
            # Fallback to a simpler model if the above fails
            _sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1
            )
        
        return _sentiment_pipeline

def get_rosenberg_lexicon() -> Set[str]:
    """
    Loads the Rosenberg self-esteem lexicon from data/raw/lexicons/rosenberg_words.txt.
    Caches the set in memory.
    """
    global _rosenberg_lexicon
    if _rosenberg_lexicon is not None:
        return _rosenberg_lexicon

    with _lock:
        if _rosenberg_lexicon is not None:
            return _rosenberg_lexicon

    lexicon_path = DATA_RAW_DIR / "lexicons" / "rosenberg_words.txt"
    if not lexicon_path.exists():
        raise FileNotFoundError(f"Lexicon file not found: {lexicon_path}")

    _rosenberg_lexicon = set()
    with open(lexicon_path, "r", encoding="utf-8") as f:
        for line in f:
            word = line.strip().lower()
            if word and not word.startswith("#"):
                _rosenberg_lexicon.add(word)

    return _rosenberg_lexicon

def clear_cache():
    """Clears the model cache."""
    global _sentiment_pipeline, _rosenberg_lexicon
    _sentiment_pipeline = None
    _rosenberg_lexicon = None
