import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.merge_metadata import (
    load_burden_data,
    load_haplogroup_data,
    load_metadata_panel,
    merge_datasets,
    ensure_dirs
)

class TestMergeMetadata:
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directory structure mimicking project layout."""
        temp_base = tempfile.mkdtemp()
        paths = {
            'raw_data': Path(temp_base) / 'raw',
            'processed_data': Path(temp_base) / 'processed',
            'logs': Path(temp_base) / 'logs'
        }
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)
        return paths, temp_base
    
    def test_load_burden_data(self, temp_dirs):
        """Test loading burden data."""
        paths, _ = temp_dirs
        burden_path = paths['processed_data'] / 'burden_per_sample.csv'
        
        # Create mock burden data
        mock_data = pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'burden_total': [0.05, 0.08],
            'burden_low': [0.02, 0.03],
            'burden_medium': [0.02, 0.03],
            'burden_high': [0.01, 0.02]
        })
        mock_data.to_csv(burden_path, index=False)
        
        df = load_burden_data(paths)
        assert len(df) == 2
        assert 'sample_id' in df.columns
        assert 'burden_total' in df.columns

    def test_load_haplogroup_data(self, temp_dirs):
        """Test loading haplogroup data."""
        paths, _ = temp_dirs
        hg_path = paths['processed_data'] / 'haplogroups.csv'
        
        mock_data = pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'haplogroup': ['H1a1', 'J1b']
        })
        mock_data.to_csv(hg_path, index=False)
        
        df = load_haplogroup_data(paths)
        assert len(df) == 2
        assert 'haplogroup' in df.columns

    def test_load_metadata_panel(self, temp_dirs):
        """Test loading metadata panel."""
        paths, _ = temp_dirs
        meta_path = paths['raw_data'] / 'metadata_panel.csv'
        
        mock_data = pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'age': [45, 60],
            'sex': ['Male', 'Female'],
            'population': ['EUR', 'AFR'],
            'PC1': [0.1, -0.2],
            'PC2': [0.05, 0.1]
        })
        mock_data.to_csv(meta_path, index=False)
        
        df = load_metadata_panel(paths)
        assert len(df) == 2
        assert 'age' in df.columns
        assert 'PC1' in df.columns

    def test_merge_datasets(self, temp_dirs):
        """Test merging all datasets."""
        paths, _ = temp_dirs
        
        # Create mock data for all sources
        burden_path = paths['processed_data'] / 'burden_per_sample.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'burden_total': [0.05, 0.08]
        }).to_csv(burden_path, index=False)
        
        hg_path = paths['processed_data'] / 'haplogroups.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'haplogroup': ['H1a1', 'J1b']
        }).to_csv(hg_path, index=False)
        
        meta_path = paths['raw_data'] / 'metadata_panel.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'age': [45, 60],
            'sex': ['Male', 'Female'],
            'population': ['EUR', 'AFR']
        }).to_csv(meta_path, index=False)
        
        burden_df = load_burden_data(paths)
        hg_df = load_haplogroup_data(paths)
        meta_df = load_metadata_panel(paths)
        
        merged = merge_datasets(burden_df, hg_df, meta_df)
        
        assert len(merged) == 2
        assert 'burden_total' in merged.columns
        assert 'haplogroup' in merged.columns
        assert 'age' in merged.columns
        assert 'sex' in merged.columns
        assert 'population' in merged.columns
        assert all(merged['sample_id'] == ['HG00001', 'HG00002'])

    def test_merge_mismatched_ids(self, temp_dirs):
        """Test that merge drops samples with missing data in any source."""
        paths, _ = temp_dirs
        
        # Burden has 3 samples
        burden_path = paths['processed_data'] / 'burden_per_sample.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002', 'HG00003'],
            'burden_total': [0.05, 0.08, 0.02]
        }).to_csv(burden_path, index=False)
        
        # Haplogroup only has 2
        hg_path = paths['processed_data'] / 'haplogroups.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002'],
            'haplogroup': ['H1a1', 'J1b']
        }).to_csv(hg_path, index=False)
        
        # Metadata has all 3
        meta_path = paths['raw_data'] / 'metadata_panel.csv'
        pd.DataFrame({
            'sample_id': ['HG00001', 'HG00002', 'HG00003'],
            'age': [45, 60, 55],
            'sex': ['Male', 'Female', 'Male'],
            'population': ['EUR', 'AFR', 'EAS']
        }).to_csv(meta_path, index=False)
        
        burden_df = load_burden_data(paths)
        hg_df = load_haplogroup_data(paths)
        meta_df = load_metadata_panel(paths)
        
        merged = merge_datasets(burden_df, hg_df, meta_df)
        
        # HG00003 should be dropped because it has no haplogroup
        assert len(merged) == 2
        assert 'HG00003' not in merged['sample_id'].values