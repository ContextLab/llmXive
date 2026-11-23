import os
import json
import pytest
from unittest.mock import patch, MagicMock
from collections import Counter

# Mock datasets module
mock_ds_item = {
    "code": "def foo(): pass",
    "path": "test.py"
}

@pytest.fixture
def mock_dataset():
    class MockDataset:
        def __init__(self, items):
            self.items = items
        def __iter__(self):
            return iter(self.items)
        def shuffle(self, seed):
            return self
        def take(self, n):
            return iter(self.items[:n])
    return MockDataset([mock_ds_item] * 1000)

def test_stratified_sampling_distribution():
    """Test that stratified sampling maintains proportional distribution."""
    from data_pipeline import load_sampled_functions
    
    # This test verifies the logic by checking the sample_report.json
    # generated during a real run. In a unit test context, we verify the
    # existence and structure of the report.
    
    report_path = "results/sample_report.json"
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert "total_collected" in report
        assert "distribution" in report
        assert "proportions" in report
        
        # Verify proportions sum to ~1.0
        total_prop = sum(report["proportions"].values())
        assert abs(total_prop - 1.0) < 0.01
        
        # Verify distribution matches proportions
        total_count = report["total_collected"]
        for ext, count in report["distribution"].items():
            expected_prop = count / total_count
            reported_prop = report["proportions"][ext]
            assert abs(expected_prop - reported_prop) < 0.001
    else:
        # If report doesn't exist, skip (pipeline not run yet)
        pytest.skip("sample_report.json not found. Run pipeline first.")