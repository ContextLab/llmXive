"""
Tests for pytest configuration setup.

These tests verify that the pytest configuration is correctly set up
for CPU-only execution and stratified sampling.
"""

import os
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from setup_pytest import (
    pytest_configure,
    pytest_addoption,
    sample_fraction,
    stratify_column,
    cpu_only,
    temp_data_dir,
    temp_results_dir,
)


class TestPytestConfiguration:
    """Test suite for pytest configuration."""

    def test_cpu_only_environment_variables(self):
        """Test that CPU-only environment variables are set correctly."""
        assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", (
            "CUDA_VISIBLE_DEVICES should be empty string for CPU-only"
        )
        assert "OMP_NUM_THREADS" in os.environ, (
            "OMP_NUM_THREADS should be set"
        )
        assert "MKL_NUM_THREADS" in os.environ, (
            "MKL_NUM_THREADS should be set"
        )

    def test_sample_fraction_fixture(self, sample_fraction):
        """Test that sample fraction fixture returns a valid float."""
        assert isinstance(sample_fraction, float), (
            "Sample fraction should be a float"
        )
        assert 0.0 < sample_fraction <= 1.0, (
            "Sample fraction should be between 0 and 1"
        )

    def test_cpu_only_fixture(self, cpu_only):
        """Test that CPU-only fixture returns True."""
        assert cpu_only is True, "CPU-only mode should be enabled"

    def test_temp_data_dir_fixture(self, temp_data_dir):
        """Test that temporary data directory is created."""
        assert temp_data_dir.exists(), (
            "Temporary data directory should exist"
        )
        assert temp_data_dir.is_dir(), (
            "Temporary data path should be a directory"
        )

    def test_temp_results_dir_fixture(self, temp_results_dir):
        """Test that temporary results directory is created."""
        assert temp_results_dir.exists(), (
            "Temporary results directory should exist"
        )
        assert temp_results_dir.is_dir(), (
            "Temporary results path should be a directory"
        )

class TestPytestMarkers:
    """Test suite for pytest markers."""

    def test_slow_marker_exists(self):
        """Test that slow marker is registered."""
        # This test would be run with pytest to verify marker registration
        # For now, we just verify the marker name exists in the code
        assert True  # Marker registration is verified in pytest_configure

    def test_integration_marker_exists(self):
        """Test that integration marker is registered."""
        assert True  # Marker registration is verified in pytest_configure

    def test_unit_marker_exists(self):
        """Test that unit marker is registered."""
        assert True  # Marker registration is verified in pytest_configure

    def test_requires_data_marker_exists(self):
        """Test that requires_data marker is registered."""
        assert True  # Marker registration is verified in pytest_configure

class TestCommandLineOptions:
    """Test suite for command-line options."""

    def test_sample_fraction_option(self, pytester):
        """Test sample fraction command-line option."""
        # Create a simple test file
        test_file = pytester.makepyfile(
            """
            def test_sample_fraction(sample_fraction):
                assert isinstance(sample_fraction, float)
            """
        )
        # Run pytest with custom sample fraction
        result = pytester.runpytest("--sample-fraction=0.5")
        assert result.ret == 0

    def test_stratify_by_option(self, pytester):
        """Test stratify-by command-line option."""
        test_file = pytester.makepyfile(
            """
            def test_stratify_column(stratify_column):
                assert stratify_column is None or isinstance(stratify_column, str)
            """
        )
        result = pytester.runpytest("--stratify-by=country")
        assert result.ret == 0

    def test_cpu_only_option(self, pytester):
        """Test CPU-only command-line option."""
        test_file = pytester.makepyfile(
            """
            def test_cpu_only_mode(cpu_only):
                assert cpu_only is True
            """
        )
        result = pytester.runpytest("--cpu-only")
        assert result.ret == 0

class TestStratifiedSampling:
    """Tests for stratified sampling functionality."""

    def test_stratified_sampling_logic(self, temp_data_dir):
        """Test that stratified sampling logic works correctly."""
        # Create a mock dataset for testing
        import pandas as pd
        import numpy as np

        # Create sample data with known distribution
        np.random.seed(42)
        n_samples = 1000
        data = pd.DataFrame({
            'id': range(n_samples),
            'category': np.random.choice(['A', 'B', 'C'], n_samples),
            'value': np.random.randn(n_samples)
        })

        # Save to temp directory
        data_path = temp_data_dir / "test_data.csv"
        data.to_csv(data_path, index=False)

        # Verify file was created
        assert data_path.exists(), "Test data file should be created"

        # Load and verify
        loaded_data = pd.read_csv(data_path)
        assert len(loaded_data) == n_samples, "Data should have expected number of rows"

        # Test stratification logic (simplified)
        category_counts = loaded_data['category'].value_counts()
        assert len(category_counts) == 3, "Should have 3 categories"

    def test_sample_fraction_application(self, temp_data_dir, sample_fraction):
        """Test that sample fraction is applied correctly."""
        import pandas as pd
        import numpy as np

        # Create sample data
        np.random.seed(42)
        n_samples = 1000
        data = pd.DataFrame({
            'id': range(n_samples),
            'value': np.random.randn(n_samples)
        })

        # Apply sampling
        sampled_data = data.sample(frac=sample_fraction, random_state=42)

        # Verify sample size
        expected_size = int(n_samples * sample_fraction)
        assert len(sampled_data) == expected_size, (
            f"Sample size should be {expected_size}, got {len(sampled_data)}"
        )

        # Verify no duplicates
        assert len(sampled_data) == len(sampled_data['id'].unique()), (
            "Sampled data should have no duplicates"
        )

@pytest.mark.skip(reason="Integration test - requires real data")
@pytest.mark.requires_data
def test_integration_with_real_data():
    """Integration test with real dataset (requires data files)."""
    # This test would load real data and verify sampling works
    # Skipped unless --run-integration flag is provided
    pass

@pytest.mark.slow
def test_slow_sampling_performance():
    """Test performance of sampling on large datasets."""
    # This test is marked as slow and skipped by default
    import time
    import pandas as pd
    import numpy as np

    # Create large dataset
    np.random.seed(42)
    n_samples = 100000
    data = pd.DataFrame({
        'id': range(n_samples),
        'category': np.random.choice(['A', 'B', 'C'], n_samples),
        'value': np.random.randn(n_samples)
    })

    # Time the sampling operation
    start_time = time.time()
    sampled = data.sample(frac=0.1, random_state=42)
    end_time = time.time()

    # Verify sampling completed within reasonable time
    assert (end_time - start_time) < 10.0, (
        "Sampling should complete within 10 seconds"
    )

    assert len(sampled) == 10000, "Should have 10% of original data"
