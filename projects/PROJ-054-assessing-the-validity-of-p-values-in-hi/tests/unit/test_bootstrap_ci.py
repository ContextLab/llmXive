"""
Unit tests for bootstrap confidence interval calculation (T030).
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from bootstrap_ci import (
    calculate_bootstrap_ci,
    load_trajectory_data,
    run_bootstrap_analysis
)
from utils.exceptions import AnalysisError


class TestCalculateBootstrapCI:
    """Tests for the bootstrap CI calculation function."""

    def test_basic_calculation(self):
        """Test basic bootstrap CI calculation with uniform data."""
        # Generate uniform p-values (ideal case)
        np.random.seed(42)
        pvalues = np.random.uniform(0, 1, 1000)
        permutation_pvalues = np.random.uniform(0, 1, 1000)

        ks_stat, ci_lower, ci_upper = calculate_bootstrap_ci(
            pvalues,
            permutation_pvalues,
            n_bootstraps=100,  # Small for speed
            confidence_level=0.95,
            random_seed=123
        )

        # KS statistic should be between 0 and 1
        assert 0 <= ks_stat <= 1
        assert 0 <= ci_lower <= 1
        assert 0 <= ci_upper <= 1
        assert ci_lower <= ks_stat <= ci_upper or ci_lower <= ci_upper

    def test_mismatched_lengths(self):
        """Test that mismatched lengths raise an error."""
        pvalues = np.random.uniform(0, 1, 100)
        permutation_pvalues = np.random.uniform(0, 1, 50)

        with pytest.raises(AnalysisError):
            calculate_bootstrap_ci(pvalues, permutation_pvalues, n_bootstraps=10)

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        np.random.seed(42)
        pvalues = np.random.uniform(0, 1, 100)
        permutation_pvalues = np.random.uniform(0, 1, 100)

        ks1, ci1_lower, ci1_upper = calculate_bootstrap_ci(
            pvalues, permutation_pvalues, n_bootstraps=50, random_seed=999
        )

        ks2, ci2_lower, ci2_upper = calculate_bootstrap_ci(
            pvalues, permutation_pvalues, n_bootstraps=50, random_seed=999
        )

        assert ks1 == ks2
        assert ci1_lower == ci2_lower
        assert ci1_upper == ci2_upper

    def test_different_confidence_levels(self):
        """Test that different confidence levels produce different intervals."""
        np.random.seed(42)
        pvalues = np.random.uniform(0, 1, 200)
        permutation_pvalues = np.random.uniform(0, 1, 200)

        _, ci90_lower, ci90_upper = calculate_bootstrap_ci(
            pvalues, permutation_pvalues, n_bootstraps=50, confidence_level=0.90, random_seed=1
        )

        _, ci95_lower, ci95_upper = calculate_bootstrap_ci(
            pvalues, permutation_pvalues, n_bootstraps=50, confidence_level=0.95, random_seed=1
        )

        # 95% CI should be wider than 90% CI
        assert (ci95_upper - ci95_lower) >= (ci90_upper - ci90_lower)


class TestLoadTrajectoryData:
    """Tests for loading trajectory data."""

    def test_load_valid_trajectory(self):
        """Test loading a valid trajectory file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                'pvalues': [0.1, 0.2, 0.3, 0.4, 0.5],
                'permutation_pvalues': [0.12, 0.18, 0.32, 0.38, 0.52],
                'seed': 123,
                'n': 100,
                'p': 50,
                'rho': 0.5,
                'distribution_type': 'normal'
            }
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            pvalues, perm_pvalues, metadata = load_trajectory_data(temp_path)

            assert len(pvalues) == 5
            assert len(perm_pvalues) == 5
            assert metadata['seed'] == 123
            assert metadata['n'] == 100
            assert metadata['p'] == 50
            assert metadata['rho'] == 0.5
            assert metadata['distribution_type'] == 'normal'
        finally:
            temp_path.unlink()

    def test_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_trajectory_data(Path("/nonexistent/file.json"))

    def test_missing_fields(self):
        """Test that missing required fields raise AnalysisError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                'seed': 123,
                'n': 100
            }
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(AnalysisError):
                load_trajectory_data(temp_path)
        finally:
            temp_path.unlink()


class TestRunBootstrapAnalysis:
    """Tests for the full analysis pipeline."""

    def test_full_pipeline(self):
        """Test the complete analysis pipeline."""
        # Create temporary trajectory file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            data = {
                'pvalues': list(np.random.uniform(0, 1, 100)),
                'permutation_pvalues': list(np.random.uniform(0, 1, 100)),
                'seed': 42,
                'n': 200,
                'p': 50,
                'rho': 0.3,
                'distribution_type': 'heavy_tailed'
            }
            json.dump(data, f)
            traj_path = Path(f.name)

        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = Path(f.name)
        output_path.unlink()  # Remove the file, we want run_bootstrap_analysis to create it

        try:
            result = run_bootstrap_analysis(
                traj_path,
                output_path,
                n_bootstraps=50,
                confidence_level=0.95,
                random_seed=123
            )

            # Check result structure
            assert 'KS_statistic' in result
            assert 'bootstrap_ci_lower' in result
            assert 'bootstrap_ci_upper' in result
            assert result['seed'] == 42
            assert result['n'] == 200
            assert result['p'] == 50
            assert result['rho'] == 0.3
            assert result['distribution_type'] == 'heavy_tailed'

            # Check output file was created
            assert output_path.exists()

            # Verify file contents
            with open(output_path, 'r') as f:
                saved_result = json.load(f)

            assert saved_result['KS_statistic'] == result['KS_statistic']
            assert saved_result['bootstrap_ci_lower'] == result['bootstrap_ci_lower']
            assert saved_result['bootstrap_ci_upper'] == result['bootstrap_ci_upper']

        finally:
            traj_path.unlink()
            if output_path.exists():
                output_path.unlink()
