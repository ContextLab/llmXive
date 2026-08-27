import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.merge_metadata import merge_datasets, load_burden_data, load_haplogroup_data, load_metadata_panel

class TestMergeMetadata:
    """Test suite for metadata merging functionality."""
    
    @pytest.fixture
    def temp_data_dirs(self):
        """Create temporary directories for test data."""
        temp_dir = tempfile.mkdtemp()
        data_raw = Path(temp_dir) / 'data' / 'raw'
        data_processed = Path(temp_dir) / 'data' / 'processed'
        data_raw.mkdir(parents=True)
        data_processed.mkdir(parents=True)
        
        # Mock environment paths
        original_get_local_paths = None
        try:
            from config import environment
            original_get_local_paths = environment.get_local_paths
            
            def mock_get_local_paths():
                return {
                    'data_raw': data_raw,
                    'data_processed': data_processed,
                    'logs': Path(temp_dir) / 'logs',
                    'figures': Path(temp_dir) / 'figures'
                }
            
            environment.get_local_paths = mock_get_local_paths
            
        except ImportError:
            pass
        
        yield {
            'temp_dir': temp_dir,
            'data_raw': data_raw,
            'data_processed': data_processed
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
        if original_get_local_paths:
            environment.get_local_paths = original_get_local_paths

    def test_merge_datasets_basic(self, temp_data_dirs):
        """Test basic merging of datasets with all required columns."""
        data_processed = temp_data_dirs['data_processed']
        
        # Create mock burden data
        burden_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097', 'HG00098'],
            'heteroplasmy_burden': [0.15, 0.22, 0.08],
            'sequencing_depth': [100, 150, 120]
        })
        burden_df.to_csv(data_processed / 'heteroplasmy_burden.csv', index=False)
        
        # Create mock haplogroup data
        haplogroup_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097', 'HG00098'],
            'haplogroup': ['H1', 'J1', 'U5b']
        })
        haplogroup_df.to_csv(data_processed / 'haplogroups.csv', index=False)
        
        # Create mock metadata panel
        metadata_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097', 'HG00098'],
            'age': [45, 62, 38],
            'sex': ['Male', 'Female', 'Male'],
            'superpopulation': ['EUR', 'AFR', 'EAS'],
            'PC1': [0.1, 0.2, 0.3],
            'PC2': [0.05, 0.15, 0.25]
        })
        metadata_df.to_csv(temp_data_dirs['data_raw'] / 'phase3_sample_info.tsv', sep='\t', index=False)
        
        # Run merge
        merged = merge_datasets()
        
        # Verify results
        assert len(merged) == 3
        assert 'heteroplasmy_burden' in merged.columns
        assert 'haplogroup' in merged.columns
        assert 'age' in merged.columns
        assert 'sex' in merged.columns
        assert 'population' in merged.columns  # Should be renamed from superpopulation
        
        # Check specific values
        assert merged.loc[merged['sample_id'] == 'HG00096', 'haplogroup'].iloc[0] == 'H1'
        assert merged.loc[merged['sample_id'] == 'HG00096', 'age'].iloc[0] == 45

    def test_merge_datasets_missing_samples(self, temp_data_dirs):
        """Test merging when some samples are missing in one dataset."""
        data_processed = temp_data_dirs['data_processed']
        
        # Create burden data with 3 samples
        burden_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097', 'HG00098'],
            'heteroplasmy_burden': [0.15, 0.22, 0.08],
        })
        burden_df.to_csv(data_processed / 'heteroplasmy_burden.csv', index=False)
        
        # Create haplogroup data with only 2 samples (missing HG00098)
        haplogroup_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097'],
            'haplogroup': ['H1', 'J1']
        })
        haplogroup_df.to_csv(data_processed / 'haplogroups.csv', index=False)
        
        # Create metadata with all 3 samples
        metadata_df = pd.DataFrame({
            'sample_id': ['HG00096', 'HG00097', 'HG00098'],
            'age': [45, 62, 38],
            'sex': ['Male', 'Female', 'Male'],
            'superpopulation': ['EUR', 'AFR', 'EAS']
        })
        metadata_df.to_csv(temp_data_dirs['data_raw'] / 'phase3_sample_info.tsv', sep='\t', index=False)
        
        # Run merge
        merged = merge_datasets()
        
        # Verify results
        assert len(merged) == 3  # All burden samples retained
        assert pd.isna(merged.loc[merged['sample_id'] == 'HG00098', 'haplogroup'].iloc[0])
        assert merged.loc[merged['sample_id'] == 'HG00096', 'haplogroup'].iloc[0] == 'H1'

    def test_merge_datasets_missing_columns(self, temp_data_dirs):
        """Test that missing required columns raise an error."""
        data_processed = temp_data_dirs['data_processed']
        
        # Create burden data missing required column
        burden_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'heteroplasmy_burden': [0.15],
        })
        burden_df.to_csv(data_processed / 'heteroplasmy_burden.csv', index=False)
        
        # Create minimal haplogroup data
        haplogroup_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'haplogroup': ['H1']
        })
        haplogroup_df.to_csv(data_processed / 'haplogroups.csv', index=False)
        
        # Create metadata missing age column
        metadata_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'sex': ['Male'],
            'superpopulation': ['EUR']
        })
        metadata_df.to_csv(temp_data_dirs['data_raw'] / 'phase3_sample_info.tsv', sep='\t', index=False)
        
        # Should raise ValueError due to missing 'age' column
        with pytest.raises(ValueError, match="Missing required columns"):
            merge_datasets()

    def test_merge_datasets_column_renaming(self, temp_data_dirs):
        """Test that metadata columns are properly renamed."""
        data_processed = temp_data_dirs['data_processed']
        
        # Create burden data
        burden_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'heteroplasmy_burden': [0.15],
        })
        burden_df.to_csv(data_processed / 'heteroplasmy_burden.csv', index=False)
        
        # Create haplogroup data
        haplogroup_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'haplogroup': ['H1']
        })
        haplogroup_df.to_csv(data_processed / 'haplogroups.csv', index=False)
        
        # Create metadata with various column name variations
        metadata_df = pd.DataFrame({
            'sample_id': ['HG00096'],
            'AGE': [45],  # Uppercase
            'SEX': ['Male'],  # Uppercase
            'superpopulation': ['EUR']
        })
        metadata_df.to_csv(temp_data_dirs['data_raw'] / 'phase3_sample_info.tsv', sep='\t', index=False)
        
        # Run merge
        merged = merge_datasets()
        
        # Verify columns are renamed to lowercase standard names
        assert 'age' in merged.columns
        assert 'sex' in merged.columns
        assert 'population' in merged.columns
        assert 'AGE' not in merged.columns
        assert 'SEX' not in merged.columns
        assert 'superpopulation' not in merged.columns
