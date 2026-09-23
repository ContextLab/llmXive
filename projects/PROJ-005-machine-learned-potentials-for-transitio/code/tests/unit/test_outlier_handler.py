import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import json
import os
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.outlier_handler import (
    load_graphs_with_metadata,
    compute_coordination_numbers,
    flag_outliers,
    save_outlier_summary,
    save_flagged_graphs,
    run_outlier_handling
)

@pytest.fixture
def mock_graphs_parquet(tmp_path):
    """Create a mock graphs_intermediate.parquet file with adjacency matrices."""
    # Create mock data
    # Simulating a DataFrame with an 'adjacency_matrix' column
    # Each row is a graph.
    
    # Graph 1: Normal, max coord 3
    adj1 = np.array([
        [0, 1, 1, 0],
        [1, 0, 1, 0],
        [1, 1, 0, 0],
        [0, 0, 0, 0]
    ])
    
    # Graph 2: Normal, max coord 4
    adj2 = np.array([
        [0, 1, 1, 1, 1],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0]
    ])
    
    # Graph 3: Outlier, max coord 7 ( > 6)
    adj3 = np.array([
        [0, 1, 1, 1, 1, 1, 1, 1], # 7 connections
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0]
    ])

    data = {
        "graph_id": [1, 2, 3],
        "adjacency_matrix": [adj1, adj2, adj3],
        "energy_dft": [1.0, 2.0, 3.0]
    }
    
    df = pd.DataFrame(data)
    file_path = tmp_path / "graphs_intermediate.parquet"
    df.to_parquet(file_path)
    
    return file_path

def test_compute_coordination_numbers(mock_graphs_parquet, tmp_path):
    """Test that coordination numbers are calculated correctly."""
    # Temporarily patch get_project_root to use tmp_path if needed, 
    # but here we pass the path directly to load function or mock the loader.
    # Since load_graphs_with_metadata expects a specific path, we'll load manually for the test
    # or adjust the function call.
    
    # Let's test compute_coordination_numbers directly with a loaded DF
    df = pd.read_parquet(mock_graphs_parquet)
    
    result_df = compute_coordination_numbers(df)
    
    # Graph 1: max degree 2
    # Graph 2: max degree 4
    # Graph 3: max degree 7
    assert result_df['max_coordination'].iloc[0] == 2.0
    assert result_df['max_coordination'].iloc[1] == 4.0
    assert result_df['max_coordination'].iloc[2] == 7.0

def test_flag_outliers(mock_graphs_parquet, tmp_path):
    """Test that outliers with coord > 6 are flagged correctly."""
    df = pd.read_parquet(mock_graphs_parquet)
    df = compute_coordination_numbers(df)
    
    result_df = flag_outliers(df, threshold=6)
    
    # Graph 1 (2) -> Not outlier
    assert result_df['is_outlier'].iloc[0] == False
    assert result_df['exclude_from_training'].iloc[0] == False
    assert result_df['retain_in_test'].iloc[0] == True
    
    # Graph 2 (4) -> Not outlier
    assert result_df['is_outlier'].iloc[1] == False
    assert result_df['exclude_from_training'].iloc[1] == False
    
    # Graph 3 (7) -> Outlier
    assert result_df['is_outlier'].iloc[2] == True
    assert result_df['exclude_from_training'].iloc[2] == True
    assert result_df['retain_in_test'].iloc[2] == True

def test_save_outlier_summary(mock_graphs_parquet, tmp_path):
    """Test saving the outlier summary JSON."""
    df = pd.read_parquet(mock_graphs_parquet)
    df = compute_coordination_numbers(df)
    df = flag_outliers(df, threshold=6)
    
    output_path = tmp_path / "outlier_summary.json"
    save_outlier_summary(df, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        summary = json.load(f)
    
    assert summary['total_samples'] == 3
    assert summary['outlier_count'] == 1
    assert summary['outlier_threshold'] == 6
    assert summary['coordination_stats']['max'] == 7.0

def test_run_outlier_handling(mock_graphs_parquet, tmp_path):
    """Test the full pipeline."""
    # We need to mock the get_project_root behavior or pass paths explicitly.
    # Since run_outlier_handling uses get_project_root, we'll create the structure
    # expected by the function or modify the test to inject paths.
    # For this unit test, we'll assume the function is called with explicit paths
    # if we refactor, or we mock the environment.
    # To keep it simple and robust, let's test the logic by calling the helper functions
    # directly as done in previous tests, or by mocking the root.
    
    # Simulating the structure:
    # tmp_path / "data" / "processed" / "graphs_intermediate.parquet"
    # But our fixture is at tmp_path / "graphs_intermediate.parquet"
    # Let's move the file to the expected location for the full test
    
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    expected_input = data_dir / "graphs_intermediate.parquet"
    
    # Copy the mock data to the expected location
    df = pd.read_parquet(mock_graphs_parquet)
    df.to_parquet(expected_input)
    
    # Mock get_project_root to return tmp_path
    import src.data.outlier_handler as handler_module
    original_get_project_root = handler_module.get_project_root
    
    def mock_get_project_root():
        return tmp_path
    
    handler_module.get_project_root = mock_get_project_root
    
    try:
        summary_path, flagged_path = run_outlier_handling(
            input_path=expected_input,
            output_dir=data_dir
        )
        
        assert summary_path.exists()
        assert flagged_path.exists()
        
        # Verify flagged parquet has the new columns
        flagged_df = pd.read_parquet(flagged_path)
        assert 'is_outlier' in flagged_df.columns
        assert 'exclude_from_training' in flagged_df.columns
        assert 'retain_in_test' in flagged_df.columns
        
    finally:
        handler_module.get_project_root = original_get_project_root

def test_missing_adjacency_raises():
    """Test that missing adjacency matrix raises an error."""
    df = pd.DataFrame({"graph_id": [1], "energy_dft": [1.0]})
    with pytest.raises(ValueError, match="Expected 'adjacency_matrix' column"):
        compute_coordination_numbers(df)