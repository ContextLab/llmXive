import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.clean import map_soc_codes, process_data, get_memory_usage_gb

class TestMapSOC:
    def test_map_soc_codes_with_llt(self):
        """Test mapping with LLT_CODE column."""
        df = pd.DataFrame({
            'LLT_CODE': ['10000001', '10000002', '10000026'],
            'OTHER': ['A', 'B', 'C']
        })
        result = map_soc_codes(df)
        assert 'SOC' in result.columns
        assert result.loc[0, 'SOC'] == 'Blood and lymphatic system disorders'
        assert result.loc[1, 'SOC'] == 'Cardiac disorders'
        assert result.loc[2, 'SOC'] == 'Vascular disorders'

    def test_map_soc_codes_with_unknown_code(self):
        """Test mapping with a code not in dictionary."""
        df = pd.DataFrame({
            'LLT_CODE': ['99999999', '10000001'],
        })
        result = map_soc_codes(df)
        assert pd.isna(result.loc[0, 'SOC'])
        assert result.loc[1, 'SOC'] == 'Blood and lymphatic system disorders'

    def test_map_soc_codes_no_code_column(self):
        """Test mapping when no code column exists."""
        df = pd.DataFrame({
            'NAME': ['Test'],
        })
        result = map_soc_codes(df)
        assert 'SOC' in result.columns
        assert pd.isna(result.loc[0, 'SOC'])

class TestProcessData:
    def test_process_data_creation(self):
        """Test that process_data creates output files and filters correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "raw"
            output_dir = Path(tmpdir) / "processed"
            input_dir.mkdir()
            
            # Create a mock CSV
            mock_data = {
                'CASE_ID': ['1', '2', '3', '4', '5'],
                'VAX_TYPE': ['COVID-19', 'Influenza', 'Hepatitis B', 'COVID-19', 'Unknown'],
                'LLT_CODE': ['10000001', '10000002', '10000003', '10000004', '10000005'],
                'REPT_DATE': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04', '2021-01-05'],
                'AGE': [30, 40, 50, 60, 70]
            }
            df = pd.DataFrame(mock_data)
            csv_path = input_dir / "test.csv"
            df.to_csv(csv_path, index=False)
            
            # Run process
            total, covid, non_covid, non_covid_non_flu = process_data(str(input_dir), str(output_dir))
            
            # Verify outputs exist
            assert (output_dir / "cleaned_vaers.parquet").exists()
            assert (output_dir / "cleaned_vaers.csv").exists()
            
            # Load and verify counts
            result_df = pd.read_parquet(output_dir / "cleaned_vaers.parquet")
            
            # Row 1: COVID-19 -> Group COVID-19
            # Row 2: Influenza -> Group Non-COVID, Sensitivity None (is Flu)
            # Row 3: Hepatitis B -> Group Non-COVID, Sensitivity Non-COVID, Non-Flu
            # Row 4: COVID-19 -> Group COVID-19
            # Row 5: Unknown -> Group Non-COVID (contains "COVID-19"? No. Contains "Influenza"? No.) -> Non-COVID, Non-Flu?
            # Wait, logic: "Non-COVID" is NOT containing "COVID-19".
            # "Non-COVID, Non-Flu" is Non-COVID AND NOT containing "Influenza".
            # "Unknown" does not contain "COVID-19" -> Non-COVID.
            # "Unknown" does not contain "Influenza" -> Non-COVID, Non-Flu.
            
            # Expected:
            # Total: 5 (all have valid dates and mapped SOCs)
            # COVID-19: 2 (Row 1, 4)
            # Non-COVID: 3 (Row 2, 3, 5)
            # Non-COVID, Non-Flu: 2 (Row 3, 5) - Row 2 is Flu
            
            assert total == 5
            assert covid == 2
            assert non_covid == 3
            assert non_covid_non_flu == 2

    def test_process_data_missing_soc_excluded(self):
        """Test that rows with unmapped SOC are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "raw"
            output_dir = Path(tmpdir) / "processed"
            input_dir.mkdir()
            
            # Code 99999999 is not in mapping, so SOC will be NaN
            mock_data = {
                'CASE_ID': ['1', '2'],
                'VAX_TYPE': ['COVID-19', 'Influenza'],
                'LLT_CODE': ['10000001', '99999999'], # Second one maps to NaN
                'REPT_DATE': ['2021-01-01', '2021-01-02'],
                'AGE': [30, 40]
            }
            df = pd.DataFrame(mock_data)
            csv_path = input_dir / "test.csv"
            df.to_csv(csv_path, index=False)
            
            total, _, _, _ = process_data(str(input_dir), str(output_dir))
            
            # Only row 1 should be kept
            assert total == 1

    def test_process_data_missing_date_excluded(self):
        """Test that rows with missing REPT_DATE are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "raw"
            output_dir = Path(tmpdir) / "processed"
            input_dir.mkdir()
            
            mock_data = {
                'CASE_ID': ['1', '2'],
                'VAX_TYPE': ['COVID-19', 'Influenza'],
                'LLT_CODE': ['10000001', '10000002'],
                'REPT_DATE': ['2021-01-01', None], # Second one missing
                'AGE': [30, 40]
            }
            df = pd.DataFrame(mock_data)
            csv_path = input_dir / "test.csv"
            df.to_csv(csv_path, index=False)
            
            total, _, _, _ = process_data(str(input_dir), str(output_dir))
            
            # Only row 1 should be kept
            assert total == 1

class TestMemoryUsage:
    def test_get_memory_usage_gb(self):
        """Test that memory usage function returns a positive float."""
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0
