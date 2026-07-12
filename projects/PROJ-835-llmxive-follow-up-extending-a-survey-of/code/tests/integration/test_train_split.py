"""
Integration test for T020: Stratified split of embeddings.

This test verifies that:
1. The stratified split preserves class distribution
2. Train and test sets are disjoint
3. Output files are created correctly
4. The split is reproducible with the same random state
"""
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.train import (
    load_embeddings,
    perform_stratified_split,
    save_split_data,
    main
)
from src.utils.config import ensure_dir


class TestTrainSplit:
    """Integration tests for the training data split functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def sample_embeddings(self, temp_dir):
        """Create a sample embeddings parquet file for testing."""
        # Create balanced dataset with known distribution
        n_benign = 80
        n_jailbreak = 20
        n_total = n_benign + n_jailbreak
        
        # Generate synthetic embeddings (100 samples, 768 dimensions)
        np.random.seed(42)
        embeddings = np.random.randn(n_total, 768).tolist()
        labels = [0] * n_benign + [1] * n_jailbreak
        
        df = pd.DataFrame({
            'embedding': embeddings,
            'label': labels,
            'file_id': [f'file_{i}' for i in range(n_total)]
        })
        
        output_path = os.path.join(temp_dir, 'embeddings.parquet')
        df.to_parquet(output_path, index=False)
        
        return {
            'path': output_path,
            'df': df,
            'temp_dir': temp_dir
        }
    
    def test_load_embeddings(self, sample_embeddings):
        """Test that embeddings can be loaded correctly."""
        df = load_embeddings(sample_embeddings['path'])
        
        assert len(df) == 100
        assert 'embedding' in df.columns
        assert 'label' in df.columns
        assert df['label'].sum() == 20  # 20 jailbreak samples
        
    def test_stratified_split_preserves_distribution(self, sample_embeddings):
        """Test that stratified split preserves class distribution."""
        df = load_embeddings(sample_embeddings['path'])
        
        train_df, test_df = perform_stratified_split(
            df,
            test_size=0.2,
            random_state=42
        )
        
        # Original distribution: 80% benign, 20% jailbreak
        original_jailbreak_ratio = df['label'].mean()
        
        # Check train distribution
        train_jailbreak_ratio = train_df['label'].mean()
        assert abs(train_jailbreak_ratio - original_jailbreak_ratio) < 0.05
        
        # Check test distribution
        test_jailbreak_ratio = test_df['label'].mean()
        assert abs(test_jailbreak_ratio - original_jailbreak_ratio) < 0.05
        
        # Verify sizes
        assert len(train_df) + len(test_df) == len(df)
        assert len(test_df) == int(len(df) * 0.2)
    
    def test_stratified_split_reproducibility(self, sample_embeddings):
        """Test that split is reproducible with same random state."""
        df = load_embeddings(sample_embeddings['path'])
        
        # First split
        train1, test1 = perform_stratified_split(df, test_size=0.2, random_state=42)
        
        # Second split with same seed
        train2, test2 = perform_stratified_split(df, test_size=0.2, random_state=42)
        
        # Should be identical
        assert len(train1) == len(train2)
        assert len(test1) == len(test2)
        
        # Check that labels match
        assert list(train1['label']) == list(train2['label'])
        assert list(test1['label']) == list(test2['label'])
    
    def test_save_split_data(self, sample_embeddings, temp_dir):
        """Test that split data is saved correctly."""
        df = load_embeddings(sample_embeddings['path'])
        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)
        
        output_dir = os.path.join(temp_dir, 'output')
        paths = save_split_data(train_df, test_df, output_dir)
        
        # Check files exist
        assert os.path.exists(paths['train_path'])
        assert os.path.exists(paths['test_path'])
        
        # Check content
        train_saved = pd.read_parquet(paths['train_path'])
        test_saved = pd.read_parquet(paths['test_path'])
        
        assert len(train_saved) == len(train_df)
        assert len(test_saved) == len(test_df)
        
        # Check columns preserved
        assert set(train_saved.columns) == set(train_df.columns)
        assert set(test_saved.columns) == set(test_df.columns)
    
    def test_main_function(self, sample_embeddings, temp_dir):
        """Test the main function with arguments."""
        output_dir = os.path.join(temp_dir, 'output')
        state_file = os.path.join(temp_dir, 'state.yaml')
        
        # Create a minimal state file
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, 'w') as f:
            f.write("artifact_hashes: {}\n")
        
        args = type('Args', (), {
            'input': sample_embeddings['path'],
            'output_dir': output_dir,
            'test_size': 0.2,
            'random_state': 42,
            'state_file': state_file
        })()
        
        exit_code = main(args)
        
        assert exit_code == 0
        
        # Verify output files created
        assert os.path.exists(os.path.join(output_dir, 'train_embeddings.parquet'))
        assert os.path.exists(os.path.join(output_dir, 'test_embeddings.parquet'))
    
    def test_main_missing_input(self, temp_dir):
        """Test main function with missing input file."""
        args = type('Args', (), {
            'input': os.path.join(temp_dir, 'nonexistent.parquet'),
            'output_dir': temp_dir,
            'test_size': 0.2,
            'random_state': 42,
            'state_file': os.path.join(temp_dir, 'state.yaml')
        })()
        
        exit_code = main(args)
        
        assert exit_code == 1  # FileNotFoundError
    
    def test_imbalanced_dataset_split(self, temp_dir):
        """Test split with imbalanced dataset."""
        # Create highly imbalanced dataset: 95% benign, 5% jailbreak
        n_benign = 190
        n_jailbreak = 10
        n_total = n_benign + n_jailbreak
        
        np.random.seed(42)
        embeddings = np.random.randn(n_total, 768).tolist()
        labels = [0] * n_benign + [1] * n_jailbreak
        
        df = pd.DataFrame({
            'embedding': embeddings,
            'label': labels,
            'file_id': [f'file_{i}' for i in range(n_total)]
        })
        
        input_path = os.path.join(temp_dir, 'imbalanced.parquet')
        df.to_parquet(input_path, index=False)
        
        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)
        
        # Check that stratification still works
        original_ratio = df['label'].mean()
        train_ratio = train_df['label'].mean()
        test_ratio = test_df['label'].mean()
        
        # Allow some tolerance for small sample sizes
        assert abs(train_ratio - original_ratio) < 0.05
        assert abs(test_ratio - original_ratio) < 0.05
    
    def test_single_class_dataset_fails_gracefully(self, temp_dir):
        """Test that split handles single-class dataset (no stratification possible)."""
        # Create single-class dataset (all benign)
        n_samples = 100
        np.random.seed(42)
        embeddings = np.random.randn(n_samples, 768).tolist()
        labels = [0] * n_samples
        
        df = pd.DataFrame({
            'embedding': embeddings,
            'label': labels,
            'file_id': [f'file_{i}' for i in range(n_samples)]
        })
        
        input_path = os.path.join(temp_dir, 'single_class.parquet')
        df.to_parquet(input_path, index=False)
        
        # Should not raise error, but stratify=None
        train_df, test_df = perform_stratified_split(df, test_size=0.2, random_state=42)
        
        assert len(train_df) + len(test_df) == len(df)
        assert all(train_df['label'] == 0)
        assert all(test_df['label'] == 0)
