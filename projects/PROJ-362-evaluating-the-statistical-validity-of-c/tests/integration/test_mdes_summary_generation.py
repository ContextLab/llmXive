import os
import csv
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add code to path if not already
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config import RESULTS_DIR
from mdes_summary_generator import load_mdes_results, generate_mdes_summary_csv, run_mdes_summary_generation

class TestMDESSummaryGeneration:
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        # Create a temporary directory structure to simulate RESULTS_DIR
        self.tmp_results = tmp_path / "results"
        self.tmp_results.mkdir()
        self.mdes_dir = self.tmp_results / "mdes"
        self.mdes_dir.mkdir()
        
        # Mock the config.RESULTS_DIR
        with patch('mdes_summary_generator.RESULTS_DIR', str(self.tmp_results)):
            with patch('config.RESULTS_DIR', str(self.tmp_results)):
                yield

    def test_generate_from_raw_json(self, setup):
        """Test generation when raw JSON input exists."""
        raw_data = [
            {"metric": "NDCG@10", "mdes": 0.05, "power": 0.85, "ci_width": 0.01},
            {"metric": "MAP", "mdes": 0.08, "power": 0.82, "ci_width": 0.015}
        ]
        
        raw_path = self.mdes_dir / "mdes_results_raw.json"
        with open(raw_path, 'w') as f:
            json.dump(raw_data, f)
        
        output_path = run_mdes_summary_generation()
        
        assert os.path.exists(output_path)
        assert output_path.endswith("mdes_summary.csv")
        
        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['metric'] == 'NDCG@10'
        assert float(rows[0]['mdes']) == 0.05
        assert float(rows[0]['power']) == 0.85
        assert float(rows[0]['ci_width']) == 0.01

    def test_generate_from_existing_csv(self, setup):
        """Test generation when only the CSV exists (fallback)."""
        csv_path = self.mdes_dir / "mdes_summary.csv"
        existing_data = [
            {"metric": "NDCG@10", "mdes": 0.10, "power": 0.90, "ci_width": 0.005}
        ]
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['metric', 'mdes', 'power', 'ci_width'])
            writer.writeheader()
            for row in existing_data:
                writer.writerow(row)
        
        # No raw JSON, so it should read the CSV
        output_path = run_mdes_summary_generation()
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['metric'] == 'NDCG@10'
        assert float(rows[0]['mdes']) == 0.10

    def test_empty_results_creates_header_only(self, setup):
        """Test that empty results list creates a CSV with headers only."""
        # No files exist, but load_mdes_results raises FileNotFoundError.
        # We need to simulate a scenario where load_mdes_results returns empty list?
        # The current implementation raises FileNotFoundError if neither file exists.
        # Let's create a raw file with empty list.
        raw_path = self.mdes_dir / "mdes_results_raw.json"
        with open(raw_path, 'w') as f:
            json.dump([], f)
        
        output_path = run_mdes_summary_generation()
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert "metric,mdes,power,ci_width" in content
        # Check no data rows
        lines = content.strip().split('\n')
        assert len(lines) == 1

    def test_columns_match_spec(self, setup):
        """Verify the CSV columns match the task specification exactly."""
        raw_data = [
            {"metric": "NDCG@10", "mdes": 0.05, "power": 0.85, "ci_width": 0.01}
        ]
        raw_path = self.mdes_dir / "mdes_results_raw.json"
        with open(raw_path, 'w') as f:
            json.dump(raw_data, f)
        
        output_path = run_mdes_summary_generation()
        
        with open(output_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        
        expected = ['metric', 'mdes', 'power', 'ci_width']
        assert fieldnames == expected
