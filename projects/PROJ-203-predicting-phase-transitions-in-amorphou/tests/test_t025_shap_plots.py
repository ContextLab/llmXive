import pytest
import os
import sys
import json
from pathlib import Path
import pandas as pd
import numpy as np
import tempfile
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.generate_shap_plots import (
    load_models,
    load_dataset,
    get_family_mask,
    generate_family_shap_plots,
    main
)
from config import get_config, reset_config

class TestT025SHAPPlots:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories and mock config for testing."""
        # Save original config
        self.original_config = get_config()
        
        # Create a temporary directory structure
        self.test_dir = tmp_path / "test_t025"
        self.test_dir.mkdir()
        
        data_dir = self.test_dir / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        model_dir = self.test_dir / "models"
        model_dir.mkdir()
        
        report_dir = self.test_dir / "docs" / "reports"
        report_dir.mkdir(parents=True)
        
        # Mock the config
        # We cannot easily mock the global get_config() without patching the module
        # Instead, we rely on the fact that the test environment might have 
        # a .env file or we patch the function directly in the module.
        # For this unit test, we will test the helper functions that don't rely on global config
        # or we assume the environment is set up correctly for the 'main' test.
        
        yield
        
        # Cleanup
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_get_family_mask(self):
        """Test the family mask generation logic."""
        data = {
            'chemical_family': ['oxide', 'sulfide', 'oxide', 'organic'],
            'val': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        mask = get_family_mask(df, 'oxide')
        expected = pd.Series([True, False, True, False])
        pd.testing.assert_series_equal(mask, expected)
        
        with pytest.raises(KeyError):
            get_family_mask(df, 'non_existent_col')

    def test_generate_family_shap_plots_structure(self, tmp_path):
        """Test that the function creates the expected directory structure and files."""
        # Create a minimal mock dataset and model for testing
        # Since SHAP requires a real model, we create a dummy Random Forest
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.datasets import make_regression
        
        X, y = make_regression(n_samples=50, n_features=5, random_state=42)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        # Create a mock dataframe
        feature_names = [f"feat_{i}" for i in range(5)]
        df = pd.DataFrame(X, columns=feature_names)
        df['chemical_family'] = ['family_A'] * 25 + ['family_B'] * 25
        # Add target for completeness
        df['Tg_exp'] = y
        
        output_dir = tmp_path / "shap_plots"
        output_dir.mkdir()
        
        # Run the function for one family
        artifacts = generate_family_shap_plots(
            model=model,
            df=df,
            family_name='family_A',
            output_dir=output_dir,
            feature_names=feature_names,
            model_type='regressor'
        )
        
        # Verify artifacts
        assert 'summary_plot' in artifacts
        assert 'importance_plot' in artifacts
        assert 'ranked_features' in artifacts
        
        # Check files exist
        assert Path(artifacts['summary_plot']).exists()
        assert Path(artifacts['importance_plot']).exists()
        assert Path(artifacts['ranked_features']).exists()
        
        # Check JSON content
        with open(artifacts['ranked_features'], 'r') as f:
            ranked_data = json.load(f)
        assert isinstance(ranked_data, list)
        assert len(ranked_data) == len(feature_names)
        assert all('rank' in item and 'feature' in item and 'mean_abs_shap' in item for item in ranked_data)

    def test_empty_family_handling(self, tmp_path):
        """Test that empty families return empty dict without error."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.datasets import make_regression
        
        X, y = make_regression(n_samples=10, n_features=2, random_state=42)
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        df = pd.DataFrame(X, columns=['f1', 'f2'])
        df['chemical_family'] = ['family_A'] * 10
        
        output_dir = tmp_path / "shap_plots"
        output_dir.mkdir()
        
        # Request a family that doesn't exist
        artifacts = generate_family_shap_plots(
            model=model,
            df=df,
            family_name='non_existent',
            output_dir=output_dir,
            feature_names=['f1', 'f2'],
            model_type='regressor'
        )
        
        assert artifacts == {}
        
    def test_small_sample_handling(self, tmp_path):
        """Test that families with < 2 samples are skipped."""
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.datasets import make_regression
        
        X, y = make_regression(n_samples=10, n_features=2, random_state=42)
        model = RandomForestRegressor(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        df = pd.DataFrame(X, columns=['f1', 'f2'])
        df['chemical_family'] = ['family_A'] * 10 + ['family_B'] * 0 # Only A exists effectively, but let's force a split
        # Actually, let's make one family have 1 sample
        df.loc[0, 'chemical_family'] = 'family_B'
        
        output_dir = tmp_path / "shap_plots"
        output_dir.mkdir()
        
        # This should run without crashing, but family_B might be skipped due to <2 samples
        artifacts = generate_family_shap_plots(
            model=model,
            df=df,
            family_name='family_B',
            output_dir=output_dir,
            feature_names=['f1', 'f2'],
            model_type='regressor'
        )
        
        # Should return empty if skipped
        assert artifacts == {}
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])