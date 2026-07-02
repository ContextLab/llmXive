"""
Unit tests for data splitting functionality.

Tests FR-009: Stratified sampling based on resistance phenotype.
"""
import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.split import (
    load_processed_data,
    perform_stratified_split,
    save_split_indices,
    split_pipeline,
    DEFAULT_TRAIN_RATIO,
    DEFAULT_HOLDOUT_RATIO,
    RANDOM_SEED
)
from utils.exceptions import PipelineException, EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT
from data.manifest import ManifestLoader

@pytest.fixture
def sample_phenotype_data():
    """Create sample phenotype data for testing."""
    np.random.seed(42)
    n_samples = 200
    sample_ids = [f"sample_{i:03d}" for i in range(n_samples)]
    
    # Create balanced binary phenotype
    phenotypes = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])
    
    return pd.Series(phenotypes, index=sample_ids, name='resistance')

@pytest.fixture
def sample_split_data(sample_phenotype_data):
    """Create sample split data."""
    train_ratio = 0.8
    holdout_ratio = 0.2
    
    train_index, holdout_index = perform_stratified_split(
        sample_phenotype_data,
        train_ratio=train_ratio,
        holdout_ratio=holdout_ratio,
        random_state=RANDOM_SEED
    )
    
    return {
        'train_index': train_index,
        'holdout_index': holdout_index,
        'phenotype_data': sample_phenotype_data
    }

class TestPerformStratifiedSplit:
    """Tests for the perform_stratified_split function."""
    
    def test_stratified_split_balanced(self, sample_phenotype_data):
        """Test that stratified split maintains class balance."""
        train_index, holdout_index, _ = perform_stratified_split(
            sample_phenotype_data,
            train_ratio=0.8,
            holdout_ratio=0.2,
            random_state=RANDOM_SEED
        )
        
        train_phenotypes = sample_phenotype_data.loc[train_index]
        holdout_phenotypes = sample_phenotype_data.loc[holdout_index]
        
        # Check that both sets have both classes
        assert set(train_phenotypes.unique()) == {0, 1}
        assert set(holdout_phenotypes.unique()) == {0, 1}
        
        # Check that proportions are approximately maintained
        train_ratio_actual = train_phenotypes.value_counts(normalize=True)[1]
        holdout_ratio_actual = holdout_phenotypes.value_counts(normalize=True)[1]
        
        assert abs(train_ratio_actual - 0.5) < 0.1
        assert abs(holdout_ratio_actual - 0.5) < 0.1
        
    def test_stratified_split_sizes(self, sample_phenotype_data):
        """Test that split sizes match expected ratios."""
        train_index, holdout_index, _ = perform_stratified_split(
            sample_phenotype_data,
            train_ratio=0.8,
            holdout_ratio=0.2,
            random_state=RANDOM_SEED
        )
        
        total_samples = len(sample_phenotype_data)
        expected_train = int(total_samples * 0.8)
        expected_holdout = int(total_samples * 0.2)
        
        assert len(train_index) == expected_train
        assert len(holdout_index) == expected_holdout
        assert len(train_index) + len(holdout_index) == total_samples
        
    def test_stratified_split_reproducibility(self, sample_phenotype_data):
        """Test that split is reproducible with same random state."""
        train_index1, holdout_index1, _ = perform_stratified_split(
            sample_phenotype_data,
            train_ratio=0.8,
            holdout_ratio=0.2,
            random_state=RANDOM_SEED
        )
        
        train_index2, holdout_index2, _ = perform_stratified_split(
            sample_phenotype_data,
            train_ratio=0.8,
            holdout_ratio=0.2,
            random_state=RANDOM_SEED
        )
        
        assert list(train_index1) == list(train_index2)
        assert list(holdout_index1) == list(holdout_index2)
        
    def test_stratified_split_insufficient_classes(self):
        """Test that split fails with insufficient class representation."""
        # Create data with only one class
        sample_ids = [f"sample_{i:03d}" for i in range(100)]
        phenotypes = pd.Series([0] * 100, index=sample_ids, name='resistance')
        
        with pytest.raises(PipelineException) as exc_info:
            perform_stratified_split(
                phenotypes,
                train_ratio=0.8,
                holdout_ratio=0.2,
                random_state=RANDOM_SEED
            )
        
        assert exc_info.value.code == EX_POWER_INSUFFICIENT
        
    def test_stratified_split_invalid_ratios(self, sample_phenotype_data):
        """Test that split fails with invalid ratio sums."""
        with pytest.raises(PipelineException) as exc_info:
            perform_stratified_split(
                sample_phenotype_data,
                train_ratio=0.7,
                holdout_ratio=0.4,
                random_state=RANDOM_SEED
            )
        
        assert exc_info.value.code == EX_DATA_INTEGRITY

