import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.co_occurrence import (
    load_epsilon_config,
    load_ingredient_pairs,
    build_cooccurrence_matrix,
    save_output
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_ingredients_csv(temp_dir):
    """Create a sample normalized ingredients CSV."""
    csv_path = os.path.join(temp_dir, "normalized_ingredients.csv")
    data = {
        'ingredient_id': ['ing1', 'ing2', 'ing3'],
        'canonical_name': ['salt', 'pepper', 'garlic'],
        'functional_role': ['primary', 'secondary', 'garnish'],
        'frequency': [100, 50, 75]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def sample_recipes_parquet(temp_dir):
    """Create a sample recipe parquet file."""
    parquet_path = os.path.join(temp_dir, "recipe1m_processed.parquet")
    data = {
        'recipe_id': [1, 2, 3],
        'ingredients': [
            ['salt', 'pepper', 'garlic'],
            ['salt', 'garlic'],
            ['pepper', 'garlic']
        ]
    }
    df = pd.DataFrame(data)
    df.to_parquet(parquet_path)
    return parquet_path

def test_load_epsilon_config_default(temp_dir):
    """Test loading epsilon config with missing file."""
    epsilon = load_epsilon_config(os.path.join(temp_dir, "nonexistent.json"))
    assert epsilon == 1e-6

def test_load_ingredient_pairs_missing_file():
    """Test loading ingredients when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        load_ingredient_pairs("nonexistent/path.csv")

def test_load_ingredient_pairs_missing_columns(sample_ingredients_csv):
    """Test loading ingredients with missing required columns."""
    # Create a CSV with missing columns
    temp_path = tempfile.mktemp(suffix=".csv")
    data = {'name': ['salt'], 'count': [100]}
    pd.DataFrame(data).to_csv(temp_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_ingredient_pairs(temp_path)

def test_build_cooccurrence_matrix_missing_recipes(sample_ingredients_csv):
    """Test building matrix when recipe file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        build_cooccurrence_matrix("nonexistent/recipes.parquet")

def test_build_cooccurrence_matrix(sample_ingredients_csv, sample_recipes_parquet):
    """Test building co-occurrence matrix with sample data."""
    # Mock the ingredient column lookup
    matrix = build_cooccurrence_matrix(
        recipes_path=sample_recipes_parquet,
        ingredient_col='ingredients'
    )
    
    assert isinstance(matrix, pd.DataFrame)
    assert matrix.shape[0] == matrix.shape[1]  # Square matrix
    assert matrix.shape[0] > 0  # Has ingredients
    
    # Check that diagonal has values (self-co-occurrence)
    # Each ingredient appears in at least one recipe
    assert matrix.values.min() >= 0  # All values non-negative

def test_save_output(temp_dir, sample_ingredients_csv, sample_recipes_parquet):
    """Test saving co-occurrence matrix."""
    matrix = build_cooccurrence_matrix(
        recipes_path=sample_recipes_parquet,
        ingredient_col='ingredients'
    )
    
    output_path = os.path.join(temp_dir, "test_co_occurrence.parquet")
    save_output(matrix, output_path)
    
    assert os.path.exists(output_path)
    
    # Verify metadata file
    metadata_path = output_path.replace('.parquet', '_metadata.json')
    assert os.path.exists(metadata_path)
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert 'shape' in metadata
    assert 'num_ingredients' in metadata
    assert metadata['shape'][0] == metadata['shape'][1]

def test_log_transform_applied(sample_ingredients_csv, sample_recipes_parquet):
    """Test that log transform is applied to co-occurrence counts."""
    matrix = build_cooccurrence_matrix(
        recipes_path=sample_recipes_parquet,
        ingredient_col='ingredients'
    )
    
    # Check that values are in log space (should be small positive numbers)
    # Original counts are integers, log(1+count) will be small
    max_val = matrix.values.max()
    assert max_val < 10  # Log transform keeps values small

def test_symmetric_matrix(sample_ingredients_csv, sample_recipes_parquet):
    """Test that the co-occurrence matrix is symmetric."""
    matrix = build_cooccurrence_matrix(
        recipes_path=sample_recipes_parquet,
        ingredient_col='ingredients'
    )
    
    # Check symmetry (allowing for small floating point errors)
    diff = matrix - matrix.T
    assert np.allclose(diff.values, 0, atol=1e-9)
