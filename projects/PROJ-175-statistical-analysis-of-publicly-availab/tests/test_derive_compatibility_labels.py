import os
import json
import pandas as pd
import pytest
from pathlib import Path
import numpy as np

from code.data.derive_compatibility_labels import (
    load_threshold_from_t048,
    load_ingredient_pairs,
    load_download_status,
    derive_labels_from_counterfactual,
    derive_labels_from_ratings,
    save_output
)

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for test artifacts."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "processed").mkdir()
    (data_dir / "logs").mkdir()
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    return tmp_path

@pytest.fixture
def sample_ingredient_pairs(temp_dirs):
    """Create sample ingredient pairs DataFrame."""
    df = pd.DataFrame({
        'ingredient_a': ['salt', 'sugar', 'butter', 'flour'],
        'ingredient_b': ['pepper', 'honey', 'oil', 'yeast'],
        'frequency_a': [100, 80, 60, 90],
        'frequency_b': [90, 70, 50, 85]
    })
    output_path = temp_dirs / "data" / "processed" / "ingredient_pairs.csv"
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def sample_counterfactual_data(temp_dirs):
    """Create sample Counterfactual dataset."""
    df = pd.DataFrame({
        'ingredient_a': ['salt', 'sugar', 'butter'],
        'ingredient_b': ['pepper', 'honey', 'oil'],
        'independent_sensory_compatibility': [1, 0, 1]
    })
    output_path = temp_dirs / "data" / "raw" / "counterfactual_raw.csv"
    df.to_csv(output_path, index=False)
    return output_path

@pytest.fixture
def sample_recipe1m_data(temp_dirs):
    """Create sample Recipe1M processed data."""
    df = pd.DataFrame({
        'recipe_id': [1, 2, 3, 4, 5],
        'ingredients': [['salt', 'pepper'], ['sugar', 'honey'], ['butter', 'oil'], ['flour', 'yeast'], ['salt', 'sugar']],
        'rating': [4.5, 3.2, 4.0, 3.8, 4.2]
    })
    output_path = temp_dirs / "data" / "raw" / "recipe1m_processed.parquet"
    df.to_parquet(output_path, index=False)
    return output_path

@pytest.fixture
def sample_download_status(temp_dirs):
    """Create sample download status JSON."""
    status = {
        'recipe1m': {'status': 'SUCCESS'},
        'flavordb': {'status': 'FAILED'},
        'counterfactual': {'status': 'SUCCESS'}
    }
    output_path = temp_dirs / "data" / "download_status.json"
    with open(output_path, 'w') as f:
        json.dump(status, f)
    return output_path

@pytest.fixture
def sample_amendment_log_ratified(temp_dirs):
    """Create sample ratified amendment log."""
    log = {
        'status': 'RATIFIED',
        'methodology': 'Causal Independence',
        'proxy_source': None,
        'timestamp': '2024-01-01T00:00:00'
    }
    output_path = temp_dirs / "data" / "amendment_log.json"
    with open(output_path, 'w') as f:
        json.dump(log, f)
    return output_path

@pytest.fixture
def sample_amendment_log_proxy(temp_dirs):
    """Create sample proxy amendment log."""
    log = {
        'status': 'RATIFIED',
        'methodology': 'Correlational Analysis',
        'proxy_source': 'Recipe1M',
        'timestamp': '2024-01-01T00:00:00'
    }
    output_path = temp_dirs / "data" / "amendment_log.json"
    with open(output_path, 'w') as f:
        json.dump(log, f)
    return output_path

def test_load_ingredient_pairs(temp_dirs, sample_ingredient_pairs):
    """Test loading ingredient pairs from CSV."""
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    assert len(df) == 4
    assert 'ingredient_a' in df.columns
    assert 'ingredient_b' in df.columns

def test_load_download_status(temp_dirs, sample_download_status):
    """Test loading download status JSON."""
    status = load_download_status(str(sample_download_status))
    assert status['recipe1m']['status'] == 'SUCCESS'
    assert status['counterfactual']['status'] == 'SUCCESS'

def test_derive_labels_from_counterfactual(temp_dirs, sample_ingredient_pairs, sample_counterfactual_data, sample_download_status, sample_amendment_log_ratified):
    """Test deriving labels from Counterfactual dataset."""
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    download_status = load_download_status(str(sample_download_status))
    
    result_df = derive_labels_from_counterfactual(df, download_status)
    
    assert 'compatibility_label' in result_df.columns
    assert len(result_df) > 0
    assert result_df['compatibility_label'].isin([0, 1]).all()

def test_derive_labels_from_ratings_proxy(temp_dirs, sample_ingredient_pairs, sample_recipe1m_data, sample_download_status, sample_amendment_log_proxy):
    """Test deriving labels from Recipe1M ratings (proxy method)."""
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    download_status = load_download_status(str(sample_download_status))
    
    # Add estimated rating column for proxy method
    df['estimated_rating'] = (df['frequency_a'] + df['frequency_b']) / 2
    
    result_df = derive_labels_from_ratings(df, download_status)
    
    assert 'compatibility_label' in result_df.columns
    assert len(result_df) > 0
    assert result_df['compatibility_label'].isin([0, 1]).all()
    
    # Check that circularity warning was created
    circularity_path = temp_dirs / "data" / "logs" / "circularity_warning.json"
    assert circularity_path.exists()
    
    # Check that circularity report was created
    report_path = temp_dirs / "docs" / "circularity_report.md"
    assert report_path.exists()

def test_save_output(temp_dirs, sample_ingredient_pairs):
    """Test saving labeled ingredient pairs."""
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    df['compatibility_label'] = [1, 0, 1, 0]
    
    output_path = temp_dirs / "data" / "processed" / "output_test.csv"
    save_output(df, str(output_path))
    
    assert output_path.exists()
    result_df = pd.read_csv(output_path)
    assert len(result_df) == 4
    assert 'compatibility_label' in result_df.columns

def test_missing_counterfactual_raises_error(temp_dirs, sample_ingredient_pairs, sample_download_status, sample_amendment_log_ratified):
    """Test that missing Counterfactual data raises error."""
    # Modify download status to indicate Counterfactual failure
    status = {
        'recipe1m': {'status': 'SUCCESS'},
        'flavordb': {'status': 'FAILED'},
        'counterfactual': {'status': 'FAILED'}
    }
    download_status_path = temp_dirs / "data" / "download_status.json"
    with open(download_status_path, 'w') as f:
        json.dump(status, f)
    
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    download_status = load_download_status(str(download_status_path))
    
    with pytest.raises(RuntimeError, match="Counterfactual dataset not available"):
        derive_labels_from_counterfactual(df, download_status)

def test_missing_amendment_log_raises_error(temp_dirs, sample_ingredient_pairs, sample_download_status):
    """Test that missing amendment log raises error for proxy method."""
    df = load_ingredient_pairs(str(sample_ingredient_pairs))
    download_status = load_download_status(str(sample_download_status))
    
    with pytest.raises(FileNotFoundError, match="Amendment log not found"):
        derive_labels_from_ratings(df, download_status)
