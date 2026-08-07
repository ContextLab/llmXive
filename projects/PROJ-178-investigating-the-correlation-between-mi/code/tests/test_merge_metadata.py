import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.merge_metadata import (
    load_burden_data, 
    load_haplogroup_data, 
    load_metadata_panel, 
    merge_datasets
)
from config.environment import get_local_paths, ensure_directories

class TestMergeMetadata:
    """Tests for T018: Metadata merge logic."""

    @pytest.fixture(autouse=True)
    def setup_mock_data(self, tmp_path):
        """Create mock data files to simulate previous task outputs."""
        self.tmp_dir = tmp_path
        self.raw_dir = self.tmp_dir / 'raw'
        self.processed_dir = self.tmp_dir / 'processed'
        self.logs_dir = self.tmp_dir / 'logs'
        
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.logs_dir.mkdir()
        
        # Create mock burden data
        burden_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'total_burden': [0.05, 0.12, 0.08],
            'low_depth_burden': [0.02, 0.05, 0.03],
            'med_depth_burden': [0.02, 0.04, 0.03],
            'high_depth_burden': [0.01, 0.03, 0.02]
        })
        burden_df.to_csv(self.processed_dir / 'burden_per_sample.csv', index=False)
        
        # Create mock haplogroup data
        hap_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3'],
            'haplogroup': ['H1', 'J2', 'T1']
        })
        hap_df.to_csv(self.processed_dir / 'haplogroups.csv', index=False)
        
        # Create mock metadata panel
        meta_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S4'], # S4 missing in others
            'age': [65, 40, 55, 30],
            'sex': ['M', 'F', 'M', 'F'],
            'population': ['EUR', 'AFR', 'EAS', 'AMR'],
            'PC1': [0.1, -0.2, 0.3, -0.1],
            'PC2': [0.05, -0.1, 0.2, 0.0]
        })
        meta_df.to_csv(self.raw_dir / '1000G_metadata_panel.csv', index=False)
        
        # Patch get_local_paths to return our temp dirs
        self.original_get_paths = get_local_paths
        def mock_get_paths():
            return {
                'raw_data': self.raw_dir,
                'processed_data': self.processed_dir,
                'logs': self.logs_dir,
                'figures': self.processed_dir,
                'code_root': self.tmp_dir
            }
        
        import config.environment
        config.environment.get_local_paths = mock_get_paths
        
        yield self.processed_dir / 'mito_aging_dataset.csv'
        
        # Restore
        config.environment.get_local_paths = self.original_get_paths

    def test_merge_datasets_creates_file(self, setup_mock_data):
        """Verify that merge_datasets creates the output CSV."""
        output_path = setup_mock_data
        
        # Run the merge
        from analysis.merge_metadata import main
        result_path = main()
        
        assert Path(result_path).exists(), "Output file was not created"
        
        # Verify content
        df = pd.read_csv(result_path)
        assert 'sample_id' in df.columns
        assert 'total_burden' in df.columns
        assert 'haplogroup' in df.columns
        assert 'age' in df.columns
        assert 'sex' in df.columns
        assert 'population' in df.columns
        assert 'PC1' in df.columns
        assert 'PC2' in df.columns

    def test_merge_handles_missing_samples(self, setup_mock_data):
        """Verify that samples missing in one dataset are handled (left join behavior)."""
        output_path = setup_mock_data
        
        from analysis.merge_metadata import main
        main()
        
        df = pd.read_csv(output_path)
        
        # S4 is in metadata but not in burden/haplogroup
        # Since we merge burden (left) with haplogroup (left) then metadata (left)
        # S4 should be present if it's in the leftmost frame? 
        # Wait: burden has S1, S2, S3. Metadata has S1, S2, S3, S4.
        # Merge burden (S1-S3) with metadata (S1-S4) -> Left join on burden means S4 is dropped?
        # The task description says "Join...". Usually this implies an inner join of available data
        # or a left join on the primary key (burden). 
        # T018 description: "join burden, haplogroups, age...".
        # Implementation used: burden (left) -> haplogroup (left) -> metadata (left).
        # If metadata is merged on the left of the result (S1-S3), S4 is dropped.
        # This is correct for analysis-ready data where we need ALL columns.
        
        assert len(df) == 3, "Expected 3 samples (intersection of burden and metadata)"
        assert 'S4' not in df['sample_id'].values

    def test_column_types_correct(self, setup_mock_data):
        """Verify numeric columns are numeric."""
        output_path = setup_mock_data
        from analysis.merge_metadata import main
        main()
        
        df = pd.read_csv(output_path)
        
        # Check numeric columns
        assert pd.api.types.is_numeric_dtype(df['age'])
        assert pd.api.types.is_numeric_dtype(df['total_burden'])
        assert pd.api.types.is_numeric_dtype(df['PC1'])
        
        # Check categorical
        assert df['sex'].dtype == object or pd.api.types.is_categorical_dtype(df['sex'])
        assert df['population'].dtype == object or pd.api.types.is_categorical_dtype(df['population'])
        assert df['haplogroup'].dtype == object or pd.api.types.is_categorical_dtype(df['haplogroup'])