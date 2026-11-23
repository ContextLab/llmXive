import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path

# Mock the config to avoid file system dependencies in unit tests
import sys
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from validation import degree_preserving_null, load_ecosystem_ids

@pytest.fixture
def sample_feature_df():
    """Create a small synthetic feature matrix for testing."""
    # 2 ecosystems, 2 plants, 2 pollinators
    data = {
        'ecosystem_id': ['eco1', 'eco1', 'eco1', 'eco1', 'eco2', 'eco2', 'eco2', 'eco2'],
        'plant_id': ['p1', 'p1', 'p2', 'p2', 'p1', 'p1', 'p2', 'p2'],
        'pollinator_id': ['a1', 'a2', 'a1', 'a2', 'a1', 'a2', 'a1', 'a2'],
        'link_label': [1, 0, 0, 1, 1, 0, 0, 1],
        'trait_1': [1.0, 1.0, 2.0, 2.0, 1.5, 1.5, 2.5, 2.5],
        'trait_2': [0.5, 0.5, 1.5, 1.5, 0.6, 0.6, 1.6, 1.6]
    }
    df = pd.DataFrame(data)
    return df

@pytest.fixture
def trained_model():
    """Return a pre-trained dummy model."""
    model = RandomForestClassifier(n_estimators=5, random_state=42)
    # Fit on dummy data to avoid errors
    X = np.random.rand(10, 2)
    y = np.random.randint(0, 2, 10)
    model.fit(X, y)
    return model

def test_load_ecosystem_ids(sample_feature_df):
    ids = load_ecosystem_ids(sample_feature_df)
    assert set(ids) == {'eco1', 'eco2'}

def test_degree_preserving_null_no_crash(sample_feature_df, trained_model):
    """
    Test that degree_preserving_null runs without crashing on small data.
    We don't assert a specific value because the stochastic nature of 
    edge switching can lead to variance, but we ensure it returns a float.
    """
    # Run with very few iterations for speed
    result = degree_preserving_null(sample_feature_df, n_iterations=5)
    
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0, "AUC should be between 0 and 1"

def test_degree_preserving_null_empty_graph(sample_feature_df):
    """Test behavior when there are no positive links."""
    df_no_links = sample_feature_df.copy()
    df_no_links['link_label'] = 0
    
    # Should handle gracefully, likely return 0.5 or 0.0
    result = degree_preserving_null(df_no_links, n_iterations=5)
    assert isinstance(result, float)

def test_degree_preserving_null_single_ecosystem(sample_feature_df):
    """Test with only one ecosystem."""
    df_single = sample_feature_df[sample_feature_df['ecosystem_id'] == 'eco1'].copy()
    result = degree_preserving_null(df_single, n_iterations=5)
    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0