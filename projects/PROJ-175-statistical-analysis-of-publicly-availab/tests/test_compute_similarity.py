import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the module functions
from code.data.compute_similarity import (
    load_ingredient_pairs,
    load_embeddings,
    compute_cosine_similarity,
    process_similarity,
    save_output
)

def test_compute_cosine_similarity_identical():
    vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    sim = compute_cosine_similarity(vec, vec)
    assert np.isclose(sim, 1.0, atol=1e-5)

def test_compute_cosine_similarity_orthogonal():
    vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, 0.0, atol=1e-5)

def test_compute_cosine_similarity_opposite():
    vec1 = np.array([1.0, 0.0], dtype=np.float32)
    vec2 = np.array([-1.0, 0.0], dtype=np.float32)
    sim = compute_cosine_similarity(vec1, vec2)
    assert np.isclose(sim, -1.0, atol=1e-5)

def test_compute_cosine_similarity_zero_norm():
    vec1 = np.array([0.0, 0.0], dtype=np.float32)
    vec2 = np.array([1.0, 1.0], dtype=np.float32)
    sim = compute_cosine_similarity(vec1, vec2)
    assert sim == 0.0

def test_load_embeddings(tmp_path):
    # Create a dummy embeddings parquet
    data = {
        'ingredient_id': ['A', 'B'],
        'embedding': [np.array([1.0, 0.0]), np.array([0.0, 1.0])]
    }
    df = pd.DataFrame(data)
    path = tmp_path / "emb.parquet"
    df.to_parquet(path)

    emb_dict = load_embeddings(str(path))
    assert 'A' in emb_dict
    assert 'B' in emb_dict
    assert np.array_equal(emb_dict['A'], np.array([1.0, 0.0]))

def test_process_similarity():
    # Mock pairs
    pairs_df = pd.DataFrame([
        {'ingredient_id_1': 'A', 'ingredient_id_2': 'B'},
        {'ingredient_id_1': 'B', 'ingredient_id_2': 'C'}
    ])
    # Mock embeddings
    embeddings = {
        'A': np.array([1.0, 0.0], dtype=np.float32),
        'B': np.array([0.0, 1.0], dtype=np.float32),
        'C': np.array([1.0, 0.0], dtype=np.float32)
    }

    result = process_similarity(pairs_df, embeddings)

    assert len(result) == 2
    assert 'similarity_score' in result.columns
    # A and B are orthogonal -> 0
    assert result.iloc[0]['similarity_score'] == 0.0
    # B and C are orthogonal -> 0
    assert result.iloc[1]['similarity_score'] == 0.0

def test_process_similarity_missing_embeddings():
    pairs_df = pd.DataFrame([
        {'ingredient_id_1': 'A', 'ingredient_id_2': 'B'}
    ])
    embeddings = {
        'A': np.array([1.0, 0.0], dtype=np.float32)
        # B is missing
    }
    result = process_similarity(pairs_df, embeddings)
    assert len(result) == 0  # Should skip missing

def test_save_output(tmp_path):
    df = pd.DataFrame([
        {'ingredient_id_1': 'A', 'ingredient_id_2': 'B', 'similarity_score': 0.5}
    ])
    output_path = tmp_path / "output.parquet"
    save_output(df, str(output_path))
    assert output_path.exists()
    loaded = pd.read_parquet(output_path)
    assert len(loaded) == 1
    assert 'similarity_score' in loaded.columns
