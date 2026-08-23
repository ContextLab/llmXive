"""
Integration tests for the T015 consolidation pipeline.

Tests the full flow from processed interim files to consolidated Parquet output.
"""
import os
import sys
import pytest
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.consolidate import load_all_processed_datasets, write_consolidated_parquet
from code.config import get_data_path


class TestConsolidationPipeline:
    """Integration tests for T015 consolidation."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory structure with test files."""
        # Create directory structure
        interim_dir = tmp_path / "interim"
        processed_dir = tmp_path / "processed"
        interim_dir.mkdir()
        processed_dir.mkdir()
        
        # Create mock processed CSV files
        # Sample 1: Aluminum, 20% reduction
        df_al_20 = pd.DataFrame({
            'phi1': [0, 10, 20],
            'Phi': [45, 45, 45],
            'phi2': [0, 0, 0],
            'confidence': [0.9, 0.8, 0.7],
            'material': ['Al', 'Al', 'Al'],
            'reduction': [20, 20, 20]
        })
        (interim_dir / "Al_20.csv").write_text(df_al_20.to_csv(index=False))
        
        # Sample 2: Copper, 40% reduction
        df_cu_40 = pd.DataFrame({
            'phi1': [39, 39, 39],
            'Phi': [39, 39, 39],
            'phi2': [0, 0, 0],
            'confidence': [0.95, 0.92, 0.88],
            'material': ['Cu', 'Cu', 'Cu'],
            'reduction': [40, 40, 40]
        })
        (interim_dir / "Cu_40.csv").write_text(df_cu_40.to_csv(index=False))
        
        # Sample 3: Nickel, 60% reduction
        df_ni_60 = pd.DataFrame({
            'phi1': [59, 59, 59],
            'Phi': [37, 37, 37],
            'phi2': [63, 63, 63],
            'confidence': [0.85, 0.82, 0.79],
            'material': ['Ni', 'Ni', 'Ni'],
            'reduction': [60, 60, 60]
        })
        (interim_dir / "Ni_60.csv").write_text(df_ni_60.to_csv(index=False))
        
        # Sample 4: Low reliability (should be excluded)
        df_low_rel = pd.DataFrame({
            'phi1': [0, 0, 0],
            'Phi': [0, 0, 0],
            'phi2': [0, 0, 0],
            'confidence': [0.05, 0.06, 0.07],  # Very low confidence
            'material': ['Al', 'Al', 'Al'],
            'reduction': [10, 10, 10]
        })
        (interim_dir / "Al_10_low_rel.csv").write_text(df_low_rel.to_csv(index=False))
        
        return {
            'base': tmp_path,
            'interim': interim_dir,
            'processed': processed_dir,
            'expected_files': ['Al_20.csv', 'Cu_40.csv', 'Ni_60.csv', 'Al_10_low_rel.csv']
        }
    
    def test_load_all_processed_datasets(self, temp_data_dir):
        """Test loading all processed datasets from interim directory."""
        # Temporarily override DATA_PATH
        original_path = os.environ.get('DATA_PATH')
        os.environ['DATA_PATH'] = str(temp_data_dir['base'])
        
        try:
            datasets = load_all_processed_datasets()
            
            # Should load 3 datasets (excluding low reliability)
            assert len(datasets) == 3, f"Expected 3 datasets, got {len(datasets)}"
            
            # Check that low reliability sample was excluded
            materials = []
            for df in datasets:
                materials.extend(df['material'].unique())
            
            assert 'Al' in materials
            assert 'Cu' in materials
            assert 'Ni' in materials
            
            # Verify no low confidence samples (confidence < 0.1 should be filtered in T014)
            for df in datasets:
                if 'confidence' in df.columns:
                    assert df['confidence'].min() >= 0.1, "Low confidence samples should be filtered"
            
        finally:
            if original_path:
                os.environ['DATA_PATH'] = original_path
            else:
                os.environ.pop('DATA_PATH', None)
    
    def test_write_consolidated_parquet(self, temp_data_dir):
        """Test writing consolidated Parquet file."""
        original_path = os.environ.get('DATA_PATH')
        os.environ['DATA_PATH'] = str(temp_data_dir['base'])
        
        try:
            datasets = load_all_processed_datasets()
            output_path = write_consolidated_parquet(datasets, temp_data_dir['processed'] / "test_output.parquet")
            
            # Verify file exists
            assert output_path.exists(), "Output Parquet file should exist"
            
            # Verify file can be read
            result_df = pq.read_table(output_path).to_pandas()
            
            # Check row count (should be 9 rows: 3 from each valid sample)
            assert len(result_df) == 9, f"Expected 9 rows, got {len(result_df)}"
            
            # Check columns
            required_cols = ['phi1', 'Phi', 'phi2', 'confidence', 'material', 'reduction']
            for col in required_cols:
                assert col in result_df.columns, f"Missing column: {col}"
            
            # Check metadata
            metadata = result_df['material'].unique()
            assert set(metadata) == {'Al', 'Cu', 'Ni'}, f"Unexpected materials: {metadata}"
            
            # Check reduction values
            reductions = sorted(result_df['reduction'].unique())
            assert reductions == [20, 40, 60], f"Unexpected reductions: {reductions}"
            
        finally:
            if original_path:
                os.environ['DATA_PATH'] = original_path
            else:
                os.environ.pop('DATA_PATH', None)
    
    def test_consolidation_with_empty_interim(self, tmp_path):
        """Test handling of empty interim directory."""
        interim_dir = tmp_path / "interim"
        interim_dir.mkdir()
        
        original_path = os.environ.get('DATA_PATH')
        os.environ['DATA_PATH'] = str(tmp_path)
        
        try:
            with pytest.raises(FileNotFoundError):
                load_all_processed_datasets()
        finally:
            if original_path:
                os.environ['DATA_PATH'] = original_path
            else:
                os.environ.pop('DATA_PATH', None)
    
    def test_metadata_preservation(self, temp_data_dir):
        """Test that metadata is preserved in Parquet file."""
        original_path = os.environ.get('DATA_PATH')
        os.environ['DATA_PATH'] = str(temp_data_dir['base'])
        
        try:
            datasets = load_all_processed_datasets()
            output_path = write_consolidated_parquet(datasets, temp_data_dir['processed'] / "metadata_test.parquet")
            
            # Read Parquet file with metadata
            parquet_file = pq.ParquetFile(output_path)
            metadata = parquet_file.metadata.metadata
            
            # Check that custom metadata exists
            assert metadata is not None, "Parquet metadata should exist"
            
            # Check specific metadata fields
            assert b'source' in metadata, "Source metadata should be present"
            assert b'created_by' in metadata, "Created_by metadata should be present"
            
            # Verify metadata values
            assert metadata[b'source'] == b'T015_consolidation_pipeline'
            assert metadata[b'created_by'] == b'consolidate.py'
            
        finally:
            if original_path:
                os.environ['DATA_PATH'] = original_path
            else:
                os.environ.pop('DATA_PATH', None)