class TestSplitPipeline:
    """Tests for the complete split pipeline."""
    
    @patch('data.split.load_processed_data')
    @patch('data.split.perform_stratified_split')
    @patch('data.split.save_split_indices')
    @patch('data.split.get_path')
    @patch('data.split.load_manifest')
    @patch('data.split.get_manifest_source_type')
    def test_split_pipeline_success(
        self,
        mock_get_source_type,
        mock_load_manifest,
        mock_get_path,
        mock_save_indices,
        mock_perform_split,
        mock_load_processed
    ):
        """Test successful split pipeline execution."""
        # Setup mocks
        mock_get_source_type.return_value = "REAL"
        mock_load_manifest.return_value = {'source': 'NCBI'}
        mock_get_path.side_effect = lambda *args: '/'.join(args)
        
        # Create sample data
        sample_snps = pd.DataFrame({
            'sample_id': [f"sample_{i:03d}" for i in range(100)],
            'snp1': np.random.randn(100),
            'snp2': np.random.randn(100)
        })
        
        sample_metabolites = pd.DataFrame({
            'sample_id': [f"sample_{i:03d}" for i in range(100)],
            'met1': np.random.randn(100),
            'met2': np.random.randn(100)
        })
        
        sample_phenotypes = pd.Series(
            np.random.choice([0, 1], 100),
            index=[f"sample_{i:03d}" for i in range(100)],
            name='resistance'
        )
        
        mock_load_processed.return_value = (
            sample_snps.set_index('sample_id'),
            sample_metabolites.set_index('sample_id'),
            sample_phenotypes
        )
        
        # Setup split indices
        train_index = [f"sample_{i:03d}" for i in range(80)]
        holdout_index = [f"sample_{i:03d}" for i in range(80, 100)]
        mock_perform_split.return_value = (train_index, holdout_index, pd.Index([]))
        
        # Execute pipeline
        result = split_pipeline()
        
        # Verify results
        assert result['success'] is True
        assert result['train_samples'] == 80
        assert result['holdout_samples'] == 20
        assert 'split_config' in result
        assert 'paths' in result
        
        # Verify function calls
        mock_load_processed.assert_called_once()
        mock_perform_split.assert_called_once()
        mock_save_indices.assert_called_once()

    @patch('data.split.load_processed_data')
    def test_split_pipeline_insufficient_samples(self, mock_load_processed):
        """Test pipeline fails with insufficient samples."""
        # Create data with too few samples
        sample_ids = [f"sample_{i:03d}" for i in range(50)]
        phenotypes = pd.Series(np.random.choice([0, 1], 50), index=sample_ids, name='resistance')
        
        mock_load_processed.return_value = (
            pd.DataFrame({'sample_id': sample_ids, 'snp1': np.random.randn(50)}).set_index('sample_id'),
            pd.DataFrame({'sample_id': sample_ids, 'met1': np.random.randn(50)}).set_index('sample_id'),
            phenotypes
        )
        
        with pytest.raises(PipelineException) as exc_info:
            split_pipeline()
        
        assert exc_info.value.code == EX_POWER_INSUFFICIENT

class TestSaveSplitIndices:
    """Tests for save_split_indices function."""
    
    @patch('data.split.get_path')
    @patch('data.split.load_manifest')
    @patch('builtins.open', new_callable=MagicMock)
    def test_save_split_indices(self, mock_open, mock_load_manifest, mock_get_path):
        """Test saving split indices to files."""
        mock_get_path.side_effect = lambda *args: '/'.join(args)
        mock_load_manifest.return_value = {'source': 'NCBI'}
        
        train_index = pd.Index(['sample_001', 'sample_002', 'sample_003'])
        holdout_index = pd.Index(['sample_004', 'sample_005'])
        split_config = {
            'train_ratio': 0.6,
            'holdout_ratio': 0.4,
            'random_state': 42
        }
        
        save_split_indices(train_index, holdout_index, split_config)
        
        # Verify files were created
        assert mock_open.call_count >= 2  # At least train and holdout files
        
        # Verify manifest was updated
        mock_load_manifest.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])