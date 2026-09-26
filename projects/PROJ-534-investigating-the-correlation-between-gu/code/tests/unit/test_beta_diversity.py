"""
Unit tests for Beta Diversity Analysis (PERMANOVA).
"""

import pytest
import pandas as pd
import numpy as np
import skbio
from pathlib import Path
import tempfile
import json

# Add src to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from code.src.analysis.beta_diversity import (
    load_distance_matrix,
    run_permanova
)
from code.src.utils.config import set_global_seed, SEED


@pytest.fixture
def sample_cohort_with_otu():
    """Generate a synthetic cohort with OTU data for testing."""
    set_global_seed(SEED)
    n_participants = 20
    
    data = {
        'participant_id': [f"sub_{i:03d}" for i in range(n_participants)],
        'cognitive_score': np.random.uniform(0, 100, n_participants),
        'age': np.random.uniform(65, 85, n_participants),
        'sex': np.random.choice(['M', 'F'], n_participants),
        'otu_1': np.random.poisson(10, n_participants),
        'otu_2': np.random.poisson(15, n_participants),
        'otu_3': np.random.poisson(5, n_participants),
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_distance_matrix(sample_cohort_with_otu):
    """Create a mock skbio DistanceMatrix from sample data."""
    otu_cols = ['otu_1', 'otu_2', 'otu_3']
    otu_data = sample_cohort_with_otu[otu_cols].values
    
    # Calculate Bray-Curtis manually to ensure consistency
    dm_values = skbio.stats.distance.braycurtis(otu_data)
    ids = sample_cohort_with_otu['participant_id'].tolist()
    
    return skbio.DistanceMatrix(dm_values, ids=ids)


class TestBetaDiversity:
    def test_load_distance_matrix(self, sample_cohort_with_otu):
        """Test that distance matrix is correctly calculated from OTU table."""
        otu_table, dm = load_distance_matrix(sample_cohort_with_otu)
        
        assert isinstance(dm, skbio.DistanceMatrix)
        assert len(dm.ids) == len(sample_cohort_with_otu)
        assert dm.shape[0] == len(sample_cohort_with_otu)
        
        # Check that IDs match
        assert set(dm.ids) == set(sample_cohort_with_otu['participant_id'])

    def test_run_permanova_basic(self, sample_cohort_with_otu, mock_distance_matrix):
        """Test basic PERMANOVA execution."""
        results = run_permanova(
            mock_distance_matrix, 
            sample_cohort_with_otu, 
            variable='cognitive_score',
            permutations=99
        )
        
        assert 'f_statistic' in results
        assert 'p_value' in results
        assert 'r_squared' in results or 'pseudo_f' in results
        assert results['n_samples'] == len(sample_cohort_with_otu)
        assert results['variable'] == 'cognitive_score'

    def test_run_permanova_invalid_variable(self, mock_distance_matrix, sample_cohort_with_otu):
        """Test PERMANOVA raises error for non-existent variable."""
        with pytest.raises(ValueError, match="Variable 'non_existent' not found"):
            run_permanova(
                mock_distance_matrix,
                sample_cohort_with_otu,
                variable='non_existent'
            )

    def test_permanova_result_structure(self, sample_cohort_with_otu, mock_distance_matrix):
        """Verify the result dictionary contains all expected keys."""
        results = run_permanova(
            mock_distance_matrix,
            sample_cohort_with_otu,
            variable='cognitive_score',
            permutations=99
        )
        
        required_keys = [
            'method', 'distance_metric', 'variable', 'n_permutations',
            'n_samples', 'f_statistic', 'p_value'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"

    def test_permanova_with_subset(self, mock_distance_matrix, sample_cohort_with_otu):
        """Test PERMANOVA when IDs don't perfectly align (simulated mismatch)."""
        # Create a cohort with missing participant
        cohort_subset = sample_cohort_with_otu.iloc[:-1].copy()
        
        # The distance matrix still has all IDs, but cohort is missing one
        # The function should handle this gracefully by filtering to common IDs
        results = run_permanova(
            mock_distance_matrix,
            cohort_subset,
            variable='cognitive_score',
            permutations=99
        )
        
        # Should run with n-1 samples
        assert results['n_samples'] == len(cohort_subset)