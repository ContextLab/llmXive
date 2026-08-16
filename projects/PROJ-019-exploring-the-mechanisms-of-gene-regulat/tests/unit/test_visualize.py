import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Mock the config to avoid path issues in tests
import code.config
from unittest.mock import patch

@pytest.fixture
def sample_enrichment_df():
    """Create a mock enrichment dataframe matching expected schema."""
    data = {
        'cell_type': ['GM', 'K562', 'HepG2', 'H1-hESC', 'IMR90'] * 3,
        'motif_id': ['MA0001.2', 'MA0001.2', 'MA0001.2', 'MA0001.2', 'MA0001.2',
                     'MA0002.2', 'MA0002.2', 'MA0002.2', 'MA0002.2', 'MA0002.2',
                     'MA0003.2', 'MA0003.2', 'MA0003.2', 'MA0003.2', 'MA0003.2'],
        'q_value_adj': [0.001, 0.002, 0.003, 0.004, 0.005,
                        0.1, 0.2, 0.3, 0.4, 0.5,
                        0.0001, 0.0002, 0.0003, 0.0004, 0.0005]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(sample_enrichment_df):
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "enrichment_matrix.csv"
        sample_enrichment_df.to_csv(csv_path, index=False)
        yield csv_path

def test_load_enrichment_matrix(temp_csv_path):
    from code.visualize import load_enrichment_matrix
    df = load_enrichment_matrix(temp_csv_path)
    assert df.shape == (15, 3)
    assert 'cell_type' in df.columns
    assert 'q_value_adj' in df.columns

def test_load_enrichment_matrix_missing_file():
    from code.visualize import load_enrichment_matrix
    with pytest.raises(FileNotFoundError):
        load_enrichment_matrix(Path("/nonexistent/path.csv"))

def test_calculate_euclidean_distance_matrix(sample_enrichment_df):
    from code.visualize import calculate_euclidean_distance_matrix
    dist_df = calculate_euclidean_distance_matrix(sample_enrichment_df)
    # Should be 5x5 matrix (5 cell types)
    assert dist_df.shape == (5, 5)
    # Diagonal should be 0 (distance to self)
    assert np.allclose(np.diag(dist_df.values), 0.0)

def test_cluster_matrix(sample_enrichment_df):
    from code.visualize import cluster_matrix
    clustered = cluster_matrix(sample_enrichment_df)
    # Should return a pivoted dataframe
    assert 'cell_type' in clustered.index
    assert 'motif_id' in clustered.columns

def test_generate_heatmap_creates_file(temp_csv_path, tmp_path):
    from code.visualize import load_enrichment_matrix, generate_heatmap
    import matplotlib
    matplotlib.use('Agg') # Ensure non-interactive backend
    
    df = load_enrichment_matrix(temp_csv_path)
    output_file = tmp_path / "test_heatmap.png"
    
    result_path = generate_heatmap(df, output_file)
    
    assert result_path.exists()
    assert result_path.suffix == ".png"
    # Check file size is reasonable (not empty)
    assert result_path.stat().st_size > 1000