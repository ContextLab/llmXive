"""
Unit tests for QQ-plot generation functionality (T028).
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import os

from plot_qq import generate_qq_plot, load_pvalue_trajectories, aggregate_pvalues
from utils.exceptions import AnalysisError


class TestQQPlotGeneration:
    """Tests for QQ-plot generation functionality."""

    def test_generate_qq_plot_creates_file(self):
        """Test that generate_qq_plot creates the output file."""
        observed = np.random.uniform(0, 1, 100)
        permutation = np.random.uniform(0, 1, 100)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            generate_qq_plot(observed, permutation, str(output_path))
            
            assert output_path.exists(), "QQ-plot file was not created"
            assert output_path.stat().st_size > 0, "QQ-plot file is empty"

    def test_generate_qq_plot_empty_arrays_raises_error(self):
        """Test that empty p-value arrays raise AnalysisError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            
            with pytest.raises(AnalysisError):
                generate_qq_plot(np.array([]), np.random.uniform(0, 1, 100), str(output_path))
                
            with pytest.raises(AnalysisError):
                generate_qq_plot(np.random.uniform(0, 1, 100), np.array([]), str(output_path))

    def test_generate_qq_plot_single_value(self):
        """Test QQ-plot generation with minimal data."""
        observed = np.array([0.5])
        permutation = np.array([0.5])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            # Should not raise
            generate_qq_plot(observed, permutation, str(output_path))
            assert output_path.exists()

    def test_aggregate_pvalues_flattens_correctly(self):
        """Test that aggregate_pvalues correctly flattens nested lists."""
        trajectories = {
            "seed1": [[0.1, 0.2], [0.3, 0.4]],
            "seed2": [[0.5, 0.6]]
        }
        
        pvalues, seeds = aggregate_pvalues(trajectories)
        
        assert len(pvalues) == 5
        assert set(seeds) == {"seed1", "seed2"}
        assert np.allclose(sorted(pvalues), [0.1, 0.2, 0.3, 0.4, 0.5, 0.6])

    def test_load_pvalue_trajectories_missing_directory(self):
        """Test that missing trajectory directory raises AnalysisError."""
        with pytest.raises(AnalysisError):
            load_pvalue_trajectories("/nonexistent/path")

    def test_load_pvalue_trajectories_invalid_json_structure(self):
        """Test handling of JSON files without 'p_values' key."""
        with tempfile.TemporaryDirectory() as tmpdir:
            traj_dir = Path(tmpdir) / "synthetic" / "trajectories"
            traj_dir.mkdir(parents=True)
            
            # Create invalid JSON file
            invalid_file = traj_dir / "invalid.json"
            with open(invalid_file, 'w') as f:
                f.write('{"wrong_key": [1, 2, 3]}')
                
            # Should log warning but not raise
            result = load_pvalue_trajectories(tmpdir)
            assert result == {}  # No valid trajectories found

    def test_qq_plot_contains_expected_elements(self):
        """Test that generated plot contains expected visual elements."""
        observed = np.random.uniform(0, 1, 200)
        permutation = np.random.uniform(0, 1, 200)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_qq.png"
            generate_qq_plot(observed, permutation, str(output_path))
            
            # File exists and has content (basic validation)
            # More detailed validation would require image analysis
            assert output_path.stat().st_size > 1000  # PNG should be > 1KB

    def test_qq_plot_with_uniform_data(self):
        """Test QQ-plot with perfectly uniform data (should lie on diagonal)."""
        n = 1000
        observed = np.sort(np.random.uniform(0, 1, n))
        permutation = np.sort(np.random.uniform(0, 1, n))
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_uniform_qq.png"
            generate_qq_plot(observed, permutation, str(output_path))
            assert output_path.exists()

    def test_qq_plot_with_biased_data(self):
        """Test QQ-plot with anti-conservative (biased) p-values."""
        # Simulate anti-conservative p-values (too many small p-values)
        observed = np.concatenate([
            np.random.beta(0.5, 5, 500),  # Skewed toward 0
            np.random.uniform(0.1, 1, 500)
        ])
        permutation = np.random.uniform(0, 1, 1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_biased_qq.png"
            generate_qq_plot(observed, permutation, str(output_path))
            assert output_path.exists()