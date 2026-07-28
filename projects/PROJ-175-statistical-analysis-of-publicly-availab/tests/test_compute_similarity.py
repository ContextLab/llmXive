import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'code'))

from data.compute_similarity import compute_cosine_similarity, load_embeddings, load_ingredient_pairs

def test_cosine_similarity_identical_vectors():
    vec1 = np.array([1.0, 2.0, 3.0])
    vec2 = np.array([1.0, 2.0, 3.0])
    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, 1.0), f"Expected 1.0, got {sim}"

def test_cosine_similarity_opposite_vectors():
    vec1 = np.array([1.0, 2.0, 3.0])
    vec2 = np.array([-1.0, -2.0, -3.0])
    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, -1.0), f"Expected -1.0, got {sim}"

def test_cosine_similarity_orthogonal_vectors():
    vec1 = np.array([1.0, 0.0, 0.0])
    vec2 = np.array([0.0, 1.0, 0.0])
    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, 0.0), f"Expected 0.0, got {sim}"

def test_cosine_similarity_zero_vector():
    vec1 = np.array([0.0, 0.0, 0.0])
    vec2 = np.array([1.0, 2.0, 3.0])
    sim = compute_cosine_similarity(vec1, vec2)
    assert sim == 0.0, f"Expected 0.0 for zero vector, got {sim}"

def test_load_embeddings_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_embeddings(str(tmp_path / "nonexistent.parquet"))

def test_load_ingredient_pairs_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_ingredient_pairs(str(tmp_path / "nonexistent.parquet"))
