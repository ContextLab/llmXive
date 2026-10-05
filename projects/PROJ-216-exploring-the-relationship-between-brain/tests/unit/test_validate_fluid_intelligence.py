import pytest
import os
import json
import csv
from pathlib import Path
import sys
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_fluid_intelligence import validate_and_aggregate, ensure_directories

class TestValidateFluidIntelligence:
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_processed = self.test_dir / "data" / "processed"
        self.data_processed.mkdir(parents=True, exist_ok=True)
        
        # Store original paths
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir)
        
        yield
        
        # Cleanup
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_halt_on_zero_valid_scores(self):
        """Test that the script raises ValueError when no valid Fluid Intelligence scores are found."""
        
        # Create download_log.json with subjects
        download_log = {
            "subjects": [
                {"id": "sub_001", "fluid_intelligence_score": None},
                {"id": "sub_002", "fluid_intelligence_score": None}
            ]
        }
        with open(self.data_processed / "download_log.json", 'w') as f:
            json.dump(download_log, f)
        
        # Create graph_metrics.csv with missing/null scores
        metrics_path = self.data_processed / "graph_metrics.csv"
        with open(metrics_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'metric_name', 'value', 'fluid_intelligence_score', 'age', 'gender'])
            writer.writeheader()
            writer.writerow({
                'subject_id': 'sub_001',
                'metric_name': 'efficiency',
                'value': 0.5,
                'fluid_intelligence_score': '',
                'age': 25,
                'gender': 'M'
            })
            writer.writerow({
                'subject_id': 'sub_002',
                'metric_name': 'efficiency',
                'value': 0.6,
                'fluid_intelligence_score': 'NaN',
                'age': 30,
                'gender': 'F'
            })
        
        # Assert that validate_and_aggregate raises ValueError
        with pytest.raises(ValueError) as excinfo:
            validate_and_aggregate()
        
        assert "No valid Fluid Intelligence scores found" in str(excinfo.value)

    def test_passes_with_valid_scores(self):
        """Test that the script returns True when valid scores are present."""
        
        # Create download_log.json
        download_log = {
            "subjects": [
                {"id": "sub_001", "fluid_intelligence_score": 110.0}
            ]
        }
        with open(self.data_processed / "download_log.json", 'w') as f:
            json.dump(download_log, f)
        
        # Create graph_metrics.csv with valid score
        metrics_path = self.data_processed / "graph_metrics.csv"
        with open(metrics_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'metric_name', 'value', 'fluid_intelligence_score', 'age', 'gender'])
            writer.writeheader()
            writer.writerow({
                'subject_id': 'sub_001',
                'metric_name': 'efficiency',
                'value': 0.5,
                'fluid_intelligence_score': 110.0,
                'age': 25,
                'gender': 'M'
            })
        
        # Should not raise and return True
        result = validate_and_aggregate()
        assert result is True

    def test_missing_column_raises_error(self):
        """Test that missing 'fluid_intelligence_score' column raises ValueError."""
        
        # Create download_log.json
        download_log = {"subjects": [{"id": "sub_001"}]}
        with open(self.data_processed / "download_log.json", 'w') as f:
            json.dump(download_log, f)
        
        # Create graph_metrics.csv WITHOUT the fluid_intelligence_score column
        metrics_path = self.data_processed / "graph_metrics.csv"
        with open(metrics_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['subject_id', 'metric_name', 'value', 'age', 'gender'])
            writer.writeheader()
            writer.writerow({
                'subject_id': 'sub_001',
                'metric_name': 'efficiency',
                'value': 0.5,
                'age': 25,
                'gender': 'M'
            })
        
        with pytest.raises(ValueError) as excinfo:
            validate_and_aggregate()
        
        assert "column missing" in str(excinfo.value).lower()
