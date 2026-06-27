"""
Integration test for correlation analysis pipeline.

Tests the full correlation analysis workflow with mock data that simulates
the expected input files from US1 and US2 tasks.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Import module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from correlation_analysis import (
    load_clone_metrics,
    load_perplexity_scores,
    load_bug_detection_results,
    join_metrics_for_correlation,
    calculate_correlations,
    save_correlation_results,
    main
)


class TestCorrelationPipelineIntegration:
    """Integration tests for the correlation analysis pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data', 'processed')
        self.analysis_dir = os.path.join(self.temp_dir, 'data', 'analysis')
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.analysis_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_clone_metrics(self, n_samples=100):
        """Create test clone metrics data."""
        df = pd.DataFrame({
            'file_id': range(n_samples),
            'clone_density': np.random.rand(n_samples),
            'clone_count': np.random.randint(0, 10, n_samples),
            'file_path': [f'file_{i}.py' for i in range(n_samples)]
        })
        return df

    def create_test_perplexity_scores(self, n_samples=100):
        """Create test perplexity scores data."""
        df = pd.DataFrame({
            'file_id': range(n_samples),
            'perplexity': np.random.rand(n_samples) * 100 + 10,
            'model_name': 'Salesforce/codegen-350M-mono',
            'timestamp': pd.Timestamp.now().isoformat()
        })
        return df

    def create_test_bug_detection_results(self, n_samples=50):
        """Create test bug detection results data."""
        df = pd.DataFrame({
            'file_id': range(n_samples),
            'accuracy': np.random.rand(n_samples),
            'pass@1': np.random.rand(n_samples),
            'total_problems': 50,
            'passed_problems': np.random.randint(0, 50, n_samples)
        })
        return df

    def test_full_pipeline_with_mock_data(self):
        """Test the full correlation pipeline with mock data."""
        # Create test data
        clone_df = self.create_test_clone_metrics(100)
        perplexity_df = self.create_test_perplexity_scores(100)
        bug_df = self.create_test_bug_detection_results(100)

        # Save to temp location
        clone_path = os.path.join(self.data_dir, 'clone_metrics.csv')
        perplexity_path = os.path.join(self.data_dir, 'perplexity_scores.csv')
        bug_path = os.path.join(self.data_dir, 'bug_detection_results.csv')

        clone_df.to_csv(clone_path, index=False)
        perplexity_df.to_csv(perplexity_path, index=False)
        bug_df.to_csv(bug_path, index=False)

        # Run pipeline
        results = calculate_correlations(
            join_metrics_for_correlation(clone_df, perplexity_df, bug_df)
        )

        # Verify results
        assert len(results) == 3
        assert 'clone_density_vs_perplexity' in results
        assert 'clone_density_vs_accuracy' in results
        assert 'perplexity_vs_accuracy' in results

        # Verify correlation values are in valid range
        for name, metrics in results.items():
            assert -1.0 <= metrics['correlation'] <= 1.0
            assert 0.0 <= metrics['p_value'] <= 1.0
            assert metrics['n_samples'] > 0

    def test_save_and_load_correlation_results(self):
        """Test saving and loading correlation results."""
        # Create and save results
        results = {
            'clone_density_vs_perplexity': {
                'correlation': 0.35,
                'p_value': 0.001,
                'n_samples': 1000
            },
            'clone_density_vs_accuracy': {
                'correlation': -0.25,
                'p_value': 0.005,
                'n_samples': 1000
            },
            'perplexity_vs_accuracy': {
                'correlation': -0.45,
                'p_value': 0.0001,
                'n_samples': 1000
            }
        }

        output_path = os.path.join(self.analysis_dir, 'correlation_results.csv')
        save_correlation_results(results, output_path)

        # Load and verify
        assert os.path.exists(output_path)
        df = pd.read_csv(output_path)

        assert len(df) == 3
        assert 'correlation_coefficient' in df.columns
        assert 'p_value' in df.columns
        assert 'n_samples' in df.columns

        # Verify specific values
        clone_perp_row = df[df['correlation_pair'] == 'clone_density_vs_perplexity']
        assert abs(clone_perp_row['correlation_coefficient'].iloc[0] - 0.35) < 1e-6
        assert abs(clone_perp_row['p_value'].iloc[0] - 0.001) < 1e-6

    def test_pipeline_with_partial_data(self):
        """Test pipeline behavior when some data is missing."""
        # Create data with only partial overlap
        clone_df = self.create_test_clone_metrics(100)
        perplexity_df = self.create_test_perplexity_scores(80)  # Only 80 files
        bug_df = self.create_test_bug_detection_results(60)  # Only 60 files

        # Join should result in 60 records (inner join)
        merged = join_metrics_for_correlation(clone_df, perplexity_df, bug_df)
        assert len(merged) == 60

        results = calculate_correlations(merged)
        assert results['clone_density_vs_perplexity']['n_samples'] == 60

    def test_error_handling_missing_files(self):
        """Test error handling when required files are missing."""
        with pytest.raises(FileNotFoundError):
            load_clone_metrics('nonexistent/path/clone_metrics.csv')

        with pytest.raises(FileNotFoundError):
            load_perplexity_scores('nonexistent/path/perplexity_scores.csv')

        with pytest.raises(FileNotFoundError):
            load_bug_detection_results('nonexistent/path/bug_detection_results.csv')

    def test_pipeline_with_realistic_correlation_patterns(self):
        """Test pipeline with data that has known correlation patterns."""
        n = 1000
        np.random.seed(42)

        # Create correlated data: higher clone density -> higher perplexity
        base_clone = np.random.rand(n)
        clone_density = base_clone
        perplexity = 10 + 50 * base_clone + np.random.randn(n) * 2  # Positive correlation
        accuracy = 0.9 - 0.3 * base_clone + np.random.randn(n) * 0.1  # Negative correlation

        clone_df = pd.DataFrame({
            'file_id': range(n),
            'clone_density': clone_density
        })

        perplexity_df = pd.DataFrame({
            'file_id': range(n),
            'perplexity': perplexity
        })

        bug_df = pd.DataFrame({
            'file_id': range(n),
            'accuracy': accuracy
        })

        results = calculate_correlations(
            join_metrics_for_correlation(clone_df, perplexity_df, bug_df)
        )

        # Verify correlation signs match expectations
        assert results['clone_density_vs_perplexity']['correlation'] > 0.5
        assert results['clone_density_vs_accuracy']['correlation'] < -0.3
        assert results['perplexity_vs_accuracy']['correlation'] < -0.3

        # Verify statistical significance
        assert results['clone_density_vs_perplexity']['p_value'] < 0.001
        assert results['clone_density_vs_accuracy']['p_value'] < 0.001
        assert results['perplexity_vs_accuracy']['p_value'] < 0.001