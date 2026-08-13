"""
Integration tests for the final dataset generation pipeline.

This module tests the complete flow of:
1. Loading graph data with bridging coefficients
2. Merging novelty scores and topic clusters
3. Saving the final Parquet file
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import networkx as nx
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.lib import config
from scripts.save_final_dataset import (
    load_graph_data, 
    merge_novelty_data, 
    save_final_dataset, 
    main
)

@pytest.fixture
def sample_graph_with_clusters():
    """Create a sample graph with bridging coefficients and clusters."""
    G = nx.Graph()
    
    # Add nodes with required attributes
    nodes = [
        ('node1', {'title': 'Test Paper 1', 'citation_count': 10, 'primary_cluster': 1, 'bridging_coefficient': 0.5}),
        ('node2', {'title': 'Test Paper 2', 'citation_count': 20, 'primary_cluster': 1, 'bridging_coefficient': 0.3}),
        ('node3', {'title': 'Test Paper 3', 'citation_count': 5, 'primary_cluster': 2, 'bridging_coefficient': 0.8}),
        ('node4', {'title': '', 'citation_count': 15, 'primary_cluster': 2, 'bridging_coefficient': 0.4}),  # Empty title
    ]
    
    for node_id, attrs in nodes:
        G.add_node(node_id, **attrs)
    
    # Add some edges
    G.add_edge('node1', 'node2')
    G.add_edge('node1', 'node3')
    G.add_edge('node2', 'node4')
    
    return G

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_merge_novelty_data_basic():
    """Test merging novelty data with valid inputs."""
    # Create sample DataFrame
    df = pd.DataFrame([
        {'id': 'node1', 'title': 'Test Paper 1', 'citation_count': 10, 'primary_cluster': 1, 'bridging_coefficient': 0.5},
        {'id': 'node2', 'title': 'Test Paper 2', 'citation_count': 20, 'primary_cluster': 1, 'bridging_coefficient': 0.3},
        {'id': 'node3', 'title': 'Test Paper 3', 'citation_count': 5, 'primary_cluster': 2, 'bridging_coefficient': 0.8},
    ])
    
    # Mock the embedding and novelty functions
    with patch('scripts.save_final_dataset.generate_embeddings_for_dataset') as mock_embeddings, \
         patch('scripts.save_final_dataset.compute_novelty_scores') as mock_novelty:
        
        # Setup mock returns
        mock_embeddings.return_value = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        mock_novelty.return_value = pd.DataFrame([
            {'id': 'node1', 'novelty_score': 0.7, 'topic_cluster': 1},
            {'id': 'node2', 'novelty_score': 0.8, 'topic_cluster': 1},
            {'id': 'node3', 'novelty_score': 0.9, 'topic_cluster': 2},
        ])
        
        # Run the merge
        result = merge_novelty_data(df)
        
        # Verify results
        assert 'novelty_score' in result.columns
        assert 'topic_cluster' in result.columns
        assert len(result) == 3
        assert all(result['novelty_score'] > 0)
        assert all(result['topic_cluster'] >= 0)

def test_merge_novelty_data_empty_titles():
    """Test handling of nodes with empty titles."""
    df = pd.DataFrame([
        {'id': 'node1', 'title': '', 'citation_count': 10, 'primary_cluster': 1, 'bridging_coefficient': 0.5},
        {'id': 'node2', 'title': None, 'citation_count': 20, 'primary_cluster': 1, 'bridging_coefficient': 0.3},
    ])
    
    result = merge_novelty_data(df)
    
    # Should have default values for nodes with empty titles
    assert 'novelty_score' in result.columns
    assert 'topic_cluster' in result.columns
    assert all(result['novelty_score'] == 0.0)
    assert all(result['topic_cluster'] == -1)

def test_save_final_dataset_creates_file(temp_output_dir):
    """Test that the final dataset is saved as a Parquet file."""
    df = pd.DataFrame([
        {'id': 'node1', 'title': 'Test', 'citation_count': 10, 'primary_cluster': 1, 
         'bridging_coefficient': 0.5, 'novelty_score': 0.7, 'topic_cluster': 1},
    ])
    
    output_path = Path(temp_output_dir) / "test_output.parquet"
    success = save_final_dataset(df, output_path)
    
    assert success
    assert output_path.exists()
    
    # Verify we can read it back
    loaded_df = pd.read_parquet(output_path)
    assert len(loaded_df) == 1
    assert list(loaded_df.columns) == list(df.columns)

def test_main_integration_flow(temp_output_dir):
    """Test the complete main function flow with mocked dependencies."""
    # Mock config to use temp directory
    with patch.object(config, 'DATA_PROCESSED_DIR', temp_output_dir), \
         patch('scripts.save_final_dataset.fetch_and_build_subgraph') as mock_fetch, \
         patch('scripts.save_final_dataset.save_graph_to_parquet') as mock_save, \
         patch('scripts.save_final_dataset.generate_embeddings_for_dataset') as mock_embeddings, \
         patch('scripts.save_final_dataset.compute_novelty_scores') as mock_novelty:
        
        # Setup mock returns
        mock_fetch.return_value = nx.Graph()
        mock_save.return_value = True
        mock_embeddings.return_value = [[0.1, 0.2]]
        mock_novelty.return_value = pd.DataFrame([
            {'id': 'node1', 'novelty_score': 0.7, 'topic_cluster': 1},
        ])
        
        # Run main
        result = main()
        
        # Should complete successfully
        assert result == 0

def test_final_dataset_has_required_columns(temp_output_dir):
    """Test that the final dataset contains all required columns."""
    df = pd.DataFrame([
        {'id': 'node1', 'title': 'Test', 'citation_count': 10, 'primary_cluster': 1, 
         'bridging_coefficient': 0.5, 'novelty_score': 0.7, 'topic_cluster': 1},
    ])
    
    output_path = Path(temp_output_dir) / "test_output.parquet"
    save_final_dataset(df, output_path)
    
    loaded_df = pd.read_parquet(output_path)
    
    required_columns = [
        'id', 'title', 'citation_count', 'primary_cluster', 
        'bridging_coefficient', 'novelty_score', 'topic_cluster'
    ]
    
    for col in required_columns:
        assert col in loaded_df.columns, f"Missing required column: {col}"

def test_final_dataset_handles_large_data(temp_output_dir):
    """Test that the pipeline can handle a larger dataset."""
    # Create a larger dataset
    data = []
    for i in range(100):
        data.append({
            'id': f'node{i}',
            'title': f'Test Paper {i}',
            'citation_count': i * 10,
            'primary_cluster': i % 5,
            'bridging_coefficient': 0.1 * (i % 10),
            'novelty_score': 0.1 * (i % 10),
            'topic_cluster': i % 3
        })
    
    df = pd.DataFrame(data)
    output_path = Path(temp_output_dir) / "large_test.parquet"
    
    success = save_final_dataset(df, output_path)
    
    assert success
    assert output_path.exists()
    
    loaded_df = pd.read_parquet(output_path)
    assert len(loaded_df) == 100