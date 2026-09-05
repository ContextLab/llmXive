import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.io import filter_by_phase_label, load_and_filter_dataset, save_csv, load_csv

class TestFilterByPhaseLabel:
    def test_filter_valid_labels(self):
        """Test that valid labels are kept."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuZr', 'AuSi'],
            'phase': ['amorphous', 'crystalline', 'unknown'],
            'value': [1, 2, 3]
        })
        
        result = filter_by_phase_label(df)
        
        assert len(result) == 2
        assert 'unknown' not in result['phase'].values
        assert 'amorphous' in result['phase'].values
        assert 'crystalline' in result['phase'].values

    def test_filter_case_insensitive(self):
        """Test that filtering is case-insensitive."""
        df = pd.DataFrame({
            'composition': ['Fe2O3', 'CuZr'],
            'phase': ['AMORPHOUS', 'Crystalline'],
            'value': [1, 2]
        })
        
        result = filter_by_phase_label(df)
        
        assert len(result) == 2

    def test_filter_missing_column(self):
        """Test that ValueError is raised if 'phase' column is missing."""
        df = pd.DataFrame({
            'composition': ['Fe2O3'],
            'value': [1]
        })
        
        with pytest.raises(ValueError, match="must contain a 'phase' column"):
            filter_by_phase_label(df)

    def test_custom_valid_labels(self):
        """Test filtering with custom valid labels."""
        df = pd.DataFrame({
            'composition': ['A', 'B', 'C'],
            'phase': ['solid', 'liquid', 'gas'],
            'value': [1, 2, 3]
        })
        
        result = filter_by_phase_label(df, valid_labels=['solid', 'liquid'])
        
        assert len(result) == 2
        assert 'gas' not in result['phase'].values

    def test_empty_dataframe(self):
        """Test filtering an empty dataframe."""
        df = pd.DataFrame(columns=['composition', 'phase'])
        result = filter_by_phase_label(df)
        assert len(result) == 0

    def test_all_invalid_labels(self):
        """Test filtering when all labels are invalid."""
        df = pd.DataFrame({
            'composition': ['A', 'B'],
            'phase': ['unknown', 'none'],
            'value': [1, 2]
        })
        
        result = filter_by_phase_label(df)
        assert len(result) == 0

class TestLoadAndFilterDataset:
    def test_load_and_filter_temp_file(self):
        """Test loading from a temporary file and filtering."""
        df_input = pd.DataFrame({
            'composition': ['A', 'B', 'C'],
            'phase': ['amorphous', 'crystalline', 'invalid'],
            'value': [1, 2, 3]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_path = Path(tmpdir) / "output.csv"
            
            df_input.to_csv(input_path, index=False)
            
            result = load_and_filter_dataset(input_path, output_path)
            
            assert len(result) == 2
            assert Path(output_path).exists()
            
            # Verify output file content
            saved_df = load_csv(output_path)
            assert len(saved_df) == 2
            assert 'invalid' not in saved_df['phase'].values