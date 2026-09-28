import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path
from visualization import find_threshold

class TestFindThreshold:
    def test_find_threshold_basic(self):
        """Test that find_threshold correctly identifies the first resolution < 0.80 power."""
        # Create a temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution,power\n")
            f.write("30m,0.95\n")
            f.write("60m,0.90\n")
            f.write("120m,0.85\n")
            f.write("240m,0.75\n")  # First below 0.80
            f.write("480m,0.60\n")
            temp_path = f.name

        try:
            result = find_threshold(temp_path)
            assert result == "240m", f"Expected '240m', got '{result}'"
            
            # Check that the report file was created
            report_path = Path("data/results/threshold_report.txt")
            assert report_path.exists(), "Threshold report file was not created"
            
            # Check content of report
            with open(report_path, 'r') as r:
                content = r.read()
                assert "Threshold Resolution: 240m" in content
                assert "Power at Threshold: 0.75" in content
        finally:
            os.unlink(temp_path)
            if Path("data/results/threshold_report.txt").exists():
                os.unlink("data/results/threshold_report.txt")

    def test_find_threshold_no_threshold(self):
        """Test behavior when all powers are >= 0.80."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution,power\n")
            f.write("30m,0.95\n")
            f.write("60m,0.90\n")
            f.write("120m,0.85\n")
            temp_path = f.name

        try:
            result = find_threshold(temp_path)
            assert result is None, "Expected None when no threshold found"
        finally:
            os.unlink(temp_path)

    def test_find_threshold_missing_file(self):
        """Test behavior when input file does not exist."""
        result = find_threshold("non_existent_file.csv")
        assert result is None, "Expected None for missing file"

    def test_find_threshold_missing_columns(self):
        """Test behavior when CSV is missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution,other_column\n")
            f.write("30m,0.95\n")
            temp_path = f.name

        try:
            result = find_threshold(temp_path)
            assert result is None, "Expected None for missing columns"
        finally:
            os.unlink(temp_path)

    def test_find_threshold_unsorted_input(self):
        """Test that sorting works correctly even if input is unsorted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("resolution,power\n")
            f.write("480m,0.60\n")
            f.write("30m,0.95\n")
            f.write("240m,0.75\n")  # Should be identified despite being in middle
            f.write("60m,0.90\n")
            temp_path = f.name

        try:
            result = find_threshold(temp_path)
            assert result == "240m", f"Expected '240m', got '{result}'"
        finally:
            os.unlink(temp_path)
            if Path("data/results/threshold_report.txt").exists():
                os.unlink("data/results/threshold_report.txt")