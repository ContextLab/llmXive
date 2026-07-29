"""
Unit tests for data_loader streaming functionality.
"""
import pytest
from unittest.mock import patch, MagicMock
import networkx as nx
from pathlib import Path

# Import the module to test
from code.data_loader import fetch_locomo_dataset, build_memory_graph, CHUNK_SIZE

class TestStreaming:
    def test_fetch_dataset_streaming_flag(self):
        """Test that fetch_locomo_dataset calls load_dataset with streaming=True."""
        with patch('code.data_loader.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_load.return_value = mock_ds
            
            # Call with streaming=True
            fetch_locomo_dataset(streaming=True)
            
            mock_load.assert_called_once()
            # Check that streaming=True was passed
            call_kwargs = mock_load.call_args
            assert call_kwargs.kwargs.get('streaming') == True

    def test_fetch_dataset_subset_limit(self):
        """Test that subset parameter limits the number of items returned."""
        # Mock data
        mock_data = [{'id': str(i), 'context': f'context_{i}'} for i in range(10)]
        
        with patch('code.data_loader.load_dataset') as mock_load:
            mock_ds = MagicMock()
            mock_ds.__iter__ = MagicMock(return_value=iter(mock_data))
            mock_load.return_value = mock_ds
            
            # Fetch with subset=5
            result_iter = fetch_locomo_dataset(subset=5, streaming=False)
            result_list = list(result_iter)
            
            assert len(result_list) == 5
            assert result_list[0]['id'] == '0'
            assert result_list[-1]['id'] == '4'

    def test_build_memory_graph(self):
        """Test basic graph construction from tasks."""
        tasks = [
            {'id': 't1', 'context': 'The cat sat on the mat.'},
            {'id': 't2', 'context': 'The dog ran in the park.'}
        ]
        
        G = build_memory_graph(tasks, seed=42)
        
        assert G.number_of_nodes() > 0
        assert G.number_of_edges() > 0
        assert G.has_node('t1')
        assert G.has_node('t2')

    def test_chunk_size_constant(self):
        """Verify CHUNK_SIZE is set correctly for memory management."""
        assert CHUNK_SIZE == 1000

if __name__ == "__main__":
    pytest.main([__file__, "-v"])