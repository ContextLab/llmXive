import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data.embeddings import (
    load_ingredient_list,
    compute_cosine_similarity_matrix,
    aggregate_embeddings,
    fetch_embeddings_for_ingredients
)

@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

@pytest.fixture
def sample_ingredients(temp_dir):
    data = {
        'ingredient_id': ['1', '2', '3'],
        'canonical_name': ['salt', 'sugar', 'pepper'],
        'frequency': [100, 90, 80]
    }
    path = temp_dir / "test_ingredients.csv"
    pd.DataFrame(data).to_csv(path, index=False)
    return path

def test_load_ingredient_list(sample_ingredients):
    df = load_ingredient_list(sample_ingredients)
    assert len(df) == 3
    assert 'canonical_name' in df.columns
    assert 'salt' in df['canonical_name'].values

def test_aggregate_embeddings():
    ingredients = pd.DataFrame({
        'ingredient_id': ['1'],
        'canonical_name': ['test'],
        'frequency': [1]
    })
    embeddings = np.array([[0.1, 0.2, 0.3]])
    result = aggregate_embeddings(ingredients, embeddings)
    assert 'embedding_vector' in result.columns
    assert result['embedding_vector'].iloc[0] == [0.1, 0.2, 0.3]

def test_compute_cosine_similarity_matrix():
    df = pd.DataFrame({
        'ingredient_id': ['A', 'B'],
        'embedding_vector': [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    })
    sim_df = compute_cosine_similarity_matrix(df)
    assert len(sim_df) == 1
    # A and B are orthogonal, similarity should be 0
    assert abs(sim_df['similarity_score'].iloc[0]) < 1e-5

def test_compute_cosine_similarity_identical():
    df = pd.DataFrame({
        'ingredient_id': ['A', 'B'],
        'embedding_vector': [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    })
    sim_df = compute_cosine_similarity_matrix(df)
    assert abs(sim_df['similarity_score'].iloc[0] - 1.0) < 1e-5
