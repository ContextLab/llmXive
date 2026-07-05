import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

from embeddings import generate_pca, generate_tsne, generate_umap, run_embeddings, EmbeddingError
from config import Config

@pytest.fixture
def sample_data():
    """Generate sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_features = 20
    data = np.random.randn(n_samples, n_features)
    return data

@pytest.fixture
def sample_labels():
    """Generate sample cell labels."""
    return pd.Series(['type_A'] * 50 + ['type_B'] * 50)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_generate_pca(sample_data):
    """Test PCA generation."""
    embedding = generate_pca(sample_data, n_components=5)
    assert embedding.shape == (100, 5)
    assert not np.isnan(embedding).any()

def test_generate_tsne(sample_data):
    """Test t-SNE generation with reduced iterations for speed."""
    embedding = generate_tsne(
        sample_data,
        perplexity=10,
        n_iter=100,  # Reduced for testing
        n_jobs=1
    )
    assert embedding.shape == (100, 2)
    assert not np.isnan(embedding).any()

def test_generate_umap(sample_data):
    """Test UMAP generation."""
    embedding = generate_umap(
        sample_data,
        n_neighbors=5,  # Reduced for small dataset
        n_jobs=1
    )
    assert embedding.shape == (100, 2)
    assert not np.isnan(embedding).any()

def test_run_embeddings(sample_data, sample_labels, temp_output_dir):
    """Test full embedding pipeline."""
    results = run_embeddings(
        data=sample_data,
        output_dir=temp_output_dir,
        n_components_pca=5,
        tsne_perplexity=10,
        tsne_n_iter=100,
        umap_n_neighbors=5,
        random_state=42,
        cell_labels=sample_labels,
        accession="test_dataset"
    )
    
    # Check that all expected files were created
    assert 'pca' in results
    assert 'tsne' in results
    assert 'umap' in results
    
    # Check file existence
    for key, filepath in results.items():
        assert os.path.exists(filepath), f"File {filepath} does not exist"
        
        # Check file content
        df = pd.read_csv(filepath)
        assert 'cell_label' in df.columns
        assert len(df) == 100

def test_run_embeddings_without_labels(sample_data, temp_output_dir):
    """Test embedding pipeline without cell labels."""
    results = run_embeddings(
        data=sample_data,
        output_dir=temp_output_dir,
        n_components_pca=5,
        tsne_perplexity=10,
        tsne_n_iter=100,
        umap_n_neighbors=5,
        random_state=42,
        cell_labels=None,
        accession="test_no_labels"
    )
    
    # Check that all expected files were created
    assert 'pca' in results
    assert 'tsne' in results
    assert 'umap' in results
    
    # Check file existence
    for key, filepath in results.items():
        assert os.path.exists(filepath)
        df = pd.read_csv(filepath)
        assert 'cell_label' not in df.columns  # Should not have label column

def test_embedding_error_handling(sample_data, temp_output_dir):
    """Test error handling with invalid parameters."""
    # Test with very small perplexity (should fail or warn)
    with pytest.raises((ValueError, EmbeddingError)):
        generate_tsne(sample_data, perplexity=1, n_iter=10)