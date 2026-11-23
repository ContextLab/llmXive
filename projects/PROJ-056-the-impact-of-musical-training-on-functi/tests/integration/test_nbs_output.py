import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.analysis.write_nbs_results import load_nbs_results, write_nbs_results

class TestNBSSOutput:
    """Integration tests for NBS results output generation (T031)."""

    def test_write_nbs_results_creates_file(self, tmp_path):
        """Verify that write_nbs_results creates the output file."""
        input_data = {
            'component_id': [1, 2],
            'size_edges': [15, 8],
            'p_value_fwer': [0.032, 0.105]
        }
        df = pd.DataFrame(input_data)
        
        output_file = tmp_path / "nbs_results.csv"
        
        write_nbs_results(df, str(output_file))
        
        assert output_file.exists(), "Output file was not created."
        
        # Verify content
        result_df = pd.read_csv(output_file)
        assert len(result_df) == 2
        assert 'component_id' in result_df.columns
        assert 'size_edges' in result_df.columns
        assert 'p_value_fwer' in result_df.columns
        assert result_df['component_id'].iloc[0] == 1

    def test_load_nbs_results_validates_columns(self, tmp_path):
        """Verify that load_nbs_results raises error on missing columns."""
        bad_data = {
            'component_id': [1],
            'invalid_col': [0.5]
        }
        df = pd.DataFrame(bad_data)
        temp_file = tmp_path / "bad_nbs.csv"
        df.to_csv(temp_file, index=False)
        
        with pytest.raises(ValueError) as exc_info:
            load_nbs_results(str(temp_file))
        
        assert "Missing required columns" in str(exc_info.value)

    def test_load_nbs_results_file_not_found(self):
        """Verify that load_nbs_results raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_nbs_results("non_existent_file.csv")

    def test_full_pipeline_integration(self, tmp_path):
        """Simulate the full flow: Generate data -> Write -> Read back."""
        # Create realistic NBS data
        data = {
            'component_id': [1, 2, 3],
            'size_edges': [42, 12, 5],
            'p_value_fwer': [0.001, 0.045, 0.210]
        }
        df = pd.DataFrame(data)
        
        output_path = tmp_path / "nbs_results.csv"
        
        # Write
        write_nbs_results(df, str(output_path))
        
        # Read back
        loaded_df = load_nbs_results(str(output_path))
        
        # Assertions
        assert len(loaded_df) == 3
        assert loaded_df['p_value_fwer'].iloc[0] == 0.001
        assert loaded_df['size_edges'].iloc[1] == 12
        assert loaded_df['component_id'].tolist() == [1, 2, 3]
