"""
Tests for the model loader utilities.
"""
import pytest
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.model_loader import get_sentiment_pipeline, get_rosenberg_lexicon, clear_cache

def test_get_rosenberg_lexicon_exists():
    """Test that the lexicon loads successfully and is a set."""
    clear_cache()
    lexicon = get_rosenberg_lexicon()
    assert isinstance(lexicon, set)
    assert len(lexicon) > 0
    # Check for known Rosenberg words
    assert "good" in lexicon
    assert "worthy" in lexicon
    assert "worthless" in lexicon  # Negative word included for reverse scoring
    assert "useless" in lexicon

def test_get_rosenberg_lexicon_caching():
    """Test that the lexicon is cached."""
    clear_cache()
    lexicon1 = get_rosenberg_lexicon()
    lexicon2 = get_rosenberg_lexicon()
    assert lexicon1 is lexicon2

def test_clear_cache():
    """Test that clear_cache resets the singleton."""
    clear_cache()
    lexicon1 = get_rosenberg_lexicon()
    clear_cache()
    lexicon2 = get_rosenberg_lexicon()
    # They should be different instances after clear
    assert lexicon1 is not lexicon2

def test_get_sentiment_pipeline():
    """Test that the sentiment pipeline loads (basic check)."""
    clear_cache()
    pipeline = get_sentiment_pipeline()
    assert pipeline is not None
    # Basic sanity check: pipeline should have a predict method or be callable
    # The actual pipeline object from transformers is callable
    assert callable(pipeline)

def test_sentiment_pipeline_caching():
    """Test that the sentiment pipeline is cached."""
    clear_cache()
    pipe1 = get_sentiment_pipeline()
    pipe2 = get_sentiment_pipeline()
    assert pipe1 is pipe2
