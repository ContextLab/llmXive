"""
Unit tests for saving fPCA results (task T024).
"""
import pytest
import json
import pickle
import tempfile
from pathlib import Path
import numpy as np

# Add project root to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.run_save_fpca_results import save_fpca_results

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_fpca_results():
    """Create sample fPCA results for testing."""
    return {
        'eigenvalues': [10.5, 5.2, 2.1, 0.8, 0.3],
        'eigenfunctions': [
            np.random.rand(10, 5),
            np.random.rand(10, 5),
            np.random.rand(10, 5)
        ]
    }

@pytest.fixture
def sample_variance_metrics():
    """Create sample variance metrics for testing."""
    return {
        'total_variance': 18.9,
        'cumulative_variance': [55.55, 82.54, 93.65, 97.88, 99.47],
        'variance_explained_by_top_components': [55.55, 27.01, 11.11],
        'n_components_retained': 3,
        'cumulative_variance_threshold': 80.0
    }

def test_save_fpca_results_creates_files(temp_output_dir, sample_fpca_results, sample_variance_metrics):
    """Test that save_fpca_results creates all required files."""
    saved_files = save_fpca_results(temp_output_dir, sample_fpca_results, sample_variance_metrics)
    
    # Check that all expected files were created
    assert 'eigenvalues' in saved_files
    assert 'eigenfunctions' in saved_files
    assert 'variance_metrics' in saved_files
    
    # Check file paths exist
    assert Path(saved_files['eigenvalues']).exists()
    assert Path(saved_files['eigenfunctions']).exists()
    assert Path(saved_files['variance_metrics']).exists()

def test_eigenvalues_content(temp_output_dir, sample_fpca_results, sample_variance_metrics):
    """Test that eigenvalues are saved correctly."""
    saved_files = save_fpca_results(temp_output_dir, sample_fpca_results, sample_variance_metrics)
    
    with open(saved_files['eigenvalues'], 'r') as f:
        loaded_eigenvalues = json.load(f)
    
    assert loaded_eigenvalues == sample_fpca_results['eigenvalues']

def test_eigenfunctions_content(temp_output_dir, sample_fpca_results, sample_variance_metrics):
    """Test that eigenfunctions are saved correctly."""
    saved_files = save_fpca_results(temp_output_dir, sample_fpca_results, sample_variance_metrics)
    
    with open(saved_files['eigenfunctions'], 'rb') as f:
        loaded_eigenfunctions = pickle.load(f)
    
    assert len(loaded_eigenfunctions) == len(sample_fpca_results['eigenfunctions'])
    for i, loaded_func in enumerate(loaded_eigenfunctions):
        np.testing.assert_array_almost_equal(loaded_func, sample_fpca_results['eigenfunctions'][i])

def test_variance_metrics_content(temp_output_dir, sample_fpca_results, sample_variance_metrics):
    """Test that variance metrics are saved correctly."""
    saved_files = save_fpca_results(temp_output_dir, sample_fpca_results, sample_variance_metrics)
    
    with open(saved_files['variance_metrics'], 'r') as f:
        loaded_metrics = json.load(f)
    
    assert loaded_metrics == sample_variance_metrics

def test_save_fpca_results_creates_directory(temp_output_dir):
    """Test that save_fpca_results creates the output directory if it doesn't exist."""
    new_dir = temp_output_dir / "subdir" / "nested"
    
    # Directory shouldn't exist yet
    assert not new_dir.exists()
    
    saved_files = save_fpca_results(new_dir, sample_fpca_results, sample_variance_metrics)
    
    # Directory should now exist
    assert new_dir.exists()
    assert Path(saved_files['eigenvalues']).exists()