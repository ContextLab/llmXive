"""
Tests for T042c: Duration verification logic.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from verify_duration import assert_duration_limit, load_metrics, MAX_DURATION_SECONDS


class TestLoadMetrics:
    """Tests for load_metrics function."""
    
    def test_load_metrics_success(self, tmp_path):
        """Test successful loading of metrics file."""
        metrics_data = {
            "duration_seconds": 1000,
            "other_field": "value"
        }
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        result = load_metrics(metrics_file)
        assert result == metrics_data
        assert result['duration_seconds'] == 1000
    
    def test_load_metrics_file_not_found(self, tmp_path):
        """Test FileNotFoundError when metrics file doesn't exist."""
        non_existent = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_metrics(non_existent)


class TestAssertDurationLimit:
    """Tests for assert_duration_limit function."""
    
    def test_duration_within_limit(self, caplog):
        """Test that assertion passes when duration is within limit."""
        metrics = {"duration_seconds": 1000}
        
        # Should not raise
        result = assert_duration_limit(metrics, MagicMock())
        assert result is True
    
    def test_duration_exactly_at_limit(self, caplog):
        """Test that assertion passes when duration equals limit."""
        metrics = {"duration_seconds": MAX_DURATION_SECONDS}
        
        # Should not raise
        result = assert_duration_limit(metrics, MagicMock())
        assert result is True
    
    def test_duration_exceeds_limit(self, caplog):
        """Test that RuntimeError is raised when duration exceeds limit."""
        metrics = {"duration_seconds": MAX_DURATION_SECONDS + 1}
        
        with pytest.raises(RuntimeError) as exc_info:
            assert_duration_limit(metrics, MagicMock())
        
        assert "SC-004 VIOLATION" in str(exc_info.value)
    
    def test_missing_duration_field(self):
        """Test KeyError when duration_seconds is missing."""
        metrics = {"other_field": "value"}
        
        with pytest.raises(KeyError) as exc_info:
            assert_duration_limit(metrics, MagicMock())
        
        assert "duration_seconds" in str(exc_info.value)


class TestMain:
    """Tests for main function."""
    
    def test_main_success(self, tmp_path):
        """Test main function with valid metrics."""
        # Create mock metrics file
        metrics_data = {"duration_seconds": 1000}
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        # Mock get_output_path to return tmp_path
        with patch('verify_duration.get_output_path', return_value=tmp_path):
            exit_code = main()
        
        assert exit_code == 0
    
    def test_main_file_not_found(self, tmp_path):
        """Test main function when metrics file is missing."""
        with patch('verify_duration.get_output_path', return_value=tmp_path):
            exit_code = main()
        
        assert exit_code == 1
    
    def test_main_missing_field(self, tmp_path):
        """Test main function when metrics missing duration field."""
        metrics_data = {"other_field": "value"}
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        with patch('verify_duration.get_output_path', return_value=tmp_path):
            exit_code = main()
        
        assert exit_code == 1
    
    def test_main_duration_exceeded(self, tmp_path):
        """Test main function when duration exceeds limit."""
        metrics_data = {"duration_seconds": MAX_DURATION_SECONDS + 1000}
        metrics_file = tmp_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_data, f)
        
        with patch('verify_duration.get_output_path', return_value=tmp_path):
            exit_code = main()
        
        assert exit_code == 1