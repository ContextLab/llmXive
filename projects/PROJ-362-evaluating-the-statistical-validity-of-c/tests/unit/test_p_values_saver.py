import os
import csv
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import logging

# Setup logging for tests
logging.basicConfig(level=logging.INFO)

class TestPValuesSaver:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_ensure_p_values_dir_creates_directory(self, temp_dir):
        """Test that ensure_p_values_dir creates the directory if it doesn't exist."""
        from p_values_saver import ensure_p_values_dir
        
        # Mock RESULTS_DIR to point to temp_dir
        with patch('p_values_saver.RESULTS_DIR', temp_dir):
            result = ensure_p_values_dir()
            
            expected_path = os.path.join(temp_dir, "p_values")
            assert result == expected_path
            assert os.path.exists(result)
            assert os.path.isdir(result)

    def test_save_raw_p_values_creates_csv(self, temp_dir):
        """Test that save_raw_p_values creates a properly formatted CSV."""
        from p_values_saver import save_raw_p_values
        
        # Sample data
        test_data = [
            {'query_id': 1, 'metric': 'NDCG@10', 'raw_p': 0.05},
            {'query_id': 2, 'metric': 'MAP', 'raw_p': 0.12},
            {'query_id': 3, 'metric': 'NDCG@10', 'raw_p': 0.001},
        ]
        
        output_path = os.path.join(temp_dir, "test_p_values.csv")
        result_path = save_raw_p_values(test_data, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 3
            assert rows[0] == {'query_id': '1', 'metric': 'NDCG@10', 'raw_p': '0.05'}
            assert rows[1] == {'query_id': '2', 'metric': 'MAP', 'raw_p': '0.12'}
            assert rows[2] == {'query_id': '3', 'metric': 'NDCG@10', 'raw_p': '0.001'}

    def test_run_p_values_saving_integration(self, temp_dir):
        """Test the full run_p_values_saving flow with mocked dependencies."""
        from p_values_saver import run_p_values_saving
        from p_values import process_null_distributions
        
        # Mock process_null_distributions to return test data
        mock_data = [
            {'query_id': 10, 'metric': 'NDCG@10', 'raw_p': 0.045},
            {'query_id': 11, 'metric': 'MAP', 'raw_p': 0.089},
        ]
        
        with patch('p_values_saver.process_null_distributions', return_value=mock_data):
            with patch('p_values_saver.RESULTS_DIR', temp_dir):
                result = run_p_values_saving()
                
                assert result is not None
                assert os.path.exists(result)
                
                # Verify file content
                with open(result, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 2
                    assert rows[0]['query_id'] == '10'
                    assert rows[0]['metric'] == 'NDCG@10'
                    assert rows[0]['raw_p'] == '0.045'

    def test_empty_p_values_data(self, temp_dir):
        """Test behavior when no p-values data is found."""
        from p_values_saver import run_p_values_saving
        
        with patch('p_values_saver.process_null_distributions', return_value=[]):
            with patch('p_values_saver.RESULTS_DIR', temp_dir):
                result = run_p_values_saving()
                
                assert result is None