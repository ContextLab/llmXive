"""Unit tests for correlation analysis module."""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis.correlations import (
    load_metrics_data,
    partial_correlation,
    apply_fdr_correction,
    run_metric_correlations,
    run_pca,
    compute_and_save_pca,
    merge_metrics_and_pca,
    create_full_metrics_output,
    main
)


class TestLoadMetricsData:
    def test_load_synthetic_data(self):
        """Test that synthetic data generation works correctly."""
        df = load_metrics_data(use_synthetic=True, n_subjects=30)

        assert len(df) == 30
        required_cols = [
            'subject_id', 'modularity', 'global_efficiency',
            'participation_coef', 'within_module_degree', 'fd'
        ]
        for col in required_cols:
            assert col in df.columns

    def test_synthetic_data_realistic_ranges(self):
        """Test that synthetic data falls within realistic ranges."""
        df = load_metrics_data(use_synthetic=True, n_subjects=100)

        # Modularity typically 0.3-0.8
        assert df['modularity'].between(0.2, 1.0).all()

        # Global efficiency typically 0.1-0.5
        assert df['global_efficiency'].between(0.0, 1.0).all()

        # Participation coefficient typically 0-1
        assert df['participation_coef'].between(0.0, 1.0).all()

        # Within-module degree typically 0-2
        assert df['within_module_degree'].between(0.0, 3.0).all()

        # FD is always positive
        assert (df['fd'] >= 0).all()


class TestPartialCorrelation:
    def test_partial_correlation_basic(self):
        """Test basic partial correlation calculation."""
        np.random.seed(42)
        n = 100

        # Create variables with known relationships
        x = np.random.normal(0, 1, n)
        z = np.random.normal(0, 1, n)
        # y depends on both x and z
        y = 0.5 * x + 0.5 * z + np.random.normal(0, 0.5, n)

        # Without controlling for z, correlation should be high
        corr_no_control = np.corrcoef(x, y)[0, 1]

        # With controlling for z, correlation should be lower
        r, p = partial_correlation(x, y, z)

        assert abs(r) < abs(corr_no_control)
        assert 0 <= p <= 1

    def test_partial_correlation_with_matrix_z(self):
        """Test partial correlation with multiple control variables."""
        np.random.seed(42)
        n = 100

        x = np.random.normal(0, 1, n)
        z1 = np.random.normal(0, 1, n)
        z2 = np.random.normal(0, 1, n)
        y = 0.5 * x + 0.3 * z1 + 0.2 * z2 + np.random.normal(0, 0.5, n)

        z = np.column_stack([z1, z2])
        r, p = partial_correlation(x, y, z)

        assert -1 <= r <= 1
        assert 0 <= p <= 1


class TestFDRCorrection:
    def test_fdr_correction_basic(self):
        """Test basic FDR correction."""
        p_values = [0.01, 0.03, 0.04, 0.06, 0.10, 0.20]

        significant, p_adj = apply_fdr_correction(p_values, alpha=0.05)

        assert len(significant) == len(p_values)
        assert len(p_adj) == len(p_values)

        # Some should be significant
        assert any(significant)

    def test_fdr_correction_empty(self):
        """Test FDR correction with empty list."""
        significant, p_adj = apply_fdr_correction([])

        assert len(significant) == 0
        assert len(p_adj) == 0

    def test_fdr_correction_all_significant(self):
        """Test FDR correction where all p-values are significant."""
        p_values = [0.001, 0.002, 0.003, 0.004]

        significant, p_adj = apply_fdr_correction(p_values, alpha=0.05)

        assert all(significant)


class TestMetricCorrelations:
    def test_run_correlations_synthetic(self):
        """Test running correlations on synthetic data."""
        df = load_metrics_data(use_synthetic=True, n_subjects=50)

        metric_cols = ['modularity', 'global_efficiency']
        results = run_metric_correlations(df, metric_cols, target_col='motor_score')

        assert len(results) == len(metric_cols)
        assert 'r' in results.columns
        assert 'p' in results.columns
        assert 'q' in results.columns
        assert 'significant' in results.columns

    def test_partial_correlation_with_fd(self):
        """Test that partial correlation with FD covariate works."""
        df = load_metrics_data(use_synthetic=True, n_subjects=50)

        results = run_metric_correlations(
            df,
            ['modularity'],
            target_col='motor_score',
            covariate_col='fd',
            use_partial=True
        )

        assert len(results) == 1
        assert 'r' in results.columns


class TestPCA:
    def test_run_pca_basic(self):
        """Test basic PCA execution."""
        df = load_metrics_data(use_synthetic=True, n_subjects=50)

        metric_cols = ['modularity', 'global_efficiency', 'participation_coef']

        loadings, scores = run_pca(df, metric_cols, n_components=2)

        # Check loadings shape
        assert loadings.shape == (3, 2)
        assert all(f'component_{i}' in loadings.columns for i in [1, 2])

        # Check scores shape
        assert scores.shape[0] == 50
        assert 'subject_id' in scores.columns
        assert 'pca_factor_1' in scores.columns
        assert 'pca_factor_2' in scores.columns

    def test_compute_and_save_pca(self):
        """Test PCA computation and file saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = load_metrics_data(use_synthetic=True, n_subjects=50)

            metric_cols = ['modularity', 'global_efficiency']
            loadings_path = os.path.join(tmpdir, 'loadings.csv')
            scores_path = os.path.join(tmpdir, 'scores.csv')

            loadings, scores = compute_and_save_pca(
                df, metric_cols, loadings_path, scores_path, n_components=2
            )

            # Check files exist
            assert os.path.exists(loadings_path)
            assert os.path.exists(scores_path)

            # Check content
            loaded_loadings = pd.read_csv(loadings_path)
            loaded_scores = pd.read_csv(scores_path)

            assert len(loaded_loadings) == 2
            assert len(loaded_scores) == 50

    def test_merge_metrics_and_pca(self):
        """Test merging metrics with PCA scores."""
        df = load_metrics_data(use_synthetic=True, n_subjects=30)

        metric_cols = ['modularity', 'global_efficiency']
        _, scores = run_pca(df, metric_cols, n_components=2)

        merged = merge_metrics_and_pca(df, scores)

        assert len(merged) == 30
        assert 'modularity' in merged.columns
        assert 'pca_factor_1' in merged.columns

    def test_create_full_metrics_output(self):
        """Test creating full metrics output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = load_metrics_data(use_synthetic=True, n_subjects=30)

            metric_cols = ['modularity', 'global_efficiency']
            _, scores = run_pca(df, metric_cols, n_components=2)

            output_path = os.path.join(tmpdir, 'full_metrics.csv')
            merged = create_full_metrics_output(df, scores, output_path)

            assert os.path.exists(output_path)

            loaded = pd.read_csv(output_path)
            assert len(loaded) == 30
            assert 'modularity' in loaded.columns
            assert 'pca_factor_1' in loaded.columns


class TestMainFunction:
    def test_main_completes(self):
        """Test that main function completes and produces files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                input_path=None,
                output_dir=tmpdir,
                use_synthetic=True,
                n_subjects=30
            )

            # Check return dict
            assert 'loadings' in result
            assert 'factor_scores' in result
            assert 'full_metrics' in result
            assert 'correlations' in result

            # Check files exist
            for key, path in result.items():
                assert os.path.exists(path), f"File not created: {path}"

    def test_main_output_format(self):
        """Test that main function outputs have correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                output_dir=tmpdir,
                use_synthetic=True,
                n_subjects=30
            )

            # Check loadings columns
            loadings = pd.read_csv(result['loadings'])
            assert 'component_1' in loadings.columns
            assert 'component_2' in loadings.columns

            # Check factor scores columns
            scores = pd.read_csv(result['factor_scores'])
            assert 'subject_id' in scores.columns
            assert 'pca_factor_1' in scores.columns

            # Check full metrics columns
            full = pd.read_csv(result['full_metrics'])
            assert 'subject_id' in full.columns
            assert 'modularity' in full.columns
            assert 'pca_factor_1' in full.columns
