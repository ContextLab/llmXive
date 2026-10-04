import os
import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from scripts.finalize_features import serialize_graphs_to_disk, finalize_features
from scripts.extract_features import extract_graph_and_metrics

# Mock data for testing
MOCK_GT_DATA = [
    {
        'task_id': 'test_task_1',
        'code_diff': 'def hello():\n    print("world")',
        'dynamic_execution_outcome': 'Pass',
        'status': 'parseable'
    },
    {
        'task_id': 'test_task_2',
        'code_diff': 'def calc(x):\n    return x * 2',
        'dynamic_execution_outcome': 'Fail',
        'status': 'parseable'
    },
    {
        'task_id': 'test_task_3',
        'code_diff': 'invalid syntax here',
        'dynamic_execution_outcome': 'N/A',
        'status': 'Unparseable'
    }
]

@pytest.fixture
def temp_dirs(tmp_path):
    gt_path = tmp_path / "ground_truth.csv"
    graphs_dir = tmp_path / "graphs"
    features_path = tmp_path / "features.csv"
    
    # Write mock ground truth
    df = pd.DataFrame(MOCK_GT_DATA)
    df.to_csv(gt_path, index=False)
    
    return {
        'gt_path': str(gt_path),
        'graphs_dir': str(graphs_dir),
        'features_path': str(features_path)
    }

def test_serialize_graphs_to_disk(temp_dirs):
    """Test that graphs are serialized to disk and unparseable tasks are skipped."""
    count = serialize_graphs_to_disk(temp_dirs['gt_path'], temp_dirs['graphs_dir'])
    
    # Should process 2 tasks (skip the Unparseable one)
    assert count == 2
    
    # Check files exist
    assert Path(temp_dirs['graphs_dir'], 'test_task_1.json').exists()
    assert Path(temp_dirs['graphs_dir'], 'test_task_2.json').exists()
    assert not Path(temp_dirs['graphs_dir'], 'test_task_3.json').exists()
    
    # Verify content is valid JSON
    with open(Path(temp_dirs['graphs_dir'], 'test_task_1.json')) as f:
        data = json.load(f)
        assert 'nodes' in data or 'edges' in data # Assuming graph structure

def test_finalize_features(temp_dirs):
    """Test the full finalize_features pipeline."""
    # Mock extract_graph_and_metrics to return deterministic values
    mock_metrics = {
        'dependency_depth': 1,
        'cyclomatic_complexity': 1,
        'semantic_complexity_score': 0.5,
        'lines_of_code': 2
    }
    
    with patch('scripts.finalize_features.extract_graph_and_metrics') as mock_extract:
        mock_extract.return_value = ({'nodes': [], 'edges': []}, mock_metrics)
        
        finalize_features(
            temp_dirs['gt_path'], 
            temp_dirs['graphs_dir'], 
            temp_dirs['features_path']
        )
        
        # Check output file exists
        assert Path(temp_dirs['features_path']).exists()
        
        # Load and verify content
        df = pd.read_csv(temp_dirs['features_path'])
        
        # Should have 2 rows (Unparseable skipped)
        assert len(df) == 2
        
        # Check columns present
        required_cols = ['task_id', 'code_diff', 'dynamic_execution_outcome', 
                         'dependency_depth', 'cyclomatic_complexity', 
                         'semantic_complexity_score', 'lines_of_code']
        for col in required_cols:
            assert col in df.columns
        
        # Check no missing metrics (NaN)
        metric_cols = ['dependency_depth', 'cyclomatic_complexity', 'semantic_complexity_score', 'lines_of_code']
        assert not df[metric_cols].isnull().any().any(), "Missing metric values found in features.csv"
        
        # Verify specific values
        row = df[df['task_id'] == 'test_task_1'].iloc[0]
        assert row['dependency_depth'] == 1
        assert row['lines_of_code'] == 2
