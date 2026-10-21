import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from code.sample_functions import sample_functions

def test_sample_functions_count():
    """Verify that the sampler returns exactly the target count."""
    # Mock dataset as an iterable of dictionaries
    mock_data = [{"code": f"def func_{i}(): pass", "repo": "test"} for i in range(1000)]
    
    with patch("code.sample_functions.load_dataset") as mock_load:
        mock_load.return_value = mock_data
        
        target_count = 800
        result = sample_functions(target_count=target_count, candidate_pool_limit=1000)
        
        assert len(result) == target_count
        assert all("code" in item for item in result)

def test_sample_functions_insufficient_data():
    """Verify that the sampler raises RuntimeError if not enough candidates are found."""
    mock_data = [{"code": f"def func_{i}(): pass"} for i in range(100)]
    
    with patch("code.sample_functions.load_dataset") as mock_load:
        mock_load.return_value = mock_data
        
        with pytest.raises(RuntimeError, match="Insufficient candidate functions"):
            sample_functions(target_count=800, candidate_pool_limit=1000)

def test_sample_functions_determinism():
    """Verify that the same seed produces the same sample."""
    mock_data = [{"code": f"def func_{i}(): pass"} for i in range(1000)]
    
    with patch("code.sample_functions.load_dataset") as mock_load:
        mock_load.return_value = mock_data
        
        res1 = sample_functions(seed=42, target_count=100, candidate_pool_limit=1000)
        res2 = sample_functions(seed=42, target_count=100, candidate_pool_limit=1000)
        
        assert res1 == res2