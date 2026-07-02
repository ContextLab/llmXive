"""
Tests for T007a: Annotate Corpus.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# We cannot easily test the full pipeline without real data,
# but we can test the helper functions if we import them,
# or test the structure of the output if we mock the data loading.

from code.data.annotate_corpus import get_vader_label, get_textblob_label, sample_comments

def test_vader_positive():
    result = get_vader_label("This is absolutely fantastic!")
    assert result["label"] == "positive"
    assert result["score"] >= 0.05

def test_vader_negative():
    result = get_vader_label("This is terrible and awful.")
    assert result["label"] == "negative"
    assert result["score"] <= -0.05

def test_vader_neutral():
    result = get_vader_label("The sky is blue.")
    assert result["label"] == "neutral"
    assert -0.05 < result["score"] < 0.05

def test_textblob_positive():
    result = get_textblob_label("I love this project!")
    assert result["label"] == "positive"

def test_sample_comments():
    # Create a mock dataframe
    data = {
        "text": ["Good", "Bad", "Okay", "Great", "Terrible"],
        "comment_id": [1, 2, 3, 4, 5]
    }
    df = pd.DataFrame(data)
    
    # Sample 3 items
    sampled = sample_comments(df, sample_size=3)
    
    assert len(sampled) == 3
    assert "text" in sampled.columns
    assert "comment_id" in sampled.columns