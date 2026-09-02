import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Expected schema for tda_features.csv
EXPECTED_COLUMNS = [
    'smiles',
    'num_nodes',
    'num_edges',
    'molecular_weight',
    'persistence_image_features',
    'betti_0_sum',
    'betti_1_sum',
    'persistence_landscape_features',
    'topological_summary'
]

REQUIRED_TYPES = {
    'smiles': str,
    'num_nodes': int,
    'num_edges': int,
    'molecular_weight': float,
    'persistence_image_features': str,  # Stored as JSON string or array repr
    'betti_0_sum': float,
    'betti_1_sum': float,
    'persistence_landscape_features': str,
    'topological_summary': str
}

def get_tda_features_path():
    # Project root relative to the execution context
    project_root = Path("projects/PROJ-444-predicting-molecular-properties-from-top")
    return project_root / "data" / "processed" / "tda_features.csv"

@pytest.fixture
def tda_df():
    path = get_tda_features_path()
    if not path.exists():
        pytest.skip(f"File not found: {path}")
    return pd.read_csv(path)

def test_file_exists():
    """Test that the TDA features file exists."""
    assert get_tda_features_path().exists(), "tda_features.csv does not exist"

def test_schema_columns(tda_df):
    """Test that all required columns are present."""
    missing_cols = set(EXPECTED_COLUMNS) - set(tda_df.columns)
    assert not missing_cols, f"Missing columns: {missing_cols}"

def test_column_types(tda_df):
    """Test that columns have expected data types."""
    for col, expected_type in REQUIRED_TYPES.items():
        if col in tda_df.columns:
            actual_type = tda_df[col].dtype
            if expected_type == int:
                # Allow integer types and object (if they look like ints)
                assert actual_type in [np.int64, np.int32, 'int64', 'int32', 'object'], f"Column {col} type mismatch: {actual_type}"
            elif expected_type == float:
                # Allow float types and object
                assert actual_type in [np.float64, np.float32, 'float64', 'float32', 'object'], f"Column {col} type mismatch: {actual_type}"
            else:
                # For string/object columns, object dtype is expected
                assert actual_type == 'object' or actual_type == str, f"Column {col} should be string/object, got {actual_type}"

def test_no_null_values(tda_df):
    """Test that critical columns do not have null values."""
    critical_cols = ['smiles', 'num_nodes', 'num_edges', 'molecular_weight']
    for col in critical_cols:
        if col in tda_df.columns:
            assert tda_df[col].isnull().sum() == 0, f"Column {col} contains null values"

def test_feature_vector_length(tda_df):
    """Test that persistence image features are non-empty."""
    if 'persistence_image_features' in tda_df.columns:
        # Check if the string representation is not empty
        non_empty = tda_df['persistence_image_features'].apply(lambda x: len(str(x).strip()) > 0)
        assert non_empty.all(), "Some persistence image features are empty"

def test_positive_node_count(tda_df):
    """Test that node counts are positive."""
    if 'num_nodes' in tda_df.columns:
        assert (tda_df['num_nodes'] > 0).all(), "Some molecules have zero or negative node counts"

def test_non_negative_edge_count(tda_df):
    """Test that edge counts are non-negative."""
    if 'num_edges' in tda_df.columns:
        assert (tda_df['num_edges'] >= 0).all(), "Some molecules have negative edge counts"

def test_valid_json_features(tda_df):
    """Test that feature columns containing JSON are valid."""
    json_cols = ['persistence_image_features', 'persistence_landscape_features']
    for col in json_cols:
        if col in tda_df.columns:
            for idx, val in enumerate(tda_df[col]):
                try:
                    # If it's a string, try to parse it
                    if isinstance(val, str):
                        json.loads(val)
                except json.JSONDecodeError:
                    pytest.fail(f"Invalid JSON in column {col} at row {idx}: {val}")