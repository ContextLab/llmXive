import os
import sys
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.co_occurrence import load_epsilon_config, build_cooccurrence_matrix, save_output

@pytest.fixture
def sample_recipe_data():
    """Create a small sample of recipe data for testing."""
    data = {
        'recipe_id': [1, 2, 3, 4],
        'ingredients': [
            ['flour', 'sugar', 'eggs'],
            ['flour', 'butter'],
            ['sugar', 'eggs', 'vanilla'],
            ['flour', 'sugar', 'butter', 'eggs']
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_normalized_mapping():
    """Create a sample normalized ingredient mapping."""
    data = {
        'ingredient_id': [101, 102, 103, 104],
        'canonical_name': ['flour', 'sugar', 'eggs', 'butter'],
        'frequency': [100, 90, 80, 70]
    }
    df = pd.DataFrame(data)
    # Save to a temporary file for the test
    output_path = Path("data/processed/normalized_ingredients.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df

def test_load_epsilon_config():
    """Test that epsilon config is loaded correctly."""
    config = load_epsilon_config()
    assert 'epsilon' in config
    assert isinstance(config['epsilon'], float)
    assert config['epsilon'] > 0

def test_build_cooccurrence_matrix(sample_recipe_data, sample_normalized_mapping):
    """Test the co-occurrence matrix construction."""
    # We need to mock the load_ingredient_pairs function or pass data directly
    # For this test, we'll call build_cooccurrence_matrix with a modified dataframe
    # that has the normalized_ingredient_ids column
    
    # Create a mapping from canonical_name to ingredient_id
    name_to_id = sample_normalized_mapping.set_index('canonical_name')['ingredient_id'].to_dict()
    
    def normalize_ingredient_list(ing_list):
        normalized_ids = []
        for ing in ing_list:
            canonical = ing.lower().strip()
            if canonical in name_to_id:
                normalized_ids.append(name_to_id[canonical])
        return normalized_ids
    
    sample_recipe_data['normalized_ingredient_ids'] = sample_recipe_data['ingredients'].apply(normalize_ingredient_list)
    
    # Build the matrix
    co_occurrence_df, mapping_df = build_cooccurrence_matrix(sample_recipe_data)
    
    # Check dimensions
    assert co_occurrence_df.shape[0] == co_occurrence_df.shape[1]
    assert co_occurrence_df.shape[0] == len(set(sample_normalized_mapping['ingredient_id']))
    
    # Check that the matrix is symmetric
    assert np.allclose(co_occurrence_df.values, co_occurrence_df.values.T)
    
    # Check specific values
    # flour (101) and sugar (102) appear together in recipes 1 and 4 -> count = 2
    # flour (101) and eggs (103) appear together in recipes 1 and 4 -> count = 2
    # sugar (102) and eggs (103) appear together in recipes 1, 3, 4 -> count = 3
    
    # We need to map back to indices to check values
    id_list = sorted(list(set(sample_normalized_mapping['ingredient_id'])))
    id_to_idx = {id_val: idx for idx, id_val in enumerate(id_list)}
    
    flour_idx = id_to_idx[101]
    sugar_idx = id_to_idx[102]
    eggs_idx = id_to_idx[103]
    
    assert co_occurrence_df.iloc[flour_idx, sugar_idx] == 2
    assert co_occurrence_df.iloc[flour_idx, eggs_idx] == 2
    assert co_occurrence_df.iloc[sugar_idx, eggs_idx] == 3

def test_save_output(sample_recipe_data, sample_normalized_mapping, tmp_path):
    """Test saving the co-occurrence matrix."""
    # Prepare data as in the previous test
    name_to_id = sample_normalized_mapping.set_index('canonical_name')['ingredient_id'].to_dict()
    
    def normalize_ingredient_list(ing_list):
        normalized_ids = []
        for ing in ing_list:
            canonical = ing.lower().strip()
            if canonical in name_to_id:
                normalized_ids.append(name_to_id[canonical])
        return normalized_ids
    
    sample_recipe_data['normalized_ingredient_ids'] = sample_recipe_data['ingredients'].apply(normalize_ingredient_list)
    co_occurrence_df, mapping_df = build_cooccurrence_matrix(sample_recipe_data)
    
    output_path = tmp_path / "test_co_occurrence.parquet"
    epsilon_config = {"epsilon": 1e-6}
    
    save_output(co_occurrence_df, mapping_df, str(output_path), epsilon_config)
    
    # Check that the file was created
    assert output_path.exists()
    
    # Check that the mapping file was created
    mapping_path = output_path.parent / "co_occurrence_mapping.csv"
    assert mapping_path.exists()
    
    # Check that the config file was created
    config_path = output_path.parent / "co_occurrence_config.json"
    assert config_path.exists()
    
    # Read back and verify
    loaded_df = pd.read_parquet(output_path)
    assert loaded_df.shape == co_occurrence_df.shape
    
    # Verify log transform was applied (values should be different from original counts)
    # The original counts are integers, log(count + epsilon) will be floats
    assert loaded_df.values.dtype in [np.float32, np.float64]
