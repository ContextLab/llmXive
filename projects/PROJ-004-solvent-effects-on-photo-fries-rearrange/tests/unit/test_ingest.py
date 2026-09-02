"""
Unit tests for the real data ingestion module.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.ingest import ingest_real_transient_absorption_data, main
from code.utils.seeds import set_seed

# Set seed for reproducibility
set_seed(42)

class TestIngestRealData:
    """Test cases for real data ingestion functionality."""

    def test_ingest_existing_real_data(self):
        """Test ingestion of existing real data file."""
        # Create a temporary CSV file with valid data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time_ns,delta_absorbance,wavelength_nm\n")
            f.write("0.0,0.05,350\n")
            f.write("1.0,0.04,350\n")
            f.write("2.0,0.03,350\n")
            temp_path = f.name

        try:
            df = ingest_real_transient_absorption_data(
                data_path=temp_path,
                use_real_data=True
            )
            
            assert df is not None
            assert len(df) == 3
            assert 'time_ns' in df.columns
            assert 'delta_absorbance' in df.columns
            assert 'wavelength_nm' in df.columns
            assert df['time_ns'].iloc[0] == 0.0
        finally:
            os.unlink(temp_path)

    def test_missing_file_with_real_data_required(self):
        """Test that FileNotFoundError is raised when file is missing and real data required."""
        with pytest.raises(FileNotFoundError) as excinfo:
            ingest_real_transient_absorption_data(
                data_path="nonexistent_file.csv",
                use_real_data=True
            )
        
        assert "CRITICAL: Real data file missing. Aborting." in str(excinfo.value)

    def test_missing_file_with_real_data_not_required(self):
        """Test that None is returned when file is missing but real data not required."""
        result = ingest_real_transient_absorption_data(
            data_path="nonexistent_file.csv",
            use_real_data=False
        )
        
        assert result is None

    def test_empty_file_raises_error(self):
        """Test that empty file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write empty file
            pass
        temp_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                ingest_real_transient_absorption_data(
                    data_path=temp_path,
                    use_real_data=True
                )
            
            assert "empty" in str(excinfo.value).lower()
        finally:
            os.unlink(temp_path)

    def test_missing_columns_raises_error(self):
        """Test that missing required columns raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time_ns,delta_absorbance\n")  # Missing wavelength_nm
            f.write("0.0,0.05\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                ingest_real_transient_absorption_data(
                    data_path=temp_path,
                    use_real_data=True
                )
            
            assert "Missing required columns" in str(excinfo.value)
        finally:
            os.unlink(temp_path)

    def test_invalid_csv_format_raises_error(self):
        """Test that invalid CSV format raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("not,a,valid,csv\n")
            f.write("with,random,commas\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as excinfo:
                ingest_real_transient_absorption_data(
                    data_path=temp_path,
                    use_real_data=True
                )
            
            assert "parse" in str(excinfo.value).lower() or "csv" in str(excinfo.value).lower()
        finally:
            os.unlink(temp_path)

    def test_cli_entry_point_with_missing_file(self):
        """Test CLI behavior when file is missing and real data required."""
        with patch('sys.argv', ['ingest.py', '--data-path', 'missing.csv', '--use-real-data', 'true']):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(1)

    def test_cli_entry_point_with_existing_file(self):
        """Test CLI behavior with existing file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("time_ns,delta_absorbance,wavelength_nm\n")
            f.write("0.0,0.05,350\n")
            temp_path = f.name

        try:
            with patch('sys.argv', ['ingest.py', '--data-path', temp_path, '--use-real-data', 'true']):
                # This should succeed without raising
                main()
        finally:
            os.unlink(temp_path)