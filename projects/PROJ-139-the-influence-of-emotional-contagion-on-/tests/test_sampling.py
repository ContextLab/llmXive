"""
Tests for the sampling module.
"""
import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.sampling import (
    load_extracted_data,
    calculate_stratification_grid,
    load_hf_corpus,
    generate_annotations
)
from config.settings import DatasetPaths

@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    data = {
        'thread_id': ['t1', 't2', 't3', 't4'],
        'comments': [
            json.dumps([{'id': 'c1', 'text': 'This is great!', 'author': 'a1'}]),
            json.dumps([{'id': 'c2', 'text': 'I hate this.', 'author': 'a2'}]),
            json.dumps([{'id': 'c3', 'text': 'Okay I guess.', 'author': 'a3'}]),
            json.dumps([{'id': 'c4', 'text': 'Amazing work!', 'author': 'a4'}])
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_processed_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        # Create a mock threads_with_seeds.csv
        df = pd.DataFrame({
            'thread_id': ['t1', 't2', 't3', 't4', 't5', 't6', 't7', 't8'],
            'comments': [
                json.dumps([{'id': f'c{i}', 'text': 'Positive text', 'author': 'a'}])
                for i in range(1, 9)
            ]
        })
        csv_path = p / "threads_with_seeds.csv"
        df.to_csv(csv_path, index=False)
        yield p

def test_calculate_stratification_grid(sample_data):
    """Test that stratification grid is calculated correctly."""
    # We need enough data to form a grid (>= 50 in real logic, but for unit test we mock or use small set)
    # The function checks for len(df) < 50. Let's create a larger mock.
    large_data = pd.concat([sample_data] * 20, ignore_index=True) # 80 rows
    
    selected_ids, stats = calculate_stratification_grid(large_data, sample_size=20)
    
    assert isinstance(selected_ids, list)
    assert len(selected_ids) > 0
    assert 'length_median' in stats
    assert 'sentiment_median' in stats

def test_calculate_stratification_grid_small_dataset():
    """Test behavior when dataset is too small (< 50)."""
    small_data = pd.DataFrame({
        'thread_id': ['t1'],
        'comments': [json.dumps([{'id': 'c1', 'text': 'test'}])]
    })
    
    selected_ids, stats = calculate_stratification_grid(small_data)
    
    assert selected_ids == []
    assert stats.get('status') == 'insufficient_data'

def test_load_hf_corpus_failure():
    """Test that load_hf_corpus handles failures gracefully."""
    with patch('code.data.sampling.load_dataset') as mock_load:
        mock_load.side_effect = Exception("Network error")
        result = load_hf_corpus()
        assert result is None

def test_generate_annotations():
    """Test that annotations file is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "annotations.json"
        sample_ids = ['c1', 'c2']
        stats = {'test': 'value'}
        
        generate_annotations(sample_ids, stats, output_path)
        
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['status'] == 'sampled'
        assert data['sample_size'] == 2
