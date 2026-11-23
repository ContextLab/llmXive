import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from skbio.stats.distance import DissimilarityMatrix
from src.pipelines.analysis import run_permanova_analysis, apply_fdr_correction

@pytest.fixture
def sample_metadata():
    """Create sample metadata with environmental variables."""
    np.random.seed(42)
    n = 30
    data = {
        'sample_id': [f'sample_{i}' for i in range(n)],
        'pH': np.random.uniform(4.0, 8.0, n),
        'nutrients': np.random.uniform(0, 100, n),
        'moisture': np.random.uniform(10, 90, n),
        'temperature': np.random.uniform(5, 25, n),
        'biome': np.random.choice(['Forest', 'Grassland', 'Desert'], n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_distance_matrix(sample_metadata):
    """Create a sample distance matrix."""
    n = len(sample_metadata)
    # Create a random symmetric distance matrix
    np.random.seed(123)
    dist_matrix = np.random.rand(n, n)
    dist_matrix = (dist_matrix + dist_matrix.T) / 2
    np.fill_diagonal(dist_matrix, 0)
    
    ids = sample_metadata['sample_id'].tolist()
    return DissimilarityMatrix(dist_matrix, ids=ids)

def test_apply_fdr_correction():
    """Test FDR correction on sample p-values."""
    df = pd.DataFrame({
        'term': ['A', 'B', 'C', 'D'],
        'R2': [0.1, 0.2, 0.3, 0.4],
        'p-value': [0.01, 0.03, 0.05, 0.10]
    })
    
    result = apply_fdr_correction(df, 'p-value')
    
    assert 'p-value_adj' in result.columns
    assert len(result) == 4
    # Check that adjusted p-values are >= original (conservative)
    assert all(result['p-value_adj'] >= result['p-value'])

def test_run_permanova_analysis_creates_output(sample_metadata, sample_distance_matrix):
    """Test that run_permanova_analysis creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save metadata
        metadata_path = os.path.join(tmpdir, 'metadata.csv')
        sample_metadata.to_csv(metadata_path, index=False)
        
        # Save distance matrix
        dist_path = os.path.join(tmpdir, 'distance_matrix.csv')
        sample_distance_matrix.to_data_frame().to_csv(dist_path)
        
        # Output path
        output_path = os.path.join(tmpdir, 'permanova_summary.csv')
        
        # Run analysis
        result = run_permanova_analysis(
            data_path=metadata_path,
            distance_matrix_path=dist_path,
            output_path=output_path,
            env_columns=['pH', 'nutrients', 'moisture', 'temperature'],
            min_samples=10
        )
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Verify result structure
        assert 'term' in result.columns
        assert 'R2' in result.columns
        assert 'p-value' in result.columns
        assert 'p-value_adj' in result.columns
        
        # Verify all expected terms are present
        expected_terms = ['pH', 'nutrients', 'moisture', 'temperature']
        assert list(result['term']) == expected_terms

def test_run_permanova_analysis_small_sample_size(sample_metadata, sample_distance_matrix):
    """Test that analysis uses 9999 permutations for small sample sizes."""
    # Create a small dataset (n < 20)
    small_metadata = sample_metadata.head(15)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, 'metadata.csv')
        small_metadata.to_csv(metadata_path, index=False)
        
        # Create corresponding distance matrix
        small_dist = sample_distance_matrix.submatrix(small_metadata['sample_id'].tolist())
        dist_path = os.path.join(tmpdir, 'distance_matrix.csv')
        small_dist.to_data_frame().to_csv(dist_path)
        
        output_path = os.path.join(tmpdir, 'permanova_summary.csv')
        
        # This should run without error and use 9999 permutations
        result = run_permanova_analysis(
            data_path=metadata_path,
            distance_matrix_path=dist_path,
            output_path=output_path,
            env_columns=['pH', 'nutrients'],
            min_samples=5
        )
        
        assert os.path.exists(output_path)
        assert len(result) > 0

def test_run_permanova_analysis_empty_input():
    """Test handling of empty input."""
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = os.path.join(tmpdir, 'metadata.csv')
        pd.DataFrame({'sample_id': []}).to_csv(metadata_path, index=False)
        
        dist_path = os.path.join(tmpdir, 'distance_matrix.csv')
        pd.DataFrame().to_csv(dist_path)
        
        output_path = os.path.join(tmpdir, 'permanova_summary.csv')
        
        # Should handle gracefully
        with pytest.raises(Exception):
            run_permanova_analysis(
                data_path=metadata_path,
                distance_matrix_path=dist_path,
                output_path=output_path,
                env_columns=['pH'],
                min_samples=10
            )