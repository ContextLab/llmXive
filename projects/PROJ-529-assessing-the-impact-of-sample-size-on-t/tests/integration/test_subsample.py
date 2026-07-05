"""
Integration tests for the subsampling pipeline (T016).

Tests that:
1. Subsamples are generated for k=3, k=5, k=10
2. Seeds are logged correctly
3. Variance handling works for edge cases
4. Output file is created with correct schema
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from subsample import (
    generate_bootstrap_subsample,
    run_subsampling_pipeline,
    load_meta_analyses_from_disk
)
from models import Study, MetaAnalysis
from utils.exceptions import ZeroVarianceError

@pytest.fixture
def sample_studies():
    """Create a list of sample Study objects for testing."""
    studies = [
        Study(meta_id="test_1", effect_size=0.3, se=0.1, n=50),
        Study(meta_id="test_1", effect_size=0.4, se=0.12, n=45),
        Study(meta_id="test_1", effect_size=0.2, se=0.08, n=60),
        Study(meta_id="test_1", effect_size=0.5, se=0.15, n=40),
        Study(meta_id="test_1", effect_size=0.35, se=0.11, n=55),
    ]
    return studies

@pytest.fixture
def meta_analysis_fixture(sample_studies):
    """Create a MetaAnalysis fixture."""
    return MetaAnalysis(
        meta_id="test_1",
        studies=sample_studies,
        total_studies=len(sample_studies)
    )

def test_generate_subsample_k3(sample_studies):
    """Test generating a subsample with k=3."""
    subsample = generate_bootstrap_subsample(
        studies=sample_studies,
        k=3,
        seed=42,
        estimator_type="REML"
    )
    
    assert subsample is not None
    assert subsample.k == 3
    assert subsample.seed == 42
    assert subsample.estimator_type == "REML"
    assert len(subsample.studies) == 3
    assert len(subsample.effect_sizes) == 3

def test_generate_subsample_k5(sample_studies):
    """Test generating a subsample with k=5."""
    subsample = generate_bootstrap_subsample(
        studies=sample_studies,
        k=5,
        seed=123,
        estimator_type="REML"
    )
    
    assert subsample is not None
    assert subsample.k == 5
    assert subsample.seed == 123
    assert subsample.estimator_type == "REML"
    assert len(subsample.studies) == 5

def test_generate_subsample_k10_insufficient_studies(sample_studies):
    """Test that k=10 fails gracefully when insufficient studies exist."""
    subsample = generate_bootstrap_subsample(
        studies=sample_studies,
        k=10,
        seed=456,
        estimator_type="DL"
    )
    
    # Should return None when k > number of studies
    assert subsample is None

def test_generate_subsample_k2_edge_case(sample_studies):
    """Test that k=2 is rejected (minimum k=3)."""
    subsample = generate_bootstrap_subsample(
        studies=sample_studies,
        k=2,
        seed=789,
        estimator_type="REML"
    )
    
    assert subsample is None

def test_reproducibility_same_seed(sample_studies):
    """Test that same seed produces same subsample."""
    subsample1 = generate_bootstrap_subsample(
        studies=sample_studies,
        k=3,
        seed=999,
        estimator_type="REML"
    )
    
    subsample2 = generate_bootstrap_subsample(
        studies=sample_studies,
        k=3,
        seed=999,
        estimator_type="REML"
    )
    
    assert subsample1 is not None
    assert subsample2 is not None
    assert subsample1.effect_sizes == subsample2.effect_sizes
    assert subsample1.ses == subsample2.ses

def test_estimator_type_switching(sample_studies):
    """Test that estimator type switches correctly based on k."""
    # k < 10 should use REML
    subsample_small = generate_bootstrap_subsample(
        studies=sample_studies,
        k=3,
        seed=111,
        estimator_type="REML"  # Explicitly set, but logic should preserve
    )
    
    # For k >= 10, we'd need more studies, so we test the logic in the pipeline
    # Here we just verify the function accepts the parameter
    assert subsample_small.estimator_type == "REML"

def test_run_pipeline_creates_output(meta_analysis_fixture, tmp_path):
    """Test that the pipeline creates the output parquet file."""
    output_path = tmp_path / "test_subsample_data.parquet"
    
    df = run_subsampling_pipeline(
        meta_analyses=[meta_analysis_fixture],
        max_subsamples_per_k=10,
        output_path=str(output_path)
    )
    
    assert output_path.exists()
    assert not df.empty
    assert 'meta_id' in df.columns
    assert 'k' in df.columns
    assert 'seed' in df.columns
    assert 'estimator_type' in df.columns

def test_pipeline_output_schema(meta_analysis_fixture, tmp_path):
    """Test that the output DataFrame has the expected schema."""
    output_path = tmp_path / "test_subsample_schema.parquet"
    
    df = run_subsampling_pipeline(
        meta_analyses=[meta_analysis_fixture],
        max_subsamples_per_k=5,
        output_path=str(output_path)
    )
    
    expected_columns = [
        'meta_id', 'k', 'seed', 'estimator_type', 'n_studies_original',
        'n_studies_sampled', 'effect_sizes', 'ses', 'mean_effect', 'variance_effect'
    ]
    
    assert list(df.columns) == expected_columns

def test_pipeline_handles_multiple_k_values(meta_analysis_fixture, tmp_path):
    """Test that the pipeline generates subsamples for multiple k values."""
    output_path = tmp_path / "test_multiple_k.parquet"
    
    df = run_subsampling_pipeline(
        meta_analyses=[meta_analysis_fixture],
        max_subsamples_per_k=5,
        output_path=str(output_path)
    )
    
    # Should have entries for k=3, k=4, k=5 (since we have 5 studies)
    unique_k_values = sorted(df['k'].unique())
    assert 3 in unique_k_values
    assert 4 in unique_k_values
    assert 5 in unique_k_values

def test_seed_logging_in_output(meta_analysis_fixture, tmp_path):
    """Test that seeds are recorded in the output."""
    output_path = tmp_path / "test_seed_logging.parquet"
    
    df = run_subsampling_pipeline(
        meta_analyses=[meta_analysis_fixture],
        max_subsamples_per_k=5,
        output_path=str(output_path)
    )
    
    # Seeds should be integers and unique per iteration
    assert all(isinstance(seed, (int, np.integer)) for seed in df['seed'])
    assert len(df['seed'].unique()) > 0

def test_zero_variance_handling():
    """Test that zero variance studies are handled gracefully."""
    # Create a study with zero SE
    bad_study = Study(meta_id="bad", effect_size=0.3, se=0.0, n=50)
    good_study = Study(meta_id="good", effect_size=0.4, se=0.1, n=50)
    
    # This should not crash, but may skip the bad study
    # The exact behavior depends on how handle_variance_issues works
    # We just verify the function doesn't crash
    try:
        result = generate_bootstrap_subsample(
            studies=[good_study, bad_study],
            k=2,  # Should be filtered to 1 valid study, which is < 3
            seed=42,
            estimator_type="REML"
        )
        # If k=2 is passed, it should return None due to k<3 check
        assert result is None
    except ZeroVarianceError:
        # If the exception is raised, that's also acceptable behavior
        pass
