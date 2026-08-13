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

from src.data.clean import get_memory_usage_gb, map_soc_codes, process_data

class TestMapSOC:
    def test_map_soc_codes_basic(self):
        """Test basic SOC mapping functionality."""
        df = pd.DataFrame({
            'SOC_CODE': ['10021881', '10007541', '10000000'],
            'LLT': ['A', 'B', 'C'],
            'REPT_DATE': ['2021-01-01', '2021-01-02', '2021-01-03']
        })
        result = map_soc_codes(df)
        
        assert 'SOC' in result.columns
        assert result.loc[0, 'SOC'] == 'Infections and infestations'
        assert result.loc[1, 'SOC'] == 'Cardiac disorders'
        assert result.loc[2, 'SOC'] == 'Unknown'  # Code not in mapping

    def test_map_soc_codes_missing_column(self):
        """Test behavior when mapping column is missing."""
        df = pd.DataFrame({
            'OTHER': ['A', 'B'],
            'REPT_DATE': ['2021-01-01', '2021-01-02']
        })
        result = map_soc_codes(df)
        assert 'SOC' in result.columns
        assert all(result['SOC'] == 'Unknown')

class TestProcessData:
    def test_process_data_filtering(self):
        """Test that process_data correctly filters by VAX_TYPE."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_parquet = Path(tmpdir) / "output.parquet"
            output_csv = Path(tmpdir) / "output.csv"
            
            # Create mock data
            data = {
                'VAX_TYPE': ['COVID-19', 'Influenza', 'Non-COVID', 'COVID-19', 'Influenza'],
                'SOC_CODE': ['10021881', '10007541', '10021881', '10007541', '10021881'],
                'LLT': ['A', 'B', 'C', 'D', 'E'],
                'REPT_DATE': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04', '2021-01-05']
            }
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            total, covid, non_covid, non_covid_non_flu = process_data(
                input_path, output_parquet, output_csv
            )
            
            # Verify outputs exist
            assert output_parquet.exists()
            assert output_csv.exists()
            
            # Verify counts
            # COVID-19: 2 rows
            # Non-COVID (Influenza + Non-COVID): 3 rows
            # Non-COVID, Non-Flu: 1 row (the 'Non-COVID' one)
            assert covid == 2
            assert non_covid == 3
            assert non_covid_non_flu == 1

    def test_process_data_missing_rept_date(self):
        """Test that records with missing REPT_DATE are dropped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.csv"
            output_parquet = Path(tmpdir) / "output.parquet"
            output_csv = Path(tmpdir) / "output.csv"
            
            data = {
                'VAX_TYPE': ['COVID-19', 'Influenza', 'Non-COVID'],
                'SOC_CODE': ['10021881', '10007541', '10021881'],
                'LLT': ['A', 'B', 'C'],
                'REPT_DATE': ['2021-01-01', None, '2021-01-03']
            }
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            total, covid, non_covid, non_covid_non_flu = process_data(
                input_path, output_parquet, output_csv
            )
            
            # Only 2 rows should remain (COVID-19 and Non-COVID)
            assert total == 2
            assert covid == 1
            assert non_covid == 1

class TestMemoryUsage:
    def test_get_memory_usage_gb(self):
        """Test that memory usage function returns a non-negative float."""
        mem = get_memory_usage_gb()
        assert isinstance(mem, float)
        assert mem >= 0.0