"""
Integration test for end-to-end analysis pipeline on a small synthetic dataset.

This test verifies the full flow of the analysis pipeline:
1. Loading data from a small, controlled synthetic dataset
2. Running correlation analysis
3. Running stratified analysis
4. Running sensitivity analysis
5. Running visualization generation

The synthetic dataset is generated locally for testing purposes only.
In production, this test would run against a small sample of real data.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np
import pytest

# Import the analysis modules we are testing
from src.analysis.correlation import run_correlation_analysis, calculate_spearman_correlation
from src.analysis.stratified_stats import run_stratified_analysis
from src.analysis.sensitivity_analysis import run_sensitivity_analysis
from src.analysis.visualizer import create_visualization_summary
from src.analysis.power import run_power_analysis


def generate_small_synthetic_dataset(num_samples: int = 100) -> pd.DataFrame:
    """
    Generate a small synthetic dataset for integration testing.

    This creates a controlled dataset with known properties to verify
    the analysis pipeline functions correctly.

    Args:
        num_samples: Number of rows to generate (default 100 for fast testing)

    Returns:
        DataFrame with columns: name, version, age_in_days, vulnerability_count, category
    """
    np.random.seed(42)  # Reproducibility

    data = {
        'name': [f"pkg_{i}" for i in range(num_samples)],
        'version': ['1.0.0'] * num_samples,
        'age_in_days': np.random.randint(30, 3650, size=num_samples),
        'vulnerability_count': np.random.poisson(lam=2.5, size=num_samples),
        'category': np.random.choice(['framework', 'data', 'utility', 'infrastructure'], size=num_samples)
    }

    df = pd.DataFrame(data)

    # Introduce some nulls in age_in_days to test handling
    null_indices = np.random.choice(num_samples, size=int(num_samples * 0.1), replace=False)
    df.loc[null_indices, 'age_in_days'] = np.nan

    return df


def test_correlation_analysis_pipeline():
    """Test the full correlation analysis pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate synthetic data
        df = generate_small_synthetic_dataset(num_samples=100)

        # Save to CSV
        input_file = tmpdir_path / "test_dependencies.csv"
        df.to_csv(input_file, index=False)

        # Run correlation analysis
        output_file = tmpdir_path / "test_results_correlation.json"
        result = run_correlation_analysis(
            input_path=str(input_file),
            output_path=str(output_file)
        )

        # Verify results
        assert result is not None, "Correlation analysis should return a result"
        assert 'correlation_coefficient' in result, "Result should contain correlation_coefficient"
        assert 'p_value' in result, "Result should contain p_value"
        assert 'sample_size' in result, "Result should contain sample_size"

        # Verify the values are within expected bounds
        assert -1.0 <= result['correlation_coefficient'] <= 1.0, "Correlation coefficient must be between -1 and 1"
        assert 0.0 <= result['p_value'] <= 1.0, "P-value must be between 0 and 1"
        assert result['sample_size'] > 0, "Sample size must be positive"

        # Verify the output file was written
        assert output_file.exists(), "Output JSON file should be created"

        # Verify the JSON content matches the result
        with open(output_file, 'r') as f:
            saved_result = json.load(f)
            assert saved_result['correlation_coefficient'] == result['correlation_coefficient']
            assert saved_result['p_value'] == result['p_value']


def test_stratified_analysis_pipeline():
    """Test the stratified analysis pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate synthetic data with distinct categories
        df = generate_small_synthetic_dataset(num_samples=150)

        # Save to CSV
        input_file = tmpdir_path / "test_dependencies.csv"
        df.to_csv(input_file, index=False)

        # Run stratified analysis
        output_file = tmpdir_path / "test_results_stratified.json"
        result = run_stratified_analysis(
            input_path=str(input_file),
            output_path=str(output_file)
        )

        # Verify results
        assert result is not None, "Stratified analysis should return a result"
        assert 'category_correlations' in result, "Result should contain category_correlations"
        assert 'overall_correlation' in result, "Result should contain overall_correlation"

        # Verify category correlations are present and valid
        category_corrs = result['category_correlations']
        assert isinstance(category_corrs, dict), "Category correlations should be a dictionary"
        assert len(category_corrs) > 0, "Should have at least one category"

        for category, values in category_corrs.items():
            assert 'correlation' in values, f"Category {category} should have correlation"
            assert 'p_value' in values, f"Category {category} should have p_value"
            assert 'sample_size' in values, f"Category {category} should have sample_size"

            # Only check bounds if sample_size is sufficient (>= 30 per spec)
            if values['sample_size'] >= 30:
                assert -1.0 <= values['correlation'] <= 1.0, f"Correlation for {category} must be between -1 and 1"
                assert 0.0 <= values['p_value'] <= 1.0, f"P-value for {category} must be between 0 and 1"

        # Verify the output file was written
        assert output_file.exists(), "Output JSON file should be created"


def test_sensitivity_analysis_pipeline():
    """Test the sensitivity analysis pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate synthetic data
        df = generate_small_synthetic_dataset(num_samples=100)

        # Save to CSV
        input_file = tmpdir_path / "test_dependencies.csv"
        df.to_csv(input_file, index=False)

        # Run sensitivity analysis
        output_file = tmpdir_path / "test_sensitivity.json"
        result = run_sensitivity_analysis(
            input_path=str(input_file),
            output_path=str(output_file)
        )

        # Verify results
        assert result is not None, "Sensitivity analysis should return a result"
        assert 'threshold_sweep' in result, "Result should contain threshold_sweep"

        # Verify threshold sweep structure
        threshold_sweep = result['threshold_sweep']
        assert isinstance(threshold_sweep, list), "Threshold sweep should be a list"
        assert len(threshold_sweep) > 0, "Threshold sweep should have at least one entry"

        for entry in threshold_sweep:
            assert 'threshold' in entry, "Each entry should have a threshold"
            assert 'unmaintained_proportion' in entry, "Each entry should have unmaintained_proportion"
            assert 'sample_size' in entry, "Each entry should have sample_size"

        # Verify the output file was written
        assert output_file.exists(), "Output JSON file should be created"


def test_power_analysis_pipeline():
    """Test the power analysis pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate synthetic data
        df = generate_small_synthetic_dataset(num_samples=100)

        # Save to CSV
        input_file = tmpdir_path / "test_dependencies.csv"
        df.to_csv(input_file, index=False)

        # Run power analysis
        output_file = tmpdir_path / "test_power_analysis.json"
        result = run_power_analysis(
            input_path=str(input_file),
            output_path=str(output_file)
        )

        # Verify results
        assert result is not None, "Power analysis should return a result"
        assert 'effect_size' in result, "Result should contain effect_size"
        assert 'alpha' in result, "Result should contain alpha"
        assert 'sample_size' in result, "Result should contain sample_size"
        assert 'actual_power' in result, "Result should contain actual_power"

        # Verify values are within expected bounds
        assert 0.0 <= result['alpha'] <= 1.0, "Alpha must be between 0 and 1"
        assert 0.0 <= result['actual_power'] <= 1.0, "Actual power must be between 0 and 1"
        assert result['sample_size'] > 0, "Sample size must be positive"

        # Verify the output file was written
        assert output_file.exists(), "Output JSON file should be created"


def test_visualization_pipeline():
    """Test the visualization pipeline end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate synthetic data
        df = generate_small_synthetic_dataset(num_samples=100)

        # Save to CSV
        input_file = tmpdir_path / "test_dependencies.csv"
        df.to_csv(input_file, index=False)

        # Create output directory for figures
        figures_dir = tmpdir_path / "figures"
        figures_dir.mkdir()

        # Run visualization
        output_summary = tmpdir_path / "visualization_summary.json"
        result = create_visualization_summary(
            input_path=str(input_file),
            output_dir=str(figures_dir),
            summary_path=str(output_summary)
        )

        # Verify results
        assert result is not None, "Visualization should return a result"
        assert 'plots_generated' in result, "Result should contain plots_generated"
        assert 'summary_file' in result, "Result should contain summary_file"

        # Verify plots were generated
        plots = result['plots_generated']
        assert isinstance(plots, list), "Plots should be a list"
        assert len(plots) > 0, "At least one plot should be generated"

        for plot in plots:
            assert 'filename' in plot, "Each plot should have a filename"
            assert 'description' in plot, "Each plot should have a description"

            # Verify the plot file exists
            plot_path = figures_dir / plot['filename']
            assert plot_path.exists(), f"Plot file {plot['filename']} should exist"

        # Verify the summary file was written
        assert output_summary.exists(), "Summary JSON file should be created"


def test_full_integration_pipeline():
    """
    Test the complete end-to-end pipeline: data -> correlation -> stratified -> sensitivity -> visualization.
    This ensures all components work together correctly.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Step 1: Generate and save synthetic data
        df = generate_small_synthetic_dataset(num_samples=150)
        input_file = tmpdir_path / "dependencies.csv"
        df.to_csv(input_file, index=False)

        # Step 2: Run correlation analysis
        correlation_output = tmpdir_path / "correlation.json"
        correlation_result = run_correlation_analysis(
            input_path=str(input_file),
            output_path=str(correlation_output)
        )
        assert correlation_result is not None
        assert correlation_output.exists()

        # Step 3: Run stratified analysis
        stratified_output = tmpdir_path / "stratified.json"
        stratified_result = run_stratified_analysis(
            input_path=str(input_file),
            output_path=str(stratified_output)
        )
        assert stratified_result is not None
        assert stratified_output.exists()

        # Step 4: Run sensitivity analysis
        sensitivity_output = tmpdir_path / "sensitivity.json"
        sensitivity_result = run_sensitivity_analysis(
            input_path=str(input_file),
            output_path=str(sensitivity_output)
        )
        assert sensitivity_result is not None
        assert sensitivity_output.exists()

        # Step 5: Run power analysis
        power_output = tmpdir_path / "power.json"
        power_result = run_power_analysis(
            input_path=str(input_file),
            output_path=str(power_output)
        )
        assert power_result is not None
        assert power_output.exists()

        # Step 6: Generate visualizations
        figures_dir = tmpdir_path / "figures"
        figures_dir.mkdir()
        viz_output = tmpdir_path / "viz_summary.json"
        viz_result = create_visualization_summary(
            input_path=str(input_file),
            output_dir=str(figures_dir),
            summary_path=str(viz_output)
        )
        assert viz_result is not None
        assert viz_output.exists()

        # Final verification: all expected artifacts exist
        expected_artifacts = [
            input_file,
            correlation_output,
            stratified_output,
            sensitivity_output,
            power_output,
            viz_output
        ]

        for artifact in expected_artifacts:
            assert artifact.exists(), f"Expected artifact {artifact} was not created"

        # Verify the pipeline produced consistent results
        # (e.g., sample sizes should match across analyses)
        assert correlation_result['sample_size'] == stratified_result['overall_sample_size']
        assert correlation_result['sample_size'] == sensitivity_result['total_samples']