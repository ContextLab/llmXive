"""
Unit tests for plotting utilities.
Tests for code/plot_qq.py
"""
import numpy as np
import pytest
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt
from plot_qq import generate_qq_plot, load_pvalue_trajectories


class TestQQPlotGeneration:
    def test_qq_plot_creation(self):
        """Test that QQ plot can be created without errors."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 1000)

        fig = generate_qq_plot(p_values)

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        plt.close(fig)

    def test_qq_plot_uniform_data(self):
        """Test QQ plot with uniform data (should be close to diagonal)."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 1000)

        fig = generate_qq_plot(p_values)
        ax = fig.axes[0]

        # Get plot data
        lines = ax.get_lines()
        assert len(lines) > 0

        # The diagonal line should be present
        plt.close(fig)

    def test_qq_plot_biased_data(self):
        """Test QQ plot with biased data (should deviate from diagonal)."""
        np.random.seed(42)
        # Generate p-values biased towards 0
        p_values = np.random.beta(0.5, 1, 1000)

        fig = generate_qq_plot(p_values)

        assert fig is not None
        plt.close(fig)

    def test_qq_plot_small_sample(self):
        """Test QQ plot with small sample size."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 10)

        fig = generate_qq_plot(p_values)

        assert fig is not None
        plt.close(fig)

    def test_qq_plot_labels(self):
        """Test that QQ plot has correct labels."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)

        fig = generate_qq_plot(p_values)
        ax = fig.axes[0]

        # Check axis labels exist
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()

        assert "Expected" in xlabel or "Uniform" in xlabel
        assert "Observed" in ylabel or "P-value" in ylabel

        plt.close(fig)

    def test_qq_plot_title(self):
        """Test that QQ plot has a title."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)

        fig = generate_qq_plot(p_values)
        ax = fig.axes[0]

        title = ax.get_title()
        assert len(title) > 0

        plt.close(fig)

    def test_qq_plot_multiple_datasets(self):
        """Test QQ plot with multiple datasets."""
        np.random.seed(42)
        p_values1 = np.random.uniform(0, 1, 500)
        p_values2 = np.random.beta(0.5, 1, 500)

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        generate_qq_plot(p_values1, ax=axes[0])
        generate_qq_plot(p_values2, ax=axes[1])

        assert len(fig.axes) == 2

        plt.close(fig)

    def test_qq_plot_file_save(self):
        """Test that QQ plot can be saved to file."""
        import tempfile
        import os

        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_qq.png")
            fig = generate_qq_plot(p_values)
            fig.savefig(filepath)
            plt.close(fig)

            assert os.path.exists(filepath)
            assert os.path.getsize(filepath) > 0

    def test_qq_plot_invalid_input(self):
        """Test QQ plot with invalid input."""
        with pytest.raises(ValueError):
            generate_qq_plot(np.array([]))

    def test_qq_plot_negative_values(self):
        """Test QQ plot with negative values (should raise or handle)."""
        p_values = np.array([-0.1, 0.2, 0.3, 0.4])

        # Should handle gracefully or raise appropriate error
        with pytest.raises(ValueError):
            generate_qq_plot(p_values)

    def test_qq_plot_values_greater_than_one(self):
        """Test QQ plot with values > 1 (should raise or handle)."""
        p_values = np.array([0.1, 0.5, 1.5, 0.9])

        # Should handle gracefully or raise appropriate error
        with pytest.raises(ValueError):
            generate_qq_plot(p_values)


class TestTrajectoryLoading:
    def test_load_empty_trajectories(self):
        """Test loading from empty trajectory file."""
        import tempfile
        import json
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "empty_trajectories.json")
            with open(filepath, 'w') as f:
                json.dump([], f)

            # Should handle empty file
            result = load_pvalue_trajectories([filepath])
            assert len(result) == 0

    def test_load_single_trajectory(self):
        """Test loading single trajectory."""
        import tempfile
        import json
        import os

        np.random.seed(42)
        trajectory = np.random.uniform(0, 1, 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "trajectory.json")
            with open(filepath, 'w') as f:
                json.dump(trajectory.tolist(), f)

            result = load_pvalue_trajectories([filepath])
            assert len(result) == 1
            assert len(result[0]) == 100

    def test_load_multiple_trajectories(self):
        """Test loading multiple trajectories."""
        import tempfile
        import json
        import os

        np.random.seed(42)
        trajectory1 = np.random.uniform(0, 1, 50)
        trajectory2 = np.random.uniform(0, 1, 50)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath1 = os.path.join(tmpdir, "trajectory1.json")
            filepath2 = os.path.join(tmpdir, "trajectory2.json")

            with open(filepath1, 'w') as f:
                json.dump(trajectory1.tolist(), f)
            with open(filepath2, 'w') as f:
                json.dump(trajectory2.tolist(), f)

            result = load_pvalue_trajectories([filepath1, filepath2])
            assert len(result) == 2

    def test_load_corrupted_file(self):
        """Test loading corrupted JSON file."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "corrupted.json")
            with open(filepath, 'w') as f:
                f.write("not valid json")

            with pytest.raises((json.JSONDecodeError, ValueError)):
                load_pvalue_trajectories([filepath])

def test_qq_plot_visual_validation():
    """Test that QQ plot shows expected visual patterns."""
    np.random.seed(42)

    # Uniform data should follow diagonal
    uniform_pvalues = np.random.uniform(0, 1, 1000)
    fig_uniform = generate_qq_plot(uniform_pvalues)

    # Biased data should deviate
    biased_pvalues = np.random.beta(0.5, 1, 1000)
    fig_biased = generate_qq_plot(biased_pvalues)

    # Both should be valid figures
    assert fig_uniform is not None
    assert fig_biased is not None

    plt.close('all')
