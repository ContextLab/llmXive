"""
Pytest configuration and fixtures for the project.

Provides shared fixtures for test data, temporary directories, and configuration.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Ensure the project root is in sys.path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_time_series_data():
    """Generate a simple sample time series for testing."""
    import numpy as np
    import pandas as pd
    
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    values = np.random.randn(100).cumsum()  # Random walk
    return pd.Series(values, index=dates)

@pytest.fixture
def sample_data_with_missing():
    """Generate a sample time series with missing values."""
    import numpy as np
    import pandas as pd
    
    dates = pd.date_range(start='2020-01-01', periods=100, freq='D')
    values = np.random.randn(100).cumsum()
    values[10:15] = np.nan  # Add some missing values
    values[50] = np.nan
    return pd.Series(values, index=dates)

@pytest.fixture
def mock_real_data_dir(temp_test_dir):
    """Create a mock real data directory with sample files."""
    data_dir = temp_test_dir / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a sample CSV file
    sample_file = data_dir / "sample_series.csv"
    import pandas as pd
    import numpy as np
    
    dates = pd.date_range(start='2020-01-01', periods=1000, freq='H')
    values = np.random.randn(1000).cumsum()
    df = pd.DataFrame({'value': values}, index=dates)
    df.to_csv(sample_file)
    
    return data_dir
