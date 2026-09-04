"""
Tests for download_utils.py to ensure it fetches real data and fails loudly.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.download_utils import (
    load_adult_data, 
    load_iris_data, 
    load_wine_data, 
    DataFetchError,
    _ensure_dataframe
)
import pandas as pd


class TestDataFetchError:
    """Tests for the DataFetchError exception."""
    
    def test_exception_instantiation(self):
        """Test that DataFetchError can be instantiated with a message."""
        error = DataFetchError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

class TestEnsureDataFrame:
    """Tests for the internal _ensure_dataframe helper."""
    
    def test_valid_input_conversion(self):
        """Test conversion of arrays to DataFrame."""
        import numpy as np
        X = np.array([[1, 2], [3, 4]])
        y = np.array([0, 1])
        
        df = _ensure_dataframe(X, y, "test")
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'target' in df.columns

    def test_empty_dataframe_raises(self):
        """Test that empty data raises DataFetchError."""
        X = pd.DataFrame()
        y = pd.Series()
        
        with pytest.raises(DataFetchError):
            _ensure_dataframe(X, y, "test")

class TestRealDataFetching:
    """Tests that verify real data fetching behavior."""
    
    @patch('code.data.download_utils.fetch_data')
    def test_adult_fetch_success(self, mock_fetch):
        """Test successful Adult data fetch."""
        mock_X = pd.DataFrame({'age': [30, 40], 'workclass': ['Gov', 'Priv']})
        mock_y = pd.Series([0, 1], name='target')
        mock_fetch.return_value = (mock_X, mock_y)
        
        df = load_adult_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'target' in df.columns
        mock_fetch.assert_called_once_with('adult', return_X_y=True)
    
    @patch('code.data.download_utils.fetch_data')
    def test_adult_fetch_failure_raises_error(self, mock_fetch):
        """Test that fetch failure raises DataFetchError, not synthetic fallback."""
        mock_fetch.side_effect = ConnectionError("Network error")
        
        with pytest.raises(DataFetchError) as exc_info:
            load_adult_data()
        
        assert "Failed to fetch 'adult' dataset" in str(exc_info.value)
        assert "Network error" in str(exc_info.value)
    
    @patch('code.data.download_utils.fetch_data')
    def test_iris_fetch_success(self, mock_fetch):
        """Test successful Iris data fetch."""
        mock_X = pd.DataFrame({'sepal_length': [5.1, 5.9]})
        mock_y = pd.Series([0, 1], name='target')
        mock_fetch.return_value = (mock_X, mock_y)
        
        df = load_iris_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        mock_fetch.assert_called_once_with('iris', return_X_y=True)
    
    @patch('code.data.download_utils.fetch_data')
    def test_wine_fetch_success(self, mock_fetch):
        """Test successful Wine data fetch."""
        mock_X = pd.DataFrame({'fixed_acidity': [7.4, 7.8]})
        mock_y = pd.Series([5, 6], name='target')
        mock_fetch.return_value = (mock_X, mock_y)
        
        df = load_wine_data()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        mock_fetch.assert_called_once_with('wine', return_X_y=True)

class TestNoSyntheticFallback:
    """Tests to ensure no synthetic fallback logic exists."""
    
    def test_no_synthetic_imports(self):
        """Verify that download_utils does not import synthetic generators."""
        import code.data.download_utils as module
        source = open(module.__file__).read()
        
        # Check for forbidden patterns that indicate synthetic fallback
        forbidden_patterns = [
            'generate_synthetic',
            'mock_data',
            'np.random.rand',
            'np.random.randn',
            'return mock',
            'fallback to synthetic'
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Found forbidden pattern '{pattern}' in download_utils.py"