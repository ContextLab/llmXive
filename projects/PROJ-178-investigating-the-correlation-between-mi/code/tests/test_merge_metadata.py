import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent to path for imports if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.merge_metadata import load_burden_data, load_haplogroup_data, load_metadata_panel, merge_datasets
from config.environment import get_local_paths

class TestMergeMetadata:
    
    @pytest.fixture
    def temp_data_dirs(self, tmp_path):
        """Create temporary directories mimicking the project structure."""
        # Setup a mock directory structure
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        logs_dir = tmp_path / "logs"
        
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        
        # Create mock data files
        # 1. Burden data
        burden_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S4'],
            'burden': [0.05, 0.12, 0.03, 0.08],
            'depth_bin': ['Low', 'Medium', 'Low', 'High']
        })
        burden_path = processed_dir / "burden_per_sample.csv"
        burden_df.to_csv(burden_path, index=False)
        
        # 2. Haplogroup data
        haplo_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S5'], # S4 missing haplogroup, S5 missing burden
            'haplogroup': ['H1', 'J2', 'U5', 'H2']
        })
        haplo_path = processed_dir / "haplogroups.csv"
        haplo_df.to_csv(haplo_path, index=False)
        
        # 3. Metadata panel
        meta_df = pd.DataFrame({
            'sample_id': ['S1', 'S2', 'S3', 'S4', 'S6'], # S5 missing metadata, S6 missing others
            'age': [50, 65, 40, 70, 30],
            'sex': ['M', 'F', 'M', 'F', 'M'],
            'population': ['EUR', 'AFR', 'EAS', 'EUR', 'SAS'],
            'PC1': [0.1, 0.2, 0.3, 0.4, 0.5],
            'PC2': [0.05, 0.15, 0.25, 0.35, 0.45]
        })
        meta_path = processed_dir / "metadata_panel.csv"
        meta_df.to_csv(meta_path, index=False)
        
        # Mock environment config to use these paths
        # We will patch the functions to return these specific paths
        mock_paths = {
            'processed_burden': str(burden_path),
            'processed_haplogroups': str(haplo_path),
            'metadata_panel': str(meta_path),
            'processed_dataset': str(processed_dir / "mito_aging_dataset.csv")
        }
        
        return mock_paths, tmp_path

    def test_merge_logic_inner_join(self, temp_data_dirs):
        """Test that merge_datasets correctly performs inner joins."""
        mock_paths, tmp_path = temp_data_dirs
        
        # Patch the get_local_paths to return our mock paths
        from config import environment
        original_get_local_paths = environment.get_local_paths
        
        def mock_get_local_paths():
            return mock_paths
        
        environment.get_local_paths = mock_get_local_paths
        
        try:
            # Run merge
            result = merge_datasets()
            
            # Expected: S1, S2, S3 (present in all three)
            # S4: Missing haplogroup -> excluded
            # S5: Missing burden -> excluded
            # S6: Missing burden/haplogroup -> excluded
            assert len(result) == 3, f"Expected 3 samples, got {len(result)}"
            
            assert set(result['sample_id'].tolist()) == {'S1', 'S2', 'S3'}
            
            # Check columns
            assert 'burden' in result.columns
            assert 'haplogroup' in result.columns
            assert 'age' in result.columns
            assert 'sex' in result.columns
            assert 'PC1' in result.columns
            
        finally:
            environment.get_local_paths = original_get_local_paths

    def test_merge_data_integrity(self, temp_data_dirs):
        """Test that data values are preserved correctly after merge."""
        mock_paths, tmp_path = temp_data_dirs
        
        from config import environment
        original_get_local_paths = environment.get_local_paths
        
        def mock_get_local_paths():
            return mock_paths
        
        environment.get_local_paths = mock_get_local_paths
        
        try:
            result = merge_datasets()
            
            # Check specific values for S1
            s1_row = result[result['sample_id'] == 'S1'].iloc[0]
            assert s1_row['burden'] == 0.05
            assert s1_row['haplogroup'] == 'H1'
            assert s1_row['age'] == 50
            assert s1_row['population'] == 'EUR'
            
        finally:
            environment.get_local_paths = original_get_local_paths

    def test_missing_critical_columns_raises(self, temp_data_dirs):
        """Test that missing critical columns in metadata raises an error."""
        mock_paths, tmp_path = temp_data_dirs
        
        # Modify metadata to remove 'age'
        meta_df = pd.DataFrame({
            'sample_id': ['S1', 'S2'],
            'sex': ['M', 'F'],
            'population': ['EUR', 'AFR'],
            'PC1': [0.1, 0.2],
            'PC2': [0.05, 0.15]
        })
        meta_path = mock_paths['metadata_panel']
        meta_df.to_csv(meta_path, index=False)
        
        from config import environment
        original_get_local_paths = environment.get_local_paths
        
        def mock_get_local_paths():
            return mock_paths
        
        environment.get_local_paths = mock_get_local_paths
        
        try:
            with pytest.raises(ValueError, match="Missing critical columns"):
                merge_datasets()
        finally:
            environment.get_local_paths = original_get_local_paths