import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import shutil

from collinearity import calculate_vif, run_pca_on_metrics, check_and_handle_collinearity, generate_descriptive_vif_report

class TestCollinearity:
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        # Ensure data/results directory exists for tests
        self.test_dir = Path("data/results")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup after test if needed
        if self.test_dir.exists():
            for f in self.test_dir.glob("*"):
                if f.is_file() and f.name.startswith("test_"):
                    f.unlink()

    def test_vif_calculation_returns_infinite_for_perfectly_collinear_predictors(self):
        """Test that VIF is infinite (or very high) for perfectly collinear predictors."""
        # Create a DataFrame with perfectly collinear columns
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # x2 = 2 * x1
            'x3': [1, 1, 1, 1, 1]   # constant
        })
        
        vif_dict = calculate_vif(df)
        
        # x2 should have very high VIF due to perfect collinearity with x1
        assert vif_dict['x2'] > 100 or np.isinf(vif_dict['x2']), "VIF should be very high for collinear predictors"
        
    def test_pca_fallback_triggers_when_vif_gt_5_and_variance_explained_gt_60(self):
        """Test that PCA is triggered when VIF > 5 and succeeds if variance explained > 60%."""
        # Create a DataFrame with some collinearity but still enough variance
        np.random.seed(42)
        n_samples = 100
        
        # Create correlated variables
        x1 = np.random.normal(0, 1, n_samples)
        x2 = x1 * 0.8 + np.random.normal(0, 0.5, n_samples)  # Correlated but not perfect
        x3 = np.random.normal(0, 1, n_samples)  # Independent
        
        df = pd.DataFrame({
            'global_efficiency': x1,
            'modularity': x2,
            'clustering': x3
        })
        
        # First check VIF
        vif_dict = calculate_vif(df)
        
        # If VIF > 5, PCA should be attempted
        max_vif = max(vif_dict.values())
        
        if max_vif > 5.0:
            pca, info = run_pca_on_metrics(df, ['global_efficiency', 'modularity', 'clustering'], variance_threshold=0.60)
            
            # If PCA succeeds, it should return a PCA object and variance > 0.60
            if info['success']:
                assert pca is not None
                assert info['variance_explained'] >= 0.60
            else:
                # If PCA fails, the info should reflect that
                assert info['success'] == False
                assert info['variance_explained'] < 0.60
        else:
            # If VIF is low, PCA might not be triggered, but the function should still work
            pca, info = run_pca_on_metrics(df, ['global_efficiency', 'modularity', 'clustering'], variance_threshold=0.60)
            # The function should not crash
            assert isinstance(info, dict)
    
    def test_descriptive_vif_report_contains_correlation_matrix(self):
        """Test that the descriptive VIF report contains a correlation matrix."""
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],
            'x3': [1, 3, 2, 4, 3]
        })
        
        report_path = self.test_dir / "test_descriptive_vif_report.json"
        report_data = generate_descriptive_vif_report(df, ['x1', 'x2', 'x3'], report_path)
        
        assert "correlation_matrix" in report_data
        assert "vif_values" in report_data
        assert "variance_decomposition" in report_data
        
        # Check that the correlation matrix is a dictionary of dictionaries
        corr_matrix = report_data["correlation_matrix"]
        assert isinstance(corr_matrix, dict)
        assert "x1" in corr_matrix
        assert isinstance(corr_matrix["x1"], dict)
        
        # Check that the file was created
        assert report_path.exists()
        
        # Load and verify the JSON
        with open(report_path, 'r') as f:
            loaded_report = json.load(f)
        
        assert loaded_report == report_data

    def test_check_and_handle_collinearity_handles_singular_matrix(self):
        """Test that collinearity check handles singular matrices gracefully."""
        # Create a DataFrame with a singular matrix (perfectly collinear)
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5],
            'x2': [2, 4, 6, 8, 10],  # Perfectly collinear
            'x3': [1, 1, 1, 1, 1]   # Constant
        })
        
        result = check_and_handle_collinearity(df, ['x1', 'x2', 'x3'])
        
        # Should not crash and should return a valid result
        assert "status" in result
        assert result["status"] in ["ok", "pca_success", "pca_failed_report_generated"]
        
        # If PCA failed, a report should be generated
        if result["status"] == "pca_failed_report_generated":
            assert "report_path" in result
            assert Path(result["report_path"]).exists()

    def test_vif_with_realistic_graph_metrics(self):
        """Test VIF calculation with realistic graph metrics data."""
        np.random.seed(42)
        n = 50
        
        # Simulate some realistic graph metrics with moderate correlation
        global_eff = np.random.normal(0.4, 0.1, n)
        local_eff = global_eff * 0.6 + np.random.normal(0, 0.05, n)  # Correlated
        modularity = np.random.normal(0.3, 0.05, n)  # Less correlated
        
        df = pd.DataFrame({
            'global_efficiency': global_eff,
            'local_efficiency': local_eff,
            'modularity': modularity
        })
        
        vif_dict = calculate_vif(df)
        
        # All VIFs should be finite
        for col, vif in vif_dict.items():
            assert np.isfinite(vif), f"VIF for {col} is not finite"
        
        # global_efficiency and local_efficiency should have higher VIF due to correlation
        assert vif_dict['global_efficiency'] > 1.0
        assert vif_dict['local_efficiency'] > 1.0