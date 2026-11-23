import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
import sys
import json

# Add the project root to the path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.preprocessing.dft_filter import filter_dft_entries, is_dft_entry

class TestDFTFilterIntegration:
    """
    Integration tests for the DFT filter logic (T021).
    Ensures DFT targets are excluded as per specification.
    """

    def test_filter_dft_by_source_type_keyword(self):
        """Test that entries with DFT keywords in source_type are excluded."""
        data = {
            'composition': ['Co2MnGa', 'Fe3Al', 'Ni2MnSn'],
            'source_type': ['Experimental', 'DFT Calculation', 'Simulation Study'],
            'target_source': ['Journal', 'Materials Project', 'Journal'],
            'coercivity': [10.0, 0.0, 5.0],
            'saturation_magnetization': [100.0, 0.0, 90.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        # Should keep only the first row (Experimental)
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['composition'] == 'Co2MnGa'
        
        # Check excluded count
        assert len(excluded) == 2
        
        # Verify exclusion reasons
        reasons = [e['reason'] for e in excluded]
        assert any('source_type contains DFT keyword' in r for r in reasons)

    def test_filter_dft_by_target_source(self):
        """Test that entries with target_source 'Materials Project' are excluded."""
        data = {
            'composition': ['Co2MnGa', 'Fe3Al', 'Ni2MnSn'],
            'source_type': ['Experimental', 'Experimental', 'Experimental'],
            'target_source': ['Journal', 'Materials Project', 'Journal'],
            'coercivity': [10.0, 20.0, 30.0],
            'saturation_magnetization': [100.0, 110.0, 120.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        # Should keep 2 rows (exclude Materials Project)
        assert len(filtered_df) == 2
        assert len(excluded) == 1
        
        assert excluded[0]['composition'] == 'Fe3Al'
        assert 'target_source is' in excluded[0]['reason']

    def test_filter_dft_combined_conditions(self):
        """Test filtering when both conditions are met or only one is met."""
        data = {
            'composition': ['A', 'B', 'C', 'D'],
            'source_type': ['DFT', 'Experimental', 'Simulation', 'Experimental'],
            'target_source': ['Materials Project', 'Journal', 'Journal', 'Materials Project'],
            'coercivity': [1, 2, 3, 4],
            'saturation_magnetization': [10, 20, 30, 40]
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        # A: DFT + Materials Project -> Excluded
        # B: Experimental + Journal -> Kept
        # C: Simulation + Journal -> Excluded
        # D: Experimental + Materials Project -> Excluded
        
        assert len(filtered_df) == 1
        assert filtered_df.iloc[0]['composition'] == 'B'
        assert len(excluded) == 3

    def test_filter_empty_dataframe(self):
        """Test that an empty DataFrame is handled gracefully."""
        df = pd.DataFrame(columns=['composition', 'source_type', 'target_source'])
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        assert len(filtered_df) == 0
        assert len(excluded) == 0

    def test_filter_no_dft_entries(self):
        """Test that a DataFrame with no DFT entries remains unchanged."""
        data = {
            'composition': ['Co2MnGa', 'Fe3Al'],
            'source_type': ['Experimental', 'Experimental'],
            'target_source': ['Journal', 'Journal'],
            'coercivity': [10.0, 20.0],
            'saturation_magnetization': [100.0, 110.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        assert len(filtered_df) == 2
        assert len(excluded) == 0
        pd.testing.assert_frame_equal(filtered_df, df)

    def test_filter_saves_output_file(self):
        """Test that the function saves the output file when path is provided."""
        data = {
            'composition': ['Co2MnGa', 'Fe3Al'],
            'source_type': ['Experimental', 'DFT'],
            'target_source': ['Journal', 'Journal'],
            'coercivity': [10.0, 20.0],
            'saturation_magnetization': [100.0, 110.0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'filtered.csv'
            filtered_df, excluded = filter_dft_entries(df, output_path=output_path, log_excluded=True)
            
            assert output_path.exists()
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 1
            
            # Check for excluded log file
            log_path = output_path.with_suffix('.excluded_log.json')
            assert log_path.exists()
            with open(log_path) as f:
                log_data = json.load(f)
            assert len(log_data) == 1

    def test_case_insensitivity(self):
        """Test that keyword matching is case-insensitive."""
        data = {
            'composition': ['A', 'B', 'C'],
            'source_type': ['dft', 'CALCULATED', 'simulation'],
            'target_source': ['Journal', 'Journal', 'Journal'],
            'coercivity': [1, 2, 3],
            'saturation_magnetization': [10, 20, 30]
        }
        df = pd.DataFrame(data)
        
        filtered_df, excluded = filter_dft_entries(df, log_excluded=True)
        
        # All should be excluded
        assert len(filtered_df) == 0
        assert len(excluded) == 3
        
        # Test target_source case insensitivity
        data2 = {
            'composition': ['A'],
            'source_type': ['Experimental'],
            'target_source': ['materials project'],
            'coercivity': [1],
            'saturation_magnetization': [10]
        }
        df2 = pd.DataFrame(data2)
        filtered_df2, excluded2 = filter_dft_entries(df2, log_excluded=True)
        assert len(filtered_df2) == 0
        assert len(excluded2) == 1