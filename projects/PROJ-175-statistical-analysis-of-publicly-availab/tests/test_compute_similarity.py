import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.compute_similarity import (
    load_ingredient_pairs,
    load_embeddings,
    compute_cosine_similarity,
    process_similarity,
    save_output
)

@pytest.fixture
def sample_ingredients():
    return pd.DataFrame({
        'ingredient_id': ['salt', 'pepper', 'garlic'],
        'normalized_name': ['salt', 'pepper', 'garlic'],
        'frequency': [100, 90, 80]
    })

@pytest.fixture
def sample_embeddings():
    # Create simple vectors for testing
    # salt: [1, 0, 0]
    # pepper: [0, 1, 0]
    # garlic: [1, 1, 0]
    return pd.DataFrame({
        'ingredient_id': ['salt', 'pepper', 'garlic'],
        'vector': [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0]
        ]
    })

def test_compute_cosine_similarity():
    # Orthogonal vectors
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.0, 1.0, 0.0])
    assert compute_cosine_similarity(v1, v2) == pytest.approx(0.0, abs=1e-5)

    # Identical vectors
    v3 = np.array([1.0, 0.0, 0.0])
    assert compute_cosine_similarity(v1, v3) == pytest.approx(1.0, abs=1e-5)

    # Opposite vectors
    v4 = np.array([-1.0, 0.0, 0.0])
    assert compute_cosine_similarity(v1, v4) == pytest.approx(-1.0, abs=1e-5)

    # Zero vector handling
    v_zero = np.array([0.0, 0.0, 0.0])
    assert compute_cosine_similarity(v1, v_zero) == pytest.approx(0.0, abs=1e-5)

def test_load_embeddings_missing_file():
    with pytest.raises(FileNotFoundError):
        load_embeddings("non_existent_path.parquet")

def test_load_embeddings_invalid_schema(sample_embeddings, tmp_path):
    # Create a file with wrong schema
    wrong_df = pd.DataFrame({'id': ['a'], 'vec': [[1]]})
    wrong_path = tmp_path / "wrong.parquet"
    wrong_df.to_parquet(wrong_path)
    
    with pytest.raises(ValueError) as exc_info:
        load_embeddings(str(wrong_path))
    assert "missing required columns" in str(exc_info.value)

def test_process_similarity(sample_ingredients, sample_embeddings, tmp_path):
    result = process_similarity(sample_ingredients, sample_embeddings)
    
    assert 'ingredient_id_1' in result.columns
    assert 'ingredient_id_2' in result.columns
    assert 'similarity' in result.columns
    
    # We expect 3 pairs: (salt, pepper), (salt, garlic), (pepper, garlic)
    assert len(result) == 3
    
    # Check specific values
    salt_pepper = result[(result['ingredient_id_1'] == 'salt') & (result['ingredient_id_2'] == 'pepper')]
    assert len(salt_pepper) == 1
    assert salt_pepper['similarity'].iloc[0] == pytest.approx(0.0, abs=1e-5)

def test_save_output(sample_ingredients, sample_embeddings, tmp_path):
    result = process_similarity(sample_ingredients, sample_embeddings)
    output_path = tmp_path / "test_similarity.parquet"
    
    save_output(result, str(output_path))
    
    assert output_path.exists()
    loaded = pd.read_parquet(output_path)
    assert len(loaded) == len(result)
    assert list(loaded.columns) == list(result.columns)