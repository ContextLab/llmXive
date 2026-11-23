import pytest
import pandas as pd
import numpy as np
import skbio
from skbio.stats.distance import DistanceMatrix
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from code.src.analysis.beta_diversity import (
    load_filtered_cohort, 
    load_distance_matrix, 
    run_permanova, 
    main
)
from code.src.utils.config import get_processed_data_dir, get_results_dir

@pytest.fixture
def sample_cohort_with_otu():
    """Create a sample cohort with OTU data for testing."""
    np.random.seed(42)
    n_samples = 50
    n_otus = 100
    
    data = {
        'participant_id': [f'P{i:03d}' for i in range(n_samples)],
        'age': np.random.randint(65, 85, n_samples),
        'sex': np.random.choice(['M', 'F'], n_samples),
        'bmi': np.random.normal(25, 3, n_samples),
        'cognitive_flexibility_score': np.random.normal(50, 10, n_samples),
        'shannon_diversity': np.random.normal(3.5, 0.5, n_samples),
        'simpson_diversity': np.random.normal(0.9, 0.05, n_samples),
        'chao1': np.random.normal(150, 20, n_samples),
        'dietary_fiber': np.random.normal(25, 5, n_samples),
        'antibiotic_use': np.random.choice([True, False], n_samples),
    }
    
    # Add OTU columns
    for i in range(n_otus):
        data[f'otu_{i}'] = np.random.poisson(5, n_samples)
    
    return pd.DataFrame(data)

@pytest.fixture
def mock_distance_matrix(sample_cohort_with_otu):
    """Create a mock distance matrix for testing PERMANOVA."""
    n = len(sample_cohort_with_otu)
    ids = sample_cohort_with_otu['participant_id'].values
    
    # Create a random distance matrix
    data = np.random.rand(n, n)
    data = (data + data.T) / 2  # Make symmetric
    np.fill_diagonal(data, 0)
    
    return DistanceMatrix(data, ids=ids)

class TestBetaDiversity:
    def test_load_filtered_cohort_file_not_found(self):
        """Test that load_filtered_cohort raises FileNotFoundError when file is missing."""
        with patch('code.src.analysis.beta_diversity.get_processed_data_dir') as mock_dir:
            mock_dir.return_value = Path('/nonexistent/path')
            with pytest.raises(FileNotFoundError):
                load_filtered_cohort()

    def test_load_distance_matrix_valid_data(self, sample_cohort_with_otu):
        """Test distance matrix calculation with valid OTU data."""
        dm = load_distance_matrix(sample_cohort_with_otu, metric='braycurtis')
        assert isinstance(dm, DistanceMatrix)
        assert dm.shape == (len(sample_cohort_with_otu), len(sample_cohort_with_otu))
        assert np.allclose(dm.data.diagonal(), 0)

    def test_load_distance_matrix_no_otu_columns(self):
        """Test that load_distance_matrix raises error when no OTU columns exist."""
        df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [70, 75],
            'cognitive_flexibility_score': [50, 60]
        })
        with pytest.raises(ValueError, match="No OTU columns found"):
            load_distance_matrix(df)

    def test_run_permanova_basic(self, mock_distance_matrix, sample_cohort_with_otu):
        """Test basic PERMANOVA execution."""
        results = run_permanova(mock_distance_matrix, sample_cohort_with_otu)
        
        assert 'test_type' in results
        assert results['test_type'] == 'PERMANOVA'
        assert 'f_statistic' in results
        assert 'p_value' in results
        assert 'r_squared' in results
        assert 'grouping_variable' in results
        assert results['grouping_variable'] in ['cognitive_quartile', 'cognitive_flexibility_score']
        assert results['n_permutations'] == 999

    def test_run_permanova_handles_skewed_data(self, mock_distance_matrix):
        """Test that PERMANOVA handles skewed cognitive data by using quartiles."""
        df = pd.DataFrame({
            'participant_id': [f'P{i}' for i in range(20)],
            'cognitive_flexibility_score': np.random.exponential(10, 20)  # Highly skewed
        })
        
        results = run_permanova(mock_distance_matrix, df)
        
        # Should have created quartiles
        assert 'cognitive_quartile' in df.columns or results['grouping_variable'] == 'cognitive_quartile'
        assert 'skewness_check' in results

    def test_main_execution(self, sample_cohort_with_otu):
        """Test the main function execution with mocked file system."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            processed_dir = tmpdir / 'data' / 'processed'
            results_dir = tmpdir / 'data' / 'results'
            logs_dir = tmpdir / 'logs'
            
            processed_dir.mkdir(parents=True)
            results_dir.mkdir(parents=True)
            logs_dir.mkdir(parents=True)
            
            # Save test cohort
            cohort_path = processed_dir / 'filtered_cohort.csv'
            sample_cohort_with_otu.to_csv(cohort_path, index=False)
            
            # Mock config functions
            with patch('code.src.analysis.beta_diversity.get_processed_data_dir', return_value=processed_dir), \
                 patch('code.src.analysis.beta_diversity.get_results_dir', return_value=results_dir), \
                 patch('code.src.analysis.beta_diversity.get_logs_dir', return_value=logs_dir):
                
                    main()
                    
                    # Check that results file was created
                    results_path = results_dir / 'beta_diversity_results.json'
                    assert results_path.exists()
                    
                    import json
                    with open(results_path) as f:
                        data = json.load(f)
                    
                    assert 'f_statistic' in data
                    assert 'p_value' in data
                    assert 'r_squared' in data