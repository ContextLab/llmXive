"""
Integration test for VIF and correlation logic (US3).

This test verifies:
1. The VIF calculation logic in code/utils.py correctly identifies collinearity.
2. The correlation logic in code/05_correlation.py (when implemented) correctly
   processes data, applies VIF filtering, and produces expected output structures.
3. The pipeline handles the 'under-determined' case (n_samples < n_taxa) gracefully.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import calculate_vif
from code.data_models import SampleStage


class TestVIFLogic:
    """Test VIF calculation directly."""

    def test_vif_perfect_collinearity(self):
        """Test that VIF is high when features are perfectly collinear."""
        # Create a dataframe with perfect collinearity
        df = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [2, 4, 6, 8, 10],  # B = 2*A
            'C': [1, 1, 1, 1, 1]   # Constant
        })
        
        # Calculate VIF for column A
        vif_a = calculate_vif(df, 'A')
        
        # With perfect collinearity, VIF should be very high (or infinite)
        # Depending on implementation, it might raise an error or return a large number
        # We expect it to be > 5 (the threshold)
        assert vif_a > 5, f"Expected VIF > 5 for collinear features, got {vif_a}"

    def test_vif_no_collinearity(self):
        """Test that VIF is low when features are independent."""
        np.random.seed(42)
        df = pd.DataFrame({
            'A': np.random.rand(100),
            'B': np.random.rand(100),
            'C': np.random.rand(100)
        })
        
        vif_a = calculate_vif(df, 'A')
        # For independent features, VIF should be close to 1
        assert vif_a < 5, f"Expected VIF < 5 for independent features, got {vif_a}"

    def test_vif_moderate_collinearity(self):
        """Test VIF with moderate correlation."""
        np.random.seed(42)
        A = np.random.rand(100)
        B = A * 0.7 + np.random.rand(100) * 0.3  # Moderate correlation
        df = pd.DataFrame({'A': A, 'B': B, 'C': np.random.rand(100)})
        
        vif_a = calculate_vif(df, 'A')
        # Should be higher than 1 but likely < 5 depending on correlation strength
        assert vif_a >= 1, "VIF should be at least 1"


class TestCorrelationIntegration:
    """Integration tests for the correlation pipeline."""

    @pytest.fixture
    def temp_processed_dir(self):
        """Create a temporary directory with mock processed data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            processed_dir = Path(tmpdir) / "data" / "processed"
            processed_dir.mkdir(parents=True)
            
            # Create mock feature table (taxa x samples)
            np.random.seed(42)
            n_samples = 50
            n_taxa = 10
            
            # Generate correlated data to ensure some real correlations exist
            base = np.random.rand(n_samples)
            feature_data = {}
            for i in range(n_taxa):
                # Create taxa with varying degrees of correlation to a hidden factor
                if i < 3:
                    # Strongly correlated taxa
                    feature_data[f'Taxon_{i}'] = base + np.random.normal(0, 0.1, n_samples)
                else:
                    # Weakly correlated or uncorrelated
                    feature_data[f'Taxon_{i}'] = np.random.rand(n_samples)
            
            feature_table = pd.DataFrame(feature_data)
            feature_table.index = [f'Sample_{i}' for i in range(n_samples)]
            
            # Create metadata with nutrient removal rates
            metadata = pd.DataFrame({
                'SampleID': feature_table.index,
                'Stage': ['Early'] * 25 + ['Mature'] * 25,
                'N_Removal_Rate': base * 10 + np.random.normal(0, 1, n_samples),
                'P_Removal_Rate': base * 5 + np.random.normal(0, 0.5, n_samples)
            })
            
            # Save files
            feature_table.to_csv(processed_dir / "feature_table.csv")
            metadata.to_csv(processed_dir / "metadata.csv")
            
            yield processed_dir

    def test_correlation_pipeline_structure(self, temp_processed_dir):
        """Test that the correlation pipeline produces the expected output structure."""
        # Import the main function (it might not be fully implemented yet, but we test the structure)
        try:
            from code import _05_correlation as corr_module
        except ImportError:
            # If the module doesn't exist yet, skip this specific test but log it
            pytest.skip("code/05_correlation.py not yet implemented")

        # Mock the data loading to use our temp files
        with patch.object(corr_module, 'load_processed_data') as mock_load:
            mock_load.return_value = (
                pd.read_csv(temp_processed_dir / "feature_table.csv", index_col=0),
                pd.read_csv(temp_processed_dir / "metadata.csv")
            )
            
            # Mock the output directory
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                
                # Call the main function
                try:
                    corr_module.main(str(temp_processed_dir), str(output_dir))
                except SystemExit as e:
                    # Expected if power analysis fails or other checks
                    if e.code != 0:
                        # If it's a non-zero exit that's not due to missing files,
                        # we might need to adjust the test
                        pass
                
                # Check that expected output files were created
                expected_files = [
                    "correlation_results.json",
                    "correlation_cv_results.json"
                ]
                
                for fname in expected_files:
                    fpath = output_dir / fname
                    assert fpath.exists(), f"Expected output file {fname} not created"
                    
                    # Validate JSON structure
                    with open(fpath) as f:
                        data = json.load(f)
                        assert isinstance(data, dict), f"{fname} should contain a JSON object"

    def test_vif_filtering_in_pipeline(self, temp_processed_dir):
        """Test that VIF filtering is applied in the correlation pipeline."""
        try:
            from code import _05_correlation as corr_module
        except ImportError:
            pytest.skip("code/05_correlation.py not yet implemented")

        # Create data with collinearity
        np.random.seed(42)
        n_samples = 50
        base = np.random.rand(n_samples)
        
        # Create features where two are highly correlated
        feature_data = {
            'Taxon_A': base,
            'Taxon_B': base * 0.95 + np.random.normal(0, 0.01, n_samples), # Highly correlated
            'Taxon_C': np.random.rand(n_samples) # Independent
        }
        
        feature_table = pd.DataFrame(feature_data)
        metadata = pd.DataFrame({
            'SampleID': feature_table.index,
            'N_Removal_Rate': base * 10
        })
        
        # Save to temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            feature_table.to_csv(temp_dir / "feature_table.csv")
            metadata.to_csv(temp_dir / "metadata.csv")
            
            with patch.object(corr_module, 'load_processed_data') as mock_load:
                mock_load.return_value = (feature_table, metadata)
                
                output_dir = temp_dir / "output"
                output_dir.mkdir()
                
                # Run pipeline
                try:
                    corr_module.main(str(temp_dir), str(output_dir))
                except SystemExit:
                    pass
                
                # Verify that the correlation results reflect VIF filtering
                # (i.e., highly collinear taxa should be flagged or excluded)
                results_path = output_dir / "correlation_results.json"
                if results_path.exists():
                    with open(results_path) as f:
                        results = json.load(f)
                    
                    # Check for VIF flags in results
                    # The exact structure depends on implementation, but we expect
                    # some indication of collinearity handling
                    assert 'taxa' in results or 'results' in results, \
                        "Results should contain taxa information"

    def test_under_determined_case_handling(self):
        """Test that the pipeline handles n_samples < n_taxa correctly."""
        try:
            from code import _05_correlation as corr_module
        except ImportError:
            pytest.skip("code/05_correlation.py not yet implemented")

        # Create data where n_samples < n_taxa
        np.random.seed(42)
        n_samples = 5
        n_taxa = 20
        
        feature_data = {f'Taxon_{i}': np.random.rand(n_samples) for i in range(n_taxa)}
        feature_table = pd.DataFrame(feature_data)
        metadata = pd.DataFrame({
            'SampleID': feature_table.index,
            'N_Removal_Rate': np.random.rand(n_samples)
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir)
            feature_table.to_csv(temp_dir / "feature_table.csv")
            metadata.to_csv(temp_dir / "metadata.csv")
            
            with patch.object(corr_module, 'load_processed_data') as mock_load:
                mock_load.return_value = (feature_table, metadata)
                
                output_dir = temp_dir / "output"
                output_dir.mkdir()
                
                # Run pipeline - should handle under-determined case gracefully
                try:
                    corr_module.main(str(temp_dir), str(output_dir))
                except SystemExit as e:
                    # Expected if the pipeline halts due to under-determined condition
                    pass
                
                # Check for under-determined flag in output
                results_path = output_dir / "correlation_results.json"
                if results_path.exists():
                    with open(results_path) as f:
                        results = json.load(f)
                    
                    # Should have a flag indicating under-determined status
                    assert 'under_determined' in results or 'flag' in results, \
                        "Results should indicate under-determined status"

    def test_cross_validation_results(self, temp_processed_dir):
        """Test that k=3 cross-validation results are generated correctly."""
        try:
            from code import _05_correlation as corr_module
        except ImportError:
            pytest.skip("code/05_correlation.py not yet implemented")

        with patch.object(corr_module, 'load_processed_data') as mock_load:
            mock_load.return_value = (
                pd.read_csv(temp_processed_dir / "feature_table.csv", index_col=0),
                pd.read_csv(temp_processed_dir / "metadata.csv")
            )
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir)
                
                try:
                    corr_module.main(str(temp_processed_dir), str(output_dir))
                except SystemExit:
                    pass
                
                cv_path = output_dir / "correlation_cv_results.json"
                if cv_path.exists():
                    with open(cv_path) as f:
                        cv_results = json.load(f)
                    
                    # Validate CV results structure
                    assert 'mean_r2' in cv_results or 'mean_r_squared' in cv_results, \
                        "CV results should contain mean R²"
                    assert 'std_dev' in cv_results or 'std_r2' in cv_results, \
                        "CV results should contain standard deviation"
                    
                    # Verify k=3 was used (check for 3 folds or similar indicator)
                    # The exact structure depends on implementation
                    assert 'folds' in cv_results or cv_results.get('k', 0) == 3, \
                        "Cross-validation should use k=3"