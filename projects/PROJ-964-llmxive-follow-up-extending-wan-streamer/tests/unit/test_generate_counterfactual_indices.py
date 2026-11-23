import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from inference.generate_counterfactual_indices import (
    load_sampled_dataset,
    generate_counterfactual_indices,
    save_counterfactual_indices,
    SEED,
    MIN_SKIP_RATIO
)

class TestGenerateCounterfactualIndices:
    """Unit tests for counterfactual index generation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_dataset(self, temp_dir):
        """Create a sample dataset parquet file."""
        data_path = temp_dir / 'sample_dataset.parquet'
        
        # Create sample data with frame_id column
        n_frames = 1000
        df = pd.DataFrame({
            'frame_id': np.arange(n_frames),
            'timestamp': np.arange(n_frames) * 0.016,  # 60fps
            'latent_delta_magnitude': np.random.randn(n_frames),
            'turn_label': np.random.choice([0, 1], n_frames)
        })
        
        df.to_parquet(data_path, index=False)
        return data_path
    
    def test_load_sampled_dataset_exists(self, sample_dataset):
        """Test that load_sampled_dataset successfully loads existing file."""
        df = load_sampled_dataset(sample_dataset)
        
        assert len(df) == 1000
        assert 'frame_id' in df.columns
        assert df['frame_id'].dtype == np.int64
    
    def test_load_sampled_dataset_missing_file(self, temp_dir):
        """Test that load_sampled_dataset raises FileNotFoundError for missing file."""
        missing_path = temp_dir / 'nonexistent.parquet'
        
        with pytest.raises(FileNotFoundError):
            load_sampled_dataset(missing_path)
    
    def test_load_sampled_dataset_empty(self, temp_dir):
        """Test that load_sampled_dataset raises ValueError for empty file."""
        empty_path = temp_dir / 'empty.parquet'
        pd.DataFrame().to_parquet(empty_path)
        
        with pytest.raises(ValueError, match="Input dataset is empty"):
            load_sampled_dataset(empty_path)
    
    def test_load_sampled_dataset_missing_column(self, temp_dir):
        """Test that load_sampled_dataset raises ValueError for missing frame_id."""
        bad_path = temp_dir / 'bad_columns.parquet'
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })
        df.to_parquet(bad_path)
        
        with pytest.raises(ValueError, match="missing 'frame_id' column"):
            load_sampled_dataset(bad_path)
    
    def test_generate_counterfactual_indices_size(self, sample_dataset):
        """Test that generated indices meet minimum size requirement."""
        df = load_sampled_dataset(sample_dataset)
        
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        min_required = int(np.ceil(len(df) * MIN_SKIP_RATIO))
        assert len(indices) >= min_required
    
    def test_generate_counterfactual_indices_reproducibility(self, sample_dataset):
        """Test that same seed produces same results."""
        df = load_sampled_dataset(sample_dataset)
        
        indices1 = generate_counterfactual_indices(df, seed=SEED)
        indices2 = generate_counterfactual_indices(df, seed=SEED)
        
        assert np.array_equal(indices1, indices2)
    
    def test_generate_counterfactual_indices_unique(self, sample_dataset):
        """Test that all generated indices are unique."""
        df = load_sampled_dataset(sample_dataset)
        
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        assert len(indices) == len(set(indices))
    
    def test_generate_counterfactual_indices_valid_ids(self, sample_dataset):
        """Test that all generated indices exist in the dataset."""
        df = load_sampled_dataset(sample_dataset)
        all_ids = set(df['frame_id'].values)
        
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        assert all(id in all_ids for id in indices)
    
    def test_save_counterfactual_indices(self, temp_dir, sample_dataset):
        """Test that save_counterfactual_indices creates valid parquet file."""
        df = load_sampled_dataset(sample_dataset)
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        output_path = temp_dir / 'counterfactual_indices.parquet'
        save_counterfactual_indices(indices, output_path)
        
        assert output_path.exists()
        
        # Load and verify
        saved_df = pd.read_parquet(output_path)
        assert 'frame_id' in saved_df.columns
        assert len(saved_df) == len(indices)
        assert saved_df['frame_id'].dtype == np.int64
    
    def test_save_counterfactual_indices_creates_directory(self, temp_dir, sample_dataset):
        """Test that save_counterfactual_indices creates parent directories."""
        df = load_sampled_dataset(sample_dataset)
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        # Nested path that doesn't exist
        output_path = temp_dir / 'nested' / 'deep' / 'counterfactual_indices.parquet'
        
        save_counterfactual_indices(indices, output_path)
        
        assert output_path.exists()
    
    def test_generate_counterfactual_indices_custom_ratio(self, sample_dataset):
        """Test that custom min_ratio is respected."""
        df = load_sampled_dataset(sample_dataset)
        
        custom_ratio = 0.10  # 10%
        indices = generate_counterfactual_indices(df, seed=SEED, min_ratio=custom_ratio)
        
        expected_min = int(np.ceil(len(df) * custom_ratio))
        assert len(indices) >= expected_min
    
    def test_generate_counterfactual_indices_dtype(self, sample_dataset):
        """Test that generated indices have correct dtype."""
        df = load_sampled_dataset(sample_dataset)
        
        indices = generate_counterfactual_indices(df, seed=SEED)
        
        assert indices.dtype == np.int64