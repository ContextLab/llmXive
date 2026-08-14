"""
Unit tests for bootstrap resampling functionality.

These tests verify:
1. Correct bootstrap resampling logic
2. Confidence interval calculation
3. Proper handling of edge cases
"""
import os
import sys
import json
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.bootstrap import run_bootstrap_resampling, load_correlation_data


class TestBootstrapResampling:
    """Tests for bootstrap resampling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "test_correlation.csv")
        self.output_file = os.path.join(self.temp_dir, "test_bootstrap.json")
        
        # Create sample correlation data
        self.sample_data = pd.DataFrame({
            'species': ['proton', 'proton', 'helium', 'helium'],
            'rigidity': [1.0, 2.0, 1.0, 2.0],
            'lag_months': [-6, -6, -6, -6],
            'correlation': [-0.85, -0.72, -0.91, -0.68],
            'p_value': [0.001, 0.005, 0.0001, 0.008]
        })
        
        # Save sample data
        self.sample_data.to_csv(self.input_file, index=False)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_bootstrap_runs_successfully(self):
        """Test that bootstrap resampling runs without errors."""
        results = run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,  # Reduced for faster testing
            seed=42
        )
        
        assert results is not None
        assert 'results' in results
        assert 'bootstrap_parameters' in results
        assert results['bootstrap_parameters']['n_iterations'] == 100
    
    def test_output_file_created(self):
        """Test that output file is created."""
        run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,
            seed=42
        )
        
        assert os.path.exists(self.output_file)
    
    def test_confidence_intervals_calculated(self):
        """Test that confidence intervals are properly calculated."""
        results = run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,
            confidence_level=0.95,
            seed=42
        )
        
        for key, res in results['results'].items():
            assert 'ci_lower' in res
            assert 'ci_upper' in res
            assert 'original_max_correlation' in res
            
            # CI lower should be <= CI upper
            assert res['ci_lower'] <= res['ci_upper']
    
    def test_multiple_species_processed(self):
        """Test that multiple species are processed correctly."""
        results = run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,
            seed=42
        )
        
        # Should have results for both proton and helium
        species_keys = [k for k in results['results'].keys() if 'proton' in k or 'helium' in k]
        assert len(species_keys) >= 2
    
    def test_rigidity_bins_processed(self):
        """Test that different rigidity bins are processed separately."""
        results = run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,
            seed=42
        )
        
        # Check that we have results for different rigidity values
        rigidity_values = set()
        for key in results['results'].keys():
            parts = key.split('_')
            if len(parts) >= 2:
                try:
                    rigidity = float(parts[1])
                    rigidity_values.add(rigidity)
                except ValueError:
                    pass
        
        # Should have at least 2 different rigidity values
        assert len(rigidity_values) >= 2
    
    def test_bootstrap_mean_and_std(self):
        """Test that bootstrap mean and standard deviation are calculated."""
        results = run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=100,
            seed=42
        )
        
        for key, res in results['results'].items():
            assert 'bootstrap_mean' in res
            assert 'bootstrap_std' in res
            assert isinstance(res['bootstrap_mean'], float)
            assert isinstance(res['bootstrap_std'], float)
    
    def test_seed_reproducibility(self):
        """Test that results are reproducible with the same seed."""
        # Run twice with same seed
        run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=50,
            seed=123
        )
        
        with open(self.output_file, 'r') as f:
            results1 = json.load(f)
        
        # Run again with same seed
        run_bootstrap_resampling(
            input_path=self.input_file,
            output_path=self.output_file,
            n_iterations=50,
            seed=123
        )
        
        with open(self.output_file, 'r') as f:
            results2 = json.load(f)
        
        # Results should be identical
        for key in results1['results']:
            assert results1['results'][key]['ci_lower'] == results2['results'][key]['ci_lower']
            assert results1['results'][key]['ci_upper'] == results2['results'][key]['ci_upper']
    
    def test_insufficient_data_handling(self):
        """Test handling of groups with insufficient data."""
        # Create data with only one sample for a group
        insufficient_data = pd.DataFrame({
            'species': ['proton', 'helium'],
            'rigidity': [1.0, 1.0],
            'lag_months': [-6, -6],
            'correlation': [-0.85, -0.91],
            'p_value': [0.001, 0.0001]
        })
        
        temp_file = os.path.join(self.temp_dir, "insufficient.csv")
        insufficient_data.to_csv(temp_file, index=False)
        
        # This should still run but warn about insufficient data
        results = run_bootstrap_resampling(
            input_path=temp_file,
            output_path=self.output_file,
            n_iterations=50,
            seed=42
        )
        
        # Should still produce some results
        assert 'results' in results
    
    def test_invalid_input_file(self):
        """Test handling of non-existent input file."""
        with pytest.raises(FileNotFoundError):
            run_bootstrap_resampling(
                input_path="/nonexistent/file.csv",
                output_path=self.output_file,
                n_iterations=100
            )
    
    def test_empty_input_file(self):
        """Test handling of empty input file."""
        empty_file = os.path.join(self.temp_dir, "empty.csv")
        with open(empty_file, 'w') as f:
            f.write("")
        
        with pytest.raises(ValueError):
            run_bootstrap_resampling(
                input_path=empty_file,
                output_path=self.output_file,
                n_iterations=100
            )
    
    def test_missing_columns(self):
        """Test handling of missing required columns."""
        incomplete_data = pd.DataFrame({
            'species': ['proton'],
            'rigidity': [1.0]
            # Missing lag_months, correlation, p_value
        })
        
        temp_file = os.path.join(self.temp_dir, "incomplete.csv")
        incomplete_data.to_csv(temp_file, index=False)
        
        with pytest.raises(ValueError):
            run_bootstrap_resampling(
                input_path=temp_file,
                output_path=self.output_file,
                n_iterations=100
            )
    
    def test_alternative_column_names(self):
        """Test that alternative column names are handled."""
        # Create data with alternative column names
        alt_data = pd.DataFrame({
            'species_name': ['proton', 'helium'],
            'R': [1.0, 2.0],
            'lag': [-6, -6],
            'pearson_r': [-0.85, -0.91],
            'pval': [0.001, 0.0001]
        })
        
        temp_file = os.path.join(self.temp_dir, "alt_cols.csv")
        alt_data.to_csv(temp_file, index=False)
        
        # Should handle alternative column names
        results = run_bootstrap_resampling(
            input_path=temp_file,
            output_path=self.output_file,
            n_iterations=50,
            seed=42
        )
        
        assert 'results' in results
        assert len(results['results']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])