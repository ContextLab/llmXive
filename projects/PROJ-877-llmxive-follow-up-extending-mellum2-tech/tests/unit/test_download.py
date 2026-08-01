"""
Unit tests for code/data/download.py (T015).

Tests:
- test_download_handles_network_timeout: Simulates network timeout during fetch.
- test_download_handles_empty_dataset: Simulates empty dataset response.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import sys
from pathlib import Path
import json
import tempfile
import os

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import NetworkError

class MockDataset:
    """Mock Hugging Face dataset for testing."""
    def __init__(self, items=None, raise_on_iter=False):
        self.items = items or []
        self.raise_on_iter = raise_on_iter
        self.iterated = False
    
    def __iter__(self):
        if self.raise_on_iter:
            raise Exception("Network timeout or error")
        self.iterated = True
        return iter(self.items)
    
    def take(self, n):
        return MockDataset(items=self.items[:n], raise_on_iter=self.raise_on_iter)

def test_download_handles_network_timeout():
    """
    Test that download.py handles network timeouts gracefully.
    
    Expected behavior:
    - Should raise NetworkError when dataset fetch fails.
    - Should NOT return synthetic data.
    """
    with patch("datasets.load_dataset") as mock_load:
        # Simulate network timeout
        mock_load.side_effect = Exception("Connection timeout")
        
        # Import main function
        from code.data.download import fetch_dataset_subset
        
        # Should raise NetworkError (wrapped)
        with pytest.raises(NetworkError):
            fetch_dataset_subset(capped_n=10, languages=["python"])

def test_download_handles_empty_dataset():
    """
    Test that download.py handles empty dataset response.
    
    Expected behavior:
    - Should return empty list if no chunks match.
    - Should NOT return synthetic data.
    """
    with patch("datasets.load_dataset") as mock_load:
        # Return empty dataset
        mock_load.return_value = MockDataset(items=[])
        
        from code.data.download import fetch_dataset_subset
        
        # Should return empty list
        result = fetch_dataset_subset(capped_n=10, languages=["python"])
        assert result == []

def test_download_filters_languages():
    """Test that download correctly filters by language."""
    with patch("datasets.load_dataset") as mock_load:
        # Create mock items with different languages
        items = [
            {"language": "python", "code": "print('hello')"},
            {"language": "java", "code": "System.out.println('hello')"},
            {"language": "python", "code": "x = 1"},
            {"language": "cpp", "code": "cout << 'hello';"},
        ]
        mock_load.return_value = MockDataset(items=items)
        
        from code.data.download import fetch_dataset_subset
        
        # Fetch only python
        result = fetch_dataset_subset(capped_n=10, languages=["python"])
        assert len(result) == 2
        assert all(item["language"] == "python" for item in result)

def test_download_respects_capped_n():
    """Test that download respects the capped_N limit."""
    with patch("datasets.load_dataset") as mock_load:
        # Create more items than capped_n
        items = [
            {"language": "python", "code": f"code_{i}"}
            for i in range(100)
        ]
        mock_load.return_value = MockDataset(items=items)
        
        from code.data.download import fetch_dataset_subset
        
        # Fetch with capped_n=10
        result = fetch_dataset_subset(capped_n=10, languages=["python"])
        assert len(result) == 10

def test_load_feasibility_report_missing():
    """Test that load_feasibility_report raises error if report missing."""
    from code.data.download import load_feasibility_report
    
    with patch("code.data.download.get_config") as mock_config:
        mock_config.return_value = {"project_root": "/tmp/nonexistent"}
        
        with pytest.raises(FileNotFoundError):
            load_feasibility_report()

def test_load_feasibility_report_proceed_false():
    """Test that load_feasibility_report raises error if proceed_flag is False."""
    from code.data.download import load_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "feasibility_report.json"
        with open(report_path, 'w') as f:
            json.dump({"proceed_flag": False, "capped_N": 10}, f)
        
        with patch("code.data.download.get_config") as mock_config:
            mock_config.return_value = {"project_root": tmpdir}
            
            with pytest.raises(RuntimeError):
                load_feasibility_report()

def test_load_feasibility_report_success():
    """Test successful loading of feasibility report."""
    from code.data.download import load_feasibility_report
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "feasibility_report.json"
        with open(report_path, 'w') as f:
            json.dump({"proceed_flag": True, "capped_N": 50}, f)
        
        with patch("code.data.download.get_config") as mock_config:
            mock_config.return_value = {"project_root": tmpdir}
            
            report = load_feasibility_report()
            assert report["proceed_flag"] is True
            assert report["capped_N"] == 50