"""Tests for scaling plot generation (T030)."""
import pytest
from pathlib import Path
import tempfile
import pandas as pd

from analysis.scaling_plot_generator import (
    generate_scaling_plot_with_notes,
    load_scaling_data_real,
    fit_power_law_with_ci,
    power_law
)


def test_power_law_function():
    """Test power-law function computes correctly."""
    x = np.array([2.0, 4.0, 8.0])
    y = power_law(x, a=1.0, b=0.85)
    expected = np.array([1.80, 3.23, 5.78])
    assert np.allclose(y, expected, rtol=0.01)


def test_load_scaling_data_real():
    """Test loading real scaling data from CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)

        # Create mock data files
        for count in [3, 5, 7]:
            df = pd.DataFrame({
                'game_id': [1, 2, 3],
                'specialization_index': [0.7, 0.6, 0.65],
                'retrieval_efficiency': [0.8, 0.75, 0.78],
                'context_condition': ['scaling', 'scaling', 'scaling'],
                'agent_count': [count, count, count]
            })
            df.to_csv(results_dir / f"results_scaling_{count}.csv", index=False)

        # Load and verify
        data = load_scaling_data_real(results_dir)
        assert len(data) == 3
        assert list(data['agent_count']) == [3, 5, 7]


def test_fit_power_law_with_ci():
    """Test power-law fitting returns valid results."""
    x_data = np.array([3, 5, 7])
    y_data = np.array([0.72, 0.65, 0.58])
    x_fit = np.linspace(3, 7, 50)

    fitted_y, exponent, ci = fit_power_law_with_ci(x_data, y_data, x_fit)

    assert len(fitted_y) == 50
    assert isinstance(exponent, float)
    assert isinstance(ci, float)
    assert ci >= 0  # Confidence interval should be non-negative


def test_generate_scaling_plot_with_notes():
    """Test full plot generation produces PDF with reliability note."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        output_path = Path(tmpdir) / "test_scaling_plot.pdf"

        # Create mock data
        for count in [3, 5, 7]:
            df = pd.DataFrame({
                'game_id': range(5),
                'specialization_index': [0.7 - count * 0.02, 0.68 - count * 0.02,
                                         0.72 - count * 0.02, 0.69 - count * 0.02,
                                         0.71 - count * 0.02],
                'retrieval_efficiency': [0.8 - count * 0.02, 0.78 - count * 0.02,
                                         0.82 - count * 0.02, 0.79 - count * 0.02,
                                         0.81 - count * 0.02],
                'context_condition': ['scaling'] * 5,
                'agent_count': [count] * 5
            })
            df.to_csv(results_dir / f"results_scaling_{count}.csv", index=False)

        # Generate plot
        result = generate_scaling_plot_with_notes(results_dir, output_path, num_points=3)

        # Verify output
        assert output_path.exists()
        assert result.plot_path == str(output_path)
        assert len(result.agent_counts) == 3
        assert result.fitted_exponent is not None
        assert "3 data points" in result.confidence_note
        assert "limited statistical reliability" in result.confidence_note