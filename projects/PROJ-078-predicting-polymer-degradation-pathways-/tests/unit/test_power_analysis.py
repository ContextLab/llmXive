import pytest
import json
import os
import sys
from pathlib import Path
import csv
import tempfile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from power_analysis import check_dataset_power, run_power_analysis_from_csv
from utils import get_project_paths

class TestPowerAnalysis:
    def test_check_dataset_power_threshold(self):
        """Test that n < 150 triggers warning."""
        result = check_dataset_power(100)
        assert result["n"] == 100
        assert result["power_warning"] is True
        assert "Insufficient power" in result["interpretation"]

    def test_check_dataset_power_pass(self):
        """Test that n >= 150 does not trigger warning."""
        result = check_dataset_power(150)
        assert result["n"] == 150
        assert result["power_warning"] is False

        result = check_dataset_power(200)
        assert result["n"] == 200
        assert result["power_warning"] is False

    def test_run_power_analysis_from_csv(self):
        """Test reading CSV and generating report."""
        # Create a temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'label', 'temp'])
            writer.writeheader()
            # Write 149 rows to trigger warning
            for i in range(149):
                writer.writerow({'smiles': f'C{i}', 'label': 'hydrolysis', 'temp': '25'})
            temp_path = f.name

        try:
            result = run_power_analysis_from_csv(temp_path)
            assert result["n"] == 149
            assert result["power_warning"] is True
        finally:
            os.unlink(temp_path)

    def test_run_power_analysis_missing_file(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            run_power_analysis_from_csv("/nonexistent/path/file.csv")
