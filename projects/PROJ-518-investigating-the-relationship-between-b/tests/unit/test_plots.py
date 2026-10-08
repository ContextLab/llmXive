import os
import sys
import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add parent to path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from viz.plots import plot_residuals, RegressionResult

class TestPlotResiduals:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.residuals_path = os.path.join(self.temp_dir, 'model_residuals.png')
        self.qq_path = os.path.join(self.temp_dir, 'model_qq.png')
        
        # Create mock model data
        np.random.seed(42)
        n = 50
        self.fitted = np.random.normal(0, 1, n)
        self.residuals = np.random.normal(0, 0.5, n)
        
        self.mock_model = RegressionResult(
            coefficients={},
            r_squared=0.5,
            adjusted_r_squared=0.45,
            pearson_r=0.7,
            residuals=self.residuals,
            fitted_values=self.fitted
        )

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_plot_residuals_creates_files(self):
        """Test that plot_residuals creates the expected output files."""
        plot_residuals(self.mock_model, self.residuals_path, self.qq_path)
        
        assert os.path.exists(self.residuals_path), f"Residuals plot not found at {self.residuals_path}"
        assert os.path.exists(self.qq_path), f"QQ plot not found at {self.qq_path}"
        
        # Check file size > 0
        assert os.path.getsize(self.residuals_path) > 0, "Residuals plot is empty"
        assert os.path.getsize(self.qq_path) > 0, "QQ plot is empty"

    def test_plot_residuals_nan_handling(self):
        """Test that NaN values are filtered out without error."""
        # Inject NaNs
        fitted_with_nan = self.fitted.copy()
        residuals_with_nan = self.residuals.copy()
        fitted_with_nan[0] = np.nan
        residuals_with_nan[1] = np.nan
        
        model_with_nan = RegressionResult(
            coefficients={},
            r_squared=0.5,
            adjusted_r_squared=0.45,
            pearson_r=0.7,
            residuals=residuals_with_nan,
            fitted_values=fitted_with_nan
        )
        
        # Should not raise
        plot_residuals(model_with_nan, self.residuals_path, self.qq_path)
        
        assert os.path.exists(self.residuals_path)
        assert os.path.exists(self.qq_path)

    def test_plot_residuals_missing_data_raises(self):
        """Test that missing residuals/fitted values raise an error."""
        bad_model = RegressionResult(
            coefficients={},
            r_squared=0.5,
            adjusted_r_squared=0.45,
            pearson_r=0.7,
            residuals=None,
            fitted_values=self.fitted
        )
        
        with pytest.raises(ValueError, match="Model must contain"):
            plot_residuals(bad_model, self.residuals_path, self.qq_path)

class TestPlotFlexibilityVsCreativity:
    # Reuse logic from T022 tests if they exist, or basic check here
    pass