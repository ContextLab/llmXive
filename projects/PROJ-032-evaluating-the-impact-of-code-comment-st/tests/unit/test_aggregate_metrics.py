"""
Unit tests for T027: Aggregate metrics functionality.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the function to test
from aggregate_metrics import load_metric_file, aggregate_metrics

class TestLoadMetricFile:
    """Tests for load_metric_file function."""
    
    def test_load_list_structure(self, tmp_path):
        """Test loading a list-based JSON structure."""
        file_path = tmp_path / "test.json"
        data = [
            {"repo_id": "repo1", "value": 0.5},
            {"repo_id": "repo2", "value": 0.8}
        ]
        file_path.write_text(json.dumps(data))
        
        result = load_metric_file(file_path)
        assert result == {"repo1": 0.5, "repo2": 0.8}
    
    def test_load_dict_structure(self, tmp_path):
        """Test loading a dict-based JSON structure."""
        file_path = tmp_path / "test.json"
        data = {
            "repo1": 0.5,
            "repo2": 0.8
        }
        file_path.write_text(json.dumps(data))
        
        result = load_metric_file(file_path)
        assert result == data
    
    def test_missing_file(self, tmp_path):
        """Test handling of missing file."""
        file_path = tmp_path / "nonexistent.json"
        result = load_metric_file(file_path)
        assert result == {}
    
    def test_invalid_json_structure(self, tmp_path):
        """Test handling of unexpected JSON structure."""
        file_path = tmp_path / "test.json"
        file_path.write_text('"just a string"')
        
        # Should log error and return empty dict
        with patch('aggregate_metrics.logger') as mock_logger:
            result = load_metric_file(file_path)
            assert result == {}
            mock_logger.error.assert_called_once()

class TestAggregateMetrics:
    """Tests for aggregate_metrics function."""
    
    def test_aggregate_creates_csv(self, tmp_path, monkeypatch):
        """Test that aggregate_metrics creates the output CSV file."""
        # Set up temporary directories
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create mock metric files
        metric_files = {
            "readability.json": [{"repo_id": "repo1", "value": 0.5}],
            "sentiment.json": {"repo1": 0.8},
            "density.json": [{"repo_id": "repo1", "value": 0.3}],
            "churn.json": {"repo1": 100.0},
            "complexity.json": [{"repo_id": "repo1", "value": 5.2}],
            "quality_rate.json": {"repo1": 0.9}
        }
        
        for filename, data in metric_files.items():
            file_path = processed_dir / filename
            file_path.write_text(json.dumps(data))
        
        # Mock the constants
        with patch('aggregate_metrics.PROJECT_ROOT', tmp_path), \
             patch('aggregate_metrics.PROCESSED_DIR', processed_dir), \
             patch('aggregate_metrics.METRIC_FILES', {
                 name: processed_dir / filename 
                 for name, filename in zip(
                     ["readability", "sentiment", "density", "churn", "complexity", "bug_fix_rate"],
                     metric_files.keys()
                 )
             }), \
             patch('aggregate_metrics.logger'):
            
                aggregate_metrics()
                
                # Check that output file was created
                output_file = processed_dir / "metrics.csv"
                assert output_file.exists()
                
                # Verify CSV content
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == 2  # Header + 1 data row
                assert "repo_id" in lines[0]
                assert "readability" in lines[0]
                
                # Check that values are rounded to 2 decimal places
                data_line = lines[1].strip().split(',')
                assert float(data_line[1]) == 0.5  # readability
                assert float(data_line[2]) == 0.8  # sentiment
    
    def test_handles_missing_metrics(self, tmp_path, monkeypatch):
        """Test that missing metrics are handled gracefully."""
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create only some metric files
        metric_files = {
            "readability.json": [{"repo_id": "repo1", "value": 0.5}],
            # Missing other metrics
        }
        
        for filename, data in metric_files.items():
            file_path = processed_dir / filename
            file_path.write_text(json.dumps(data))
        
        with patch('aggregate_metrics.PROJECT_ROOT', tmp_path), \
             patch('aggregate_metrics.PROCESSED_DIR', processed_dir), \
             patch('aggregate_metrics.METRIC_FILES', {
                 name: processed_dir / filename 
                 for name, filename in zip(
                     ["readability", "sentiment", "density", "churn", "complexity", "bug_fix_rate"],
                     ["readability.json", "sentiment.json", "density.json", "churn.json", "complexity.json", "quality_rate.json"]
                 )
             }), \
             patch('aggregate_metrics.logger'):
            
                aggregate_metrics()
                
                output_file = processed_dir / "metrics.csv"
                assert output_file.exists()
                
                # Should have empty values for missing metrics
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == 2
                # Check that row has correct number of columns
                assert len(lines[1].strip().split(',')) == 7
    
    def test_empty_metrics_no_crash(self, tmp_path, monkeypatch):
        """Test that empty metrics don't cause crashes."""
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True)
        
        # Create empty metric files
        for filename in ["readability.json", "sentiment.json", "density.json", 
                       "churn.json", "complexity.json", "quality_rate.json"]:
            file_path = processed_dir / filename
            file_path.write_text("[]")
        
        with patch('aggregate_metrics.PROJECT_ROOT', tmp_path), \
             patch('aggregate_metrics.PROCESSED_DIR', processed_dir), \
             patch('aggregate_metrics.METRIC_FILES', {
                 name: processed_dir / filename 
                 for name, filename in zip(
                     ["readability", "sentiment", "density", "churn", "complexity", "bug_fix_rate"],
                     ["readability.json", "sentiment.json", "density.json", "churn.json", "complexity.json", "quality_rate.json"]
                 )
             }), \
             patch('aggregate_metrics.logger') as mock_logger:
            
                aggregate_metrics()
                
                # Should log warning about no data
                mock_logger.warning.assert_called()