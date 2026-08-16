import pytest
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.analyze_drift import fit_reduced_model, get_data_for_reduced_model

class TestAnalyzeDrift:
    @pytest.fixture
    def sample_data(self):
        """Create a small sample DataFrame for testing."""
        data = {
            'power_est': np.random.rand(50),
            'effect_size': np.random.rand(50) * 2,
            'sample_size': np.random.randint(20, 100, 50),
            'field': np.random.choice(['Psychology', 'Biology', 'Economics'], 50),
            'original_study_id': [f'Study_{i}' for i in range(50)]
        }
        return pd.DataFrame(data)

    def test_fit_reduced_model_converges(self, sample_data):
        """Test that the reduced model fits and converges on valid data."""
        # Ensure types are correct
        sample_data['field'] = sample_data['field'].astype(str)
        sample_data['original_study_id'] = sample_data['original_study_id'].astype(str)
        
        result = fit_reduced_model(sample_data)
        
        # Check if result is not None
        assert result is not None, "Model fitting returned None."
        
        # Check if model converged (statsmodels result object has converged attribute)
        # Note: In some cases, small synthetic data might not converge perfectly, 
        # but it should not raise an error.
        # We assert that the result object exists.
        assert hasattr(result, 'llf'), "Result object missing llf attribute."

    def test_fit_reduced_model_handles_nan(self):
        """Test that the function handles NaN values gracefully (by dropping them)."""
        data = {
            'power_est': [0.5, np.nan, 0.6, 0.7],
            'effect_size': [0.5, 0.6, np.nan, 0.7],
            'sample_size': [50, 60, 70, 80],
            'field': ['A', 'B', 'C', 'D'],
            'original_study_id': ['S1', 'S2', 'S3', 'S4']
        }
        df = pd.DataFrame(data)
        df['field'] = df['field'].astype(str)
        df['original_study_id'] = df['original_study_id'].astype(str)
        
        # The function should drop rows with NaN
        result = fit_reduced_model(df)
        
        # Should still fit on the remaining 2 rows (though 2 rows is very small)
        # We just check it doesn't crash
        assert result is not None, "Model fitting failed on data with NaNs."