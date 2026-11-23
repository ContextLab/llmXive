"""
Unit tests for the embeddings service.

This module tests:
1. Filtering of invalid nodes (empty/null titles)
2. Saving excluded nodes to log file
3. Processing nodes for embeddings
"""
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock

from src.services.embeddings import (
    filter_valid_nodes,
    save_excluded_nodes,
    process_nodes_for_embeddings
)


@pytest.fixture
def sample_dataframe_with_nulls():
    """Create a sample DataFrame with various title conditions."""
    data = {
        'id': [1, 2, 3, 4, 5, 6],
        'title': [
            "Valid title 1",
            "",  # Empty string
            None,  # Null value
            "Valid title 2",
            "   ",  # Whitespace only
            "Valid title 3"
        ],
        'citation_count': [10, 20, 30, 40, 50, 60]
    }
    return pd.DataFrame(data)


def test_empty_title_handling(sample_dataframe_with_nulls):
    """
    Test that nodes with empty or null titles are filtered out.
    
    Expected behavior:
    - Valid nodes: 3 (indices 0, 3, 5)
    - Invalid nodes: 3 (indices 1, 2, 4)
    - Excluded nodes should be logged
    """
    # Filter nodes
    valid_df, invalid_df = filter_valid_nodes(sample_dataframe_with_nulls)
    
    # Assert counts
    assert len(valid_df) == 3, f"Expected 3 valid nodes, got {len(valid_df)}"
    assert len(invalid_df) == 3, f"Expected 3 invalid nodes, got {len(invalid_df)}"
    
    # Assert valid titles
    valid_titles = valid_df['title'].tolist()
    assert "Valid title 1" in valid_titles
    assert "Valid title 2" in valid_titles
    assert "Valid title 3" in valid_titles
    
    # Assert invalid titles are empty/null/whitespace
    invalid_titles = invalid_df['title'].tolist()
    assert "" in invalid_titles
    assert None in invalid_titles
    assert "   " in invalid_titles


def test_save_excluded_nodes_creates_file(sample_dataframe_with_nulls):
    """
    Test that excluded nodes are saved to a CSV file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock the get_logs_path function
        with patch('src.services.embeddings.get_logs_path', return_value=tmpdir):
            # Filter and save invalid nodes
            _, invalid_df = filter_valid_nodes(sample_dataframe_with_nulls)
            
            # Save with reason
            save_excluded_nodes(invalid_df, 'test_reason')
            
            # Check file exists
            excluded_file = os.path.join(tmpdir, 'excluded_nodes.csv')
            assert os.path.exists(excluded_file), "Excluded nodes file was not created"
            
            # Check content
            saved_df = pd.read_csv(excluded_file)
            assert 'reason' in saved_df.columns
            assert all(saved_df['reason'] == 'test_reason')
            assert len(saved_df) == 3


def test_process_nodes_for_embeddings_handles_nulls(sample_dataframe_with_nulls):
    """
    Test that process_nodes_for_embeddings correctly handles null titles.
    
    This test mocks the embedding model to avoid actual model loading.
    """
    # Create mock model
    mock_model = MagicMock()
    mock_model.encode.return_value = np.random.rand(3, 384)  # 3 valid nodes
    
    with patch('src.services.embeddings.load_embedding_model', return_value=mock_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.services.embeddings.get_logs_path', return_value=tmpdir):
                # Process nodes
                result_df, invalid_df = process_nodes_for_embeddings(
                    sample_dataframe_with_nulls,
                    batch_size=2,
                    device="cpu"
                )
                
                # Assert result has embedding column
                assert 'embedding_vector' in result_df.columns
                
                # Assert valid nodes have embeddings
                valid_mask = result_df['title'].notna() & (result_df['title'].astype(str).str.strip() != '')
                valid_with_emb = result_df[valid_mask]
                assert all(valid_with_emb['embedding_vector'].notna())
                
                # Assert invalid nodes have null embeddings
                invalid_mask = ~valid_mask
                invalid_with_emb = result_df[invalid_mask]
                assert all(invalid_with_emb['embedding_vector'].isna())
                
                # Assert invalid_df contains the excluded nodes
                assert len(invalid_df) == 3