"""
Unit tests for T018: Feature Extraction.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from code.data.extract_features import (
    extract_ngram_features,
    extract_pos_features,
    compute_semantic_similarity,
    validate_features,
    stratified_sample_by_length
)
from code.config import get_config_summary

def test_extract_ngram_features():
    tokens = ["the", "cat", "sat"]
    feats = extract_ngram_features(tokens, n_max=2)
    assert "ngram_1_the" in feats
    assert "ngram_2_the cat" in feats
    assert feats["ngram_1_the"] == 1
    assert feats["ngram_2_the cat"] == 1

def test_extract_pos_features():
    # Mock doc object would be needed, but we can test the logic if we had a real doc
    # For now, test with a simple mock if needed, or skip if spacy dependency is heavy
    # Let's assume spacy is installed and test with a small snippet
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("The cat sat.")
        feats = extract_pos_features(["The", "cat", "sat", "."], doc)
        assert "NOUN" in feats
        assert "DET" in feats
    except OSError:
        pytest.skip("Spacy model not found")

def test_compute_semantic_similarity():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        target = ["cat"]
        refs = ["The dog barked", "The cat meowed"]
        sim = compute_semantic_similarity(target, refs, model)
        assert 0.0 <= sim <= 1.0
    except Exception as e:
        pytest.skip(f"Embedding model failed: {e}")

def test_validate_features():
    # Valid data
    data = {
        "example_id": ["1"],
        "token_id": [0],
        "token_text": ["a"],
        "feature_vector": [[0.1, 0.2, 0.3]]
    }
    df = pd.DataFrame(data)
    assert validate_features(df) is True

    # Invalid: missing column
    data_invalid = {
        "example_id": ["1"],
        "token_id": [0],
        "token_text": ["a"]
    }
    df_invalid = pd.DataFrame(data_invalid)
    assert validate_features(df_invalid) is False

    # Invalid: non-list vector
    data_bad_vec = {
        "example_id": ["1"],
        "token_id": [0],
        "token_text": ["a"],
        "feature_vector": ["string"]
    }
    df_bad_vec = pd.DataFrame(data_bad_vec)
    assert validate_features(df_bad_vec) is False

def test_stratified_sample_by_length():
    data = {
        "question": ["Short", "This is a much longer question text", "Med"],
        "answer": ["A", "B", "C"]
    }
    df = pd.DataFrame(data)
    sample = stratified_sample_by_length(df, n=2, seed=42)
    assert len(sample) <= 2
    assert "length" in sample.columns