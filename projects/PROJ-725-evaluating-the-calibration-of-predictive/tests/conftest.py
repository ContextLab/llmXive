import pytest
import pandas as pd
import numpy as np

@pytest.fixture(scope="session")
def sample_regression_data():
    """Provides a small sample regression dataset for testing."""
    np.random.seed(42)  # Ensure reproducibility
    n_samples = 100
    X = np.random.rand(n_samples, 1)
    y = 2 * X.squeeze() + 1 + 0.1 * np.random.randn(n_samples)
    data = pd.DataFrame({'feature': X.flatten(), 'target': y})
    return data

@pytest.fixture(scope="session")
def sample_preprocessed_data():
  """Provides a preprocessed sample regression dataset."""
  from code.data.preprocessor import preprocess_dataset
  sample_data = sample_regression_data()
  preprocessed_data = preprocess_dataset(sample_data)
  return preprocessed_data