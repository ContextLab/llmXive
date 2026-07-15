import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
from code.analysis.correlations import run_pca_on_metrics, load_metrics_data

def test_pca_runs_on_synthetic_metrics():
    """
    Test that PCA runs successfully on synthetic but structurally valid data.
    Verifies that output files are created and contain expected columns.
    """
    # Create synthetic data matching the expected schema
    # This is NOT a fake result, but a structural test of the pipeline logic
    n_subjects = 10
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.rand(n_subjects) * 0.5,
        'global_efficiency': np.random.rand(n_subjects) * 0.8,
        'participation_coef': np.random.rand(n_subjects) * 0.4,
        'within_module_degree': np.random.rand(n_subjects) * 1.2
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Run PCA
        loadings, scores = run_pca_on_metrics(
            df, 
            output_dir=tmpdir,
            loadings_file="test_loadings.csv",
            scores_file="test_scores.csv"
        )

        # Verify Loadings
        assert loadings is not None
        assert 'component_1' in loadings.columns
        assert 'component_2' in loadings.columns
        assert len(loadings) == 4 # 4 metrics
        
        # Verify Scores
        assert scores is not None
        assert 'subject_id' in scores.columns
        assert 'pca_factor_1' in scores.columns
        assert 'pca_factor_2' in scores.columns
        assert len(scores) == n_subjects

        # Verify files exist on disk
        loadings_path = Path(tmpdir) / "test_loadings.csv"
        scores_path = Path(tmpdir) / "test_scores.csv"
        
        assert loadings_path.exists()
        assert scores_path.exists()

def test_pca_output_columns_match_spec():
    """
    Verify that the output columns match the exact specification for T023a.
    - pca_loadings.csv: columns [component_1, component_2]
    - factor_scores.csv: columns [subject_id, pca_factor_1]
    """
    n_subjects = 5
    data = {
        'subject_id': [f'sub-{i:03d}' for i in range(n_subjects)],
        'modularity': np.random.rand(n_subjects),
        'global_efficiency': np.random.rand(n_subjects),
        'participation_coef': np.random.rand(n_subjects),
        'within_module_degree': np.random.rand(n_subjects)
    }
    df = pd.DataFrame(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        loadings, scores = run_pca_on_metrics(
            df,
            output_dir=tmpdir,
            loadings_file="loadings.csv",
            scores_file="scores.csv"
        )

        # Check loadings columns
        assert list(loadings.columns) == ['component_1', 'component_2']
        
        # Check scores columns (must start with subject_id, then pca_factor_1)
        assert list(scores.columns)[:2] == ['subject_id', 'pca_factor_1']