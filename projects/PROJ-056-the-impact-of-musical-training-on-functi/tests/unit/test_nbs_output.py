import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from analysis.output_nbs_results import load_nbs_results, write_nbs_results, process_nbs_output
from analysis.run_nbs import load_connectivity_matrices, network_based_statistic

class TestNBSOutput:
    """Tests for NBS results output functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_dir = tmp_path
        self.data_dir = self.tmp_dir / "data" / "processed"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Store original paths
        self.original_processed_dir = Path("data/processed")
        
        # Create temporary processed directory
        if not self.original_processed_dir.exists():
            self.original_processed_dir.mkdir(parents=True, exist_ok=True)
        
        yield
        
        # Cleanup
        if self.original_processed_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.original_processed_dir)
            except:
                pass
    
    def test_write_nbs_results_creates_file(self):
        """Test that write_nbs_results creates the output file."""
        # Create sample data
        df = pd.DataFrame({
            'component_id': [1, 2, 3],
            'size_edges': [10, 25, 15],
            'p_value_fwer': [0.01, 0.03, 0.07]
        })
        
        output_path = str(self.tmp_dir / "test_nbs_results.csv")
        
        # Write results
        result_path = write_nbs_results(df, output_path)
        
        # Verify file exists
        assert os.path.exists(result_path)
        assert Path(result_path).exists()
        
        # Verify content
        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 3
        assert 'component_id' in loaded_df.columns
        assert 'size_edges' in loaded_df.columns
        assert 'p_value_fwer' in loaded_df.columns
    
    def test_load_nbs_results_reads_correctly(self):
        """Test that load_nbs_results reads the file correctly."""
        # Create sample data
        df = pd.DataFrame({
            'component_id': [1, 2, 3],
            'size_edges': [10, 25, 15],
            'p_value_fwer': [0.01, 0.03, 0.07]
        })
        
        input_path = str(self.tmp_dir / "test_nbs_raw.csv")
        df.to_csv(input_path, index=False)
        
        # Load results
        loaded_df = load_nbs_results(input_path)
        
        # Verify content
        assert len(loaded_df) == 3
        assert list(loaded_df['component_id']) == [1, 2, 3]
        assert list(loaded_df['size_edges']) == [10, 25, 15]
        assert list(loaded_df['p_value_fwer']) == [0.01, 0.03, 0.07]
    
    def test_load_nbs_results_missing_file_raises(self):
        """Test that load_nbs_results raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_nbs_results("nonexistent_file.csv")
    
    def test_load_nbs_results_missing_columns_raises(self):
        """Test that load_nbs_results raises ValueError for missing columns."""
        df = pd.DataFrame({
            'component_id': [1, 2],
            'size_edges': [10, 25]
            # Missing p_value_fwer
        })
        
        input_path = str(self.tmp_dir / "incomplete.csv")
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="missing required columns"):
            load_nbs_results(input_path)
    
    def test_process_nbs_output_sorts_and_writes(self):
        """Test that process_nbs_output sorts and writes correctly."""
        # Create sample data (unsorted)
        df = pd.DataFrame({
            'component_id': [3, 1, 2],
            'size_edges': [15, 10, 25],
            'p_value_fwer': [0.07, 0.01, 0.03]
        })
        
        input_path = str(self.tmp_dir / "input_nbs.csv")
        df.to_csv(input_path, index=False)
        
        output_path = str(self.tmp_dir / "output_nbs.csv")
        
        # Process
        result_df = process_nbs_output(input_path, output_path)
        
        # Verify sorted by p_value_fwer
        assert list(result_df['p_value_fwer']) == [0.01, 0.03, 0.07]
        assert list(result_df['component_id']) == [1, 2, 3]
        
        # Verify file exists
        assert os.path.exists(output_path)
    
    def test_nbs_results_csv_format(self):
        """Test that NBS results CSV has the exact required format."""
        # Create sample data
        df = pd.DataFrame({
            'component_id': [1, 2],
            'size_edges': [100, 50],
            'p_value_fwer': [0.001, 0.049]
        })
        
        output_path = str(self.tmp_dir / "nbs_results.csv")
        write_nbs_results(df, output_path)
        
        # Read and verify
        loaded = pd.read_csv(output_path)
        
        # Check required columns
        assert 'component_id' in loaded.columns
        assert 'size_edges' in loaded.columns
        assert 'p_value_fwer' in loaded.columns
        
        # Check data types
        assert loaded['component_id'].dtype in ['int64', 'int32']
        assert loaded['size_edges'].dtype in ['int64', 'int32']
        assert loaded['p_value_fwer'].dtype in ['float64', 'float32']
        
        # Check values
        assert len(loaded) == 2
        assert loaded['size_edges'].min() > 0
        assert (loaded['p_value_fwer'] >= 0).all()
        assert (loaded['p_value_fwer'] <= 1).all()
    
    def test_empty_nbs_results_raises(self):
        """Test that loading empty NBS results raises ValueError."""
        input_path = str(self.tmp_dir / "empty_nbs.csv")
        pd.DataFrame(columns=['component_id', 'size_edges', 'p_value_fwer']).to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="empty"):
            load_nbs_results(input_path